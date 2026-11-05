from __future__ import annotations

from base64 import b64encode
from copy import deepcopy
from dataclasses import asdict, replace
from io import BytesIO
from pathlib import Path
from threading import Event
from types import TracebackType
from typing import Any, Self
from urllib.request import urlopen

import mutagen
from PIL import Image
from mutagen.flac import Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from ytmusicapi import YTMusic

import musicdownloader.config as config
from musicdownloader.songloader import QualityInfo, SongInfo, SongMetaData

# yt-dlp and ytmusicapi expose heterogeneous metadata dictionaries.
type QualityDict = dict[str, str | int | float | None]


class _DownloadCancelled(BaseException):
    """Bypass metadata error handlers when a worker is asked to stop."""


class SongDownloader:
    """Own one yt-dlp session, music client, and album cache per worker.

    Use as a context manager to close the yt-dlp session after all operations.
    Create a separate instance for each concurrent worker.
    """

    def __init__(
        self,
        configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG,
        *,
        cancel_event: Event | None = None,
        quiet: bool = False,
    ) -> None:
        if configuration.max_tries < 1:
            raise ValueError("max_tries must be at least 1")
        self.configuration = configuration
        self.cancel_event = cancel_event
        self.albums: dict[str, dict[str, Any]] = {}
        self.music = YTMusic()
        options = self._youtube_options()
        if quiet:
            options["quiet"] = True
        self.ydl = YoutubeDL(options)

    def __enter__(self) -> Self:
        try:
            self.ydl.__enter__()
        except BaseException:
            self.ydl.close()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.ydl.__exit__(exc_type, exc_value, traceback)

    def check_cancelled(self, _status: dict[str, Any] | None = None) -> None:
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise _DownloadCancelled

    @staticmethod
    def retry_delay(n: int) -> float:
        return float(min(2 ** n, 30))

    def _youtube_options(self) -> dict[str, Any]:
        return {
            "format": "bestaudio",
            "outtmpl": str(
                Path(self.configuration.output_folder)
                / "%(track,title)s%(album& - {}|)s%(artist,creator,uploader& - {}|)s.%(ext)s"
            ),
            "noplaylist": True,
            **self.configuration.cookie_options(),
            "overwrites": True,
            "continuedl": False,
            "remote_components": ["ejs:github"],
            "ignoreerrors": False,
            "js_runtimes": {"node": {}},
            # yt-dlp counts retries after the initial attempt. Let its downloader
            # and extractor classify retryable failures instead of retrying every
            # DownloadError (which also covers unavailable/private videos).
            "retries": self.configuration.max_tries - 1,
            "fragment_retries": self.configuration.max_tries - 1,
            "extractor_retries": self.configuration.max_tries - 1,
            "file_access_retries": 0,
            "skip_unavailable_fragments": False,
            "progress_hooks": [self.check_cancelled],
            "postprocessor_hooks": [self.check_cancelled],
            "retry_sleep_functions": {
                kind: self.retry_delay
                for kind in ("http", "fragment", "extractor")
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "best",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
        }

    def get_available_qualities(self, song: SongInfo | str) -> list[QualityDict]:
        """List audio formats using this session without downloading audio."""
        self.check_cancelled()
        url = song.youtube_url if isinstance(song, SongInfo) else song
        info = self.ydl.extract_info(url, download=False)
        self.check_cancelled()
        return self.qualities_from_info(info)

    def get_highest_quality(self, song: SongInfo | str) -> QualityDict:
        qualities = self.get_available_qualities(song)
        return qualities[-1] if qualities else {}

    def is_better_quality(self, new: QualityDict, old: QualityDict) -> bool:
        return self.compare_qualities(new, old, self.ydl)

    @staticmethod
    def qualities_from_info(info: dict[str, Any] | None) -> list[QualityDict]:
        """Read audio qualities from an already extracted, sorted result."""
        if info is None:
            return []
        return [
            {
                "format_id": fmt.get("format_id"),
                "ext": fmt.get("ext"),
                "codec": fmt.get("acodec"),
                "bitrate_kbps": fmt.get("abr"),
                "sample_rate_hz": fmt.get("asr"),
                "channels": fmt.get("audio_channels"),
            }
            for fmt in info.get("formats", [])
            if fmt.get("vcodec") == "none"
            and fmt.get("acodec") not in (None, "none")
            and fmt.get("has_drm") is not True
        ]

    @staticmethod
    def compare_qualities(new: QualityDict, old: QualityDict, ydl: YoutubeDL) -> bool:
        """Return True only when new ranks higher than old; ties return False.

        Accepts dictionaries returned by get_available_qualities. Uses yt-dlp's
        default ranking of the available codec, channels, bitrate, sample rate,
        and container fields. Source-specific preferences are not in these
        dictionaries and cannot be compared. Does not make network requests or
        modify either input. An empty dictionary loses to a nonempty one.
        """
        if not new:
            return False
        if not old:
            return True

        # Sorting is stable, so placing old last makes ties return False.
        formats = [
            {
                "ext": quality.get("ext"),
                "vcodec": "none",
                "acodec": quality.get("codec"),
                "abr": quality.get("bitrate_kbps"),
                "asr": quality.get("sample_rate_hz"),
                "audio_channels": quality.get("channels"),
                "protocol": "https",
            }
            for quality in (new, old)
        ]
        new_format = formats[0]
        ydl.sort_formats({"formats": formats})
        return formats[-1] is new_format

    def get_metadata(self, info: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        self.check_cancelled()
        metadata = {
            "title": info.get("track") or info.get("title"),
            "artist": info.get("artists") or ([info["artist"]] if info.get("artist") else None),
            "album": info.get("album"),
            "year": info.get("release_year"),
            "track_number": info.get("track_number"),
        }
        thumbnails = [
            {**t, "crop_square": True}
            for t in (info.get("thumbnails") or []) if t.get("url")
        ]
        if not thumbnails and info.get("thumbnail"):
            thumbnails = [{"url": info["thumbnail"], "crop_square": True}]
        try:
            self.check_cancelled()
            watch = self.music.get_watch_playlist(videoId=info["id"], limit=1)
            self.check_cancelled()
            track = next(
                (track for track in watch.get("tracks", [])
                 if track.get("videoId") == info["id"]),
                None,
            )
            if track is None:
                self.ydl.report_warning("No exact YouTube Music match; keeping available download metadata")
                return metadata, thumbnails
            metadata["title"] = track.get("title") or metadata["title"]
            metadata["artist"] = [a["name"] for a in track.get("artists", []) if a.get("name")] or metadata["artist"]
            metadata["year"] = track.get("year") or metadata["year"]
            # Watch results can contain a video's rectangular thumbnail even
            # when returned by YouTube Music. Treat it as fallback artwork;
            # actual album covers below replace it without a crop flag.
            track_thumbnails = track.get("thumbnail") or track.get("thumbnails") or []
            if track_thumbnails:
                thumbnails = [{**t, "crop_square": True} for t in track_thumbnails if t.get("url")] or thumbnails
            album_ref = track.get("album") or {}
            metadata["album"] = album_ref.get("name") or metadata["album"]
            if album_ref.get("id"):
                album_id = album_ref["id"]
                if album_id not in self.albums:
                    self.check_cancelled()
                    self.albums[album_id] = self.music.get_album(album_id)
                album = self.albums[album_id]
                metadata["album"] = album.get("title") or metadata["album"]
                metadata["year"] = album.get("year") or metadata["year"]
                metadata["album_artist"] = [a["name"] for a in album.get("artists", []) if a.get("name")]
                thumbnails = album.get("thumbnails") or thumbnails
                for number, album_track in enumerate(album.get("tracks", []), start=1):
                    if album_track.get("videoId") == info["id"]:
                        metadata["track_number"] = number
                        metadata["track_total"] = album.get("trackCount") or len(album["tracks"])
                        break
            if watch.get("lyrics"):
                self.check_cancelled()
                metadata["lyrics"] = (self.music.get_lyrics(watch["lyrics"]) or {}).get("lyrics")
        except Exception as exc:
            # Unofficial API and network failures must not discard a download.
            self.ydl.report_warning(f"YouTube Music metadata lookup incomplete: {exc}")
        return metadata, thumbnails


    def write_metadata(
        self,
        path: str | Path,
        metadata: dict[str, Any],
        thumbnails: list[dict[str, Any]],
    ) -> None:
        self.check_cancelled()
        audio = mutagen.File(path)
        if not isinstance(audio, (MP4, OggOpus, OggVorbis)):
            raise ValueError(f"Unsupported audio format for tagging: {path}")
        if audio.tags is None:
            audio.add_tags()

        fields = {
            "title": ("\u00a9nam", "title"),
            "artist": ("\u00a9ART", "artist"),
            "album": ("\u00a9alb", "album"),
            "album_artist": ("aART", "albumartist"),
            "year": ("\u00a9day", "date"),
            "comment": ("\u00a9cmt", "comment"),
            "lyrics": ("\u00a9lyr", "lyrics"),
            "bpm": ("tmpo", "bpm"),
        }
        for field, (mp4_key, ogg_key) in fields.items():
            value = metadata.get(field)
            if value is None or value == []:
                continue
            values = value if isinstance(value, list) else [value]
            if isinstance(audio, MP4):
                audio[mp4_key] = [int(v) for v in values] if field == "bpm" else [str(v) for v in values]
            else:
                audio[ogg_key] = [str(v) for v in values]
        if metadata.get("track_number") is not None:
            number = int(metadata["track_number"])
            total = int(metadata.get("track_total") or 0)
            if isinstance(audio, MP4):
                audio["trkn"] = [(number, total)]
            else:
                audio["tracknumber"] = [str(number)]
                if total:
                    audio["tracktotal"] = [str(total)]

        if thumbnails:
            try:
                thumbnail = max(thumbnails, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0))
                with urlopen(thumbnail["url"], timeout=15) as response:
                    cover = response.read()
                self.check_cancelled()
                if thumbnail.get("crop_square"):
                    with Image.open(BytesIO(cover)) as image:
                        side = min(image.size)
                        left = (image.width - side) // 2
                        top = (image.height - side) // 2
                        square = image.crop((left, top, left + side, top + side))
                        buffer = BytesIO()
                        square.save(buffer, format="PNG")
                        cover = buffer.getvalue()
                if cover.startswith(b"\xff\xd8\xff"):
                    mime, image_format = "image/jpeg", MP4Cover.FORMAT_JPEG
                elif cover.startswith(b"\x89PNG\r\n\x1a\n"):
                    mime, image_format = "image/png", MP4Cover.FORMAT_PNG
                else:
                    # YouTube video thumbnails may be WebP; MP4 cover art
                    # requires JPEG or PNG.
                    with Image.open(BytesIO(cover)) as image:
                        buffer = BytesIO()
                        image.save(buffer, format="PNG")
                        cover = buffer.getvalue()
                    mime, image_format = "image/png", MP4Cover.FORMAT_PNG
                if isinstance(audio, MP4):
                    audio["covr"] = [MP4Cover(cover, imageformat=image_format)]
                else:
                    picture = Picture()
                    picture.type = 3
                    picture.mime = mime
                    picture.desc = "Front cover"
                    picture.data = cover
                    audio["metadata_block_picture"] = [b64encode(picture.write()).decode("ascii")]
            except Exception as exc:
                self.ydl.report_warning(f"Could not embed album artwork: {exc}")
        audio.save()

    def _metadata_changed(self, song: SongInfo, previous: SongInfo | None) -> bool:
        return (
            self.configuration.check_metadata_changes
            and previous is not None
            and song.metadata_overrides != previous.metadata_overrides
        )

    def _download_info(
        self,
        song: SongInfo,
        previous: SongInfo | None,
        metadata_changed: bool,
    ) -> dict[str, Any] | None:
        """Decide whether to download, reusing extraction for quality upgrades."""
        if self.configuration.download_all or previous is None or metadata_changed:
            return self.ydl.extract_info(song.youtube_url, download=True)
        if not self.configuration.check_quality_increase:
            return None
        info = self.ydl.extract_info(song.youtube_url, download=False)
        self.check_cancelled()
        qualities = self.qualities_from_info(info)
        if not self.is_better_quality(
            new=qualities[-1] if qualities else {},
            old=asdict(previous.quality) if previous.quality else {},
        ):
            return None
        return self.ydl.process_ie_result(info, download=True)

    @staticmethod
    def _make_record(song: SongInfo, metadata: dict[str, Any], downloaded: dict[str, Any]) -> SongInfo:
        return replace(
            song,
            name=song.name or metadata.get("title") or downloaded.get("title"),
            metadata_overrides=deepcopy(song.metadata_overrides),
            quality=QualityInfo(
                bitrate_kbps=downloaded.get("abr"),
                channels=downloaded.get("audio_channels"),
                codec=downloaded.get("acodec"),
                ext=downloaded.get("ext"),
                format_id=downloaded.get("format_id"),
                sample_rate_hz=downloaded.get("asr"),
            ),
        )

    def _select_record(
        self,
        record: SongInfo,
        previous: SongInfo | None,
        metadata_changed: bool,
    ) -> SongInfo:
        """Preserve the existing history selection behavior after downloads."""
        if previous is None:
            return record
        new_quality = asdict(record.quality) if record.quality else {}
        old_quality = asdict(previous.quality) if previous.quality else {}
        if self.is_better_quality(new=old_quality, old=new_quality):
            print(
                f"\033[31mWARNING: {record.youtube_url} was downloaded at lower quality "
                "than previously recorded; saving the actual downloaded quality.\033[0m"
            )
        elif (
            self.configuration.download_all
            and not metadata_changed
            and not self.is_better_quality(new=new_quality, old=old_quality)
        ):
            return previous
        return record

    def download_song(self, song: SongInfo, previous: SongInfo | None = None) -> SongInfo | None:
        """Return one completed record, or None for a skipped or failed song."""
        self.check_cancelled()
        metadata_changed = self._metadata_changed(song, previous)
        try:
            info = self._download_info(song, previous, metadata_changed)
        except DownloadError as exc:
            print(f"Failed: {song.youtube_url}: {exc}")
            return None
        if info is None:
            return None

        metadata, thumbnails = self.get_metadata(info)
        if song.metadata_overrides is not None:
            metadata.update({
                key: value for key, value in asdict(song.metadata_overrides).items()
                if value is not None
            })
        # Postprocessing changes live in requested_downloads; unchanged fields
        # stay in the main info dictionary.
        downloaded = {
            **info,
            **next(
                (item for item in info.get("requested_downloads", []) if item.get("filepath")),
                {},
            ),
        }
        path = downloaded.get("filepath")
        if not path or not Path(path).is_file():
            self.ydl.report_warning(f"No downloaded audio file found for {song.youtube_url}")
            return None
        try:
            self.write_metadata(path, metadata, thumbnails)
        except (mutagen.MutagenError, OSError, ValueError, KeyError) as exc:
            self.ydl.report_warning(f"Downloaded audio, but could not write music tags: {exc}")
        record = self._make_record(song, metadata, downloaded)
        return self._select_record(record, previous, metadata_changed)

    @staticmethod
    def merge_history(
        downloaded_songs: list[SongInfo],
        already_downloaded_songs: list[SongInfo],
    ) -> list[SongInfo]:
        """Prefer completed records and retain skipped, failed, or unvisited ones."""
        merged = {song.youtube_url: song for song in downloaded_songs}
        for song in already_downloaded_songs:
            merged.setdefault(song.youtube_url, song)
        return list(merged.values())

    def download_songs(
        self,
        songs: list[SongInfo],
        already_downloaded_songs: list[SongInfo] | None = None,
    ) -> list[SongInfo]:
        previous_songs = already_downloaded_songs or []
        completed: list[SongInfo] = []
        try:
            self.check_cancelled()
            for song in songs:
                previous = next((s for s in previous_songs if s == song), None)
                record = self.download_song(song, previous)
                if record is not None:
                    completed.append(record)
        except (KeyboardInterrupt, _DownloadCancelled):
            print("\nDownload interrupted; returning completed and previous downloads.")
        return self.merge_history(completed, previous_songs)


def get_available_qualities(
    youtube_url: SongInfo | str,
    configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG,
) -> list[QualityDict]:
    """Compatibility wrapper; reuse SongDownloader for multiple operations."""
    with SongDownloader(configuration, quiet=True) as downloader:
        return downloader.get_available_qualities(youtube_url)


def _qualities_from_info(info: dict[str, Any] | None) -> list[QualityDict]:
    return SongDownloader.qualities_from_info(info)


def get_highest_quality(
    song: SongInfo | str,
    configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG,
) -> QualityDict:
    with SongDownloader(configuration, quiet=True) as downloader:
        return downloader.get_highest_quality(song)


def is_better_quality(
    new: QualityDict,
    old: QualityDict,
    *,
    ydl: YoutubeDL | None = None,
) -> bool:
    if ydl is not None:
        return SongDownloader.compare_qualities(new, old, ydl)
    # Comparing quality dictionaries does not need browser cookies.
    with SongDownloader(config.DownloadConfig(browser_cookies=None), quiet=True) as downloader:
        return downloader.is_better_quality(new, old)


def download_songs(
    songs: list[SongInfo],
    already_downloaded_songs: list[SongInfo] | None = None,
    configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG,
    *,
    cancel_event: Event | None = None,
) -> list[SongInfo]:
    """Download through one owned session and return completed plus previous records."""
    records: list[SongInfo] = []
    try:
        with SongDownloader(configuration, cancel_event=cancel_event) as downloader:
            records = downloader.download_songs(songs, already_downloaded_songs)
    except (KeyboardInterrupt, _DownloadCancelled):
        print("\nDownload interrupted; returning completed and previous downloads.")
        return SongDownloader.merge_history(records, already_downloaded_songs or [])
    return records


def main() -> None:
    from pprint import pprint
    from musicdownloader.musicloader import write_music_file_json

    x = [
        SongInfo(
            youtube_url = "https://music.youtube.com/watch?v=Oqrswo5KlCU",
            spotify_url="https://open.spotify.com/track/6eIdYm2beEFXDadXRCipHb",
            name="Sukiyo Two hearts",
        ),
        SongInfo(
            youtube_url="https://www.youtube.com/watch?v=g89-7dQMMjY",
            metadata_overrides=SongMetaData(artist="Saki")
        ),
        SongInfo(
            youtube_url="https://music.youtube.com/watch?v=7nVctvQVz0U"
        )
    ]
    with SongDownloader() as downloader:
        pprint(downloader.get_highest_quality(x[-1]))
        records = downloader.download_songs(x)
    write_music_file_json("music/.downloaded_songs.json", records)


if __name__ == "__main__":
    main()
