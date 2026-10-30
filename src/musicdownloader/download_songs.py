from yt_dlp import YoutubeDL 
from pathlib import Path 
from base64 import b64encode
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import asdict, replace
from io import BytesIO
from threading import Event
from urllib.request import urlopen

import mutagen
from PIL import Image
from mutagen.flac import Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from yt_dlp.utils import DownloadError
from ytmusicapi import YTMusic


from musicdownloader.songloader import SongInfo, SongMetaData, QualityInfo
import musicdownloader.config as config


class _DownloadCancelled(BaseException):
    """Bypass metadata error handlers when a worker is asked to stop."""


def get_available_qualities(youtube_url: SongInfo | str, configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG) -> list[dict]:
    """Return available audio-only formats without downloading the song.

    Each entry includes the format ID, container extension, codec, reported
    bitrate in kbps, sample rate in Hz, and channel count. Unknown values are
    None. Uses the configured cookie source and the Node runtime.
    Extraction failures raise yt_dlp.utils.DownloadError.
    """
    if isinstance(youtube_url, SongInfo):
        youtube_url = youtube_url.youtube_url

    yt_opts = {
        "format": "bestaudio",
        "noplaylist": True,
        **configuration.cookie_options(),
        "ignoreerrors": False,
        "js_runtimes": {"node": {}},
        "skip_download": True,
        "quiet": True,
    }

    with YoutubeDL(yt_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    return _qualities_from_info(info)


def _qualities_from_info(info: dict | None) -> list[dict]:
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

def get_highest_quality(song: SongInfo | str, configuration: config.DownloadConfig = config.DEFAULT_DOWNLOAD_CONFIG) -> dict:
    qualities: list[dict] = get_available_qualities(song, configuration=configuration)
    return qualities[-1] if qualities else {}


def is_better_quality(new: dict, old: dict, *, ydl: YoutubeDL | None = None) -> bool:
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
    with (nullcontext(ydl) if ydl is not None else YoutubeDL({"quiet": True})) as sorter:
        sorter.sort_formats({"formats": formats})
    return formats[-1] is new_format
    


def download_songs(
        songs: list[SongInfo],
        already_downloaded_songs: list[SongInfo] = None,
        configuration: config.DownloadConfig=config.DEFAULT_DOWNLOAD_CONFIG,
        *,
        cancel_event: Event | None = None,
) -> list[SongInfo]:
    """Return completed and previous records, including after Ctrl+C.

    Changed overrides trigger a download when check_metadata_changes is enabled.
    Successful downloads record their actual quality, including downgrades.
    Previously downloaded songs are checked for upgrades only when
    check_quality_increase is enabled; download_all always downloads them.
    Retry transient failures up to max_tries per operation.
    """

    if configuration.max_tries < 1:
        raise ValueError("max_tries must be at least 1")

    if already_downloaded_songs is None:
        already_downloaded_songs = []
    downloaded_songs: list[SongInfo] = []

    albums = {}

    def check_cancelled(_status=None):
        if cancel_event is not None and cancel_event.is_set():
            raise _DownloadCancelled

    def get_metadata(info, ydl):
        check_cancelled()
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
            check_cancelled()
            watch = music.get_watch_playlist(videoId=info["id"], limit=1)
            check_cancelled()
            track = next(
                (track for track in watch.get("tracks", [])
                 if track.get("videoId") == info["id"]),
                None,
            )
            if track is None:
                ydl.report_warning("No exact YouTube Music match; keeping available download metadata")
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
                if album_id not in albums:
                    check_cancelled()
                    albums[album_id] = music.get_album(album_id)
                album = albums[album_id]
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
                check_cancelled()
                metadata["lyrics"] = (music.get_lyrics(watch["lyrics"]) or {}).get("lyrics")
        except Exception as exc:
            # Unofficial API and network failures must not discard a download.
            ydl.report_warning(f"YouTube Music metadata lookup incomplete: {exc}")
        return metadata, thumbnails

    def write_metadata(path, metadata, thumbnails, ydl):
        check_cancelled()
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
                check_cancelled()
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
                ydl.report_warning(f"Could not embed album artwork: {exc}")
        audio.save()

    yt_opts = {
        "format": "bestaudio",
        "outtmpl": str(
            Path(configuration.output_folder)
            / "%(track,title)s%(album& - {}|)s%(artist,creator,uploader& - {}|)s.%(ext)s"
        ),
        "noplaylist": True,
        **configuration.cookie_options(),
        "overwrites": True,
        "continuedl": False,
        "remote_components": ["ejs:github"],
        "ignoreerrors": False,
        "js_runtimes": {"node": {}},
        # yt-dlp counts retries after the initial attempt. Let its downloader
        # and extractor classify retryable failures instead of retrying every
        # DownloadError (which also covers unavailable/private videos).
        "retries": configuration.max_tries - 1,
        "fragment_retries": configuration.max_tries - 1,
        "extractor_retries": configuration.max_tries - 1,
        "file_access_retries": 0,
        "skip_unavailable_fragments": False,
        "progress_hooks": [check_cancelled],
        "postprocessor_hooks": [check_cancelled],
        "retry_sleep_functions": {
            kind: lambda n: min(2 ** n, 30)
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

    try:
        check_cancelled()
        music = YTMusic()
        with YoutubeDL(yt_opts) as ydl:
            for song in songs:
                check_cancelled()
                previous = next((s for s in already_downloaded_songs if s == song), None)
                metadata_changed = (
                    configuration.check_metadata_changes
                    and previous is not None
                    and song.metadata_overrides != previous.metadata_overrides
                )
                try:
                    if not configuration.download_all and previous is not None and not metadata_changed:
                        if not configuration.check_quality_increase:
                            continue
                        info = ydl.extract_info(song.youtube_url, download=False)
                        check_cancelled()
                        qualities = _qualities_from_info(info)
                        if not is_better_quality(
                            new=qualities[-1] if qualities else {},
                            old=asdict(previous.quality) if previous.quality else {},
                            ydl=ydl,
                        ):
                            continue
                        # Download the already resolved formats without extracting again.
                        info = ydl.process_ie_result(info, download=True)
                    else:
                        info = ydl.extract_info(song.youtube_url, download=True)
                except DownloadError as exc:
                    print(f"Failed: {song.youtube_url}: {exc}")
                    continue
                if info is None:
                    continue
                metadata, thumbnails = get_metadata(info, ydl)
                if song.metadata_overrides is not None:
                    metadata.update({
                        key: value for key, value in asdict(song.metadata_overrides).items()
                        if value is not None
                    })
                # Per-download data contains changes made by postprocessors, such
                # as WebM becoming Opus; unchanged fields remain in the main info.
                downloaded = {
                    **info,
                    **next(
                        (item for item in info.get("requested_downloads", []) if item.get("filepath")),
                        {},
                    ),
                }
                path = downloaded.get("filepath")
                if not path or not Path(path).is_file():
                    ydl.report_warning(f"No downloaded audio file found for {song.youtube_url}")
                    continue
                try:
                    write_metadata(downloaded["filepath"], metadata, thumbnails, ydl)
                except (mutagen.MutagenError, OSError, ValueError, KeyError) as exc:
                    ydl.report_warning(f"Downloaded audio, but could not write music tags: {exc}")

                record = replace(
                    song,
                    name=song.name or metadata.get("title") or info.get("title"),
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
                if previous is not None:
                    new_quality = asdict(record.quality)
                    old_quality = asdict(previous.quality) if previous.quality else {}
                    if is_better_quality(new=old_quality, old=new_quality, ydl=ydl):
                        print(
                            f"\033[31mWARNING: {song.youtube_url} was downloaded at lower quality "
                            "than previously recorded; saving the actual downloaded quality.\033[0m"
                        )
                    elif configuration.download_all and not metadata_changed and not is_better_quality(
                        new=new_quality, old=old_quality, ydl=ydl,
                    ):
                        record = previous
                downloaded_songs.append(record)

    except (KeyboardInterrupt, _DownloadCancelled):
        print("\nDownload interrupted; returning completed and previous downloads.")

    # Keep selected records first; retain previous records for skipped,
    # failed, interrupted, or unvisited songs regardless of download_all.
    merged = {song.youtube_url: song for song in downloaded_songs}
    for song in already_downloaded_songs:
        merged.setdefault(song.youtube_url, song)
    return list(merged.values())


def main():
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
    # pprint(get_available_qualities(x[0]))
    # pprint(get_available_qualities(x[-1]))
    pprint(get_highest_quality(x[-1]))
    
    write_music_file_json("music/.downloaded_songs.json", download_songs(x))
if __name__ == "__main__":
    main()
