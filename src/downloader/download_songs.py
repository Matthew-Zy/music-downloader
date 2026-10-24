from yt_dlp import YoutubeDL 
from spotdl import Spotdl
from spotdl.utils.config import SPOTIFY_OPTIONS
from pathlib import Path 
from musicdownloader.songloader import SongInfo, SongMetaData
import musicdownloader.config as config


def download_song(youtube_url: str, spotify_url: str, dl: Spotdl) -> Path:
    song = dl.search([
        f"{youtube_url}|{spotify_url}"
    ])
    if not song:
        raise RuntimeError(f"Failed to find song: {youtube_url}|{spotify_url}")
    song, path = dl.download(song[0])
    if path is None: 
        raise RuntimeError(f"Download failed for {youtube_url}|{spotify_url}")
    return path

def download_songs(songs: list[SongInfo], output="music/output/", format="mp3"):
    dl = Spotdl(
        client_id=SPOTIFY_OPTIONS["client_id"],
        client_secret=SPOTIFY_OPTIONS["client_secret"],
        downloader_settings={
            "format" : format,
            "output" : output + "{artists} - {title}.{output-ext}",
        },
    )
    for s in songs:
        tries = 0 
        try:
            download_song(s.youtube_url, s.spotify_url, dl)
        except RuntimeError:
            
            pass 
    pass


if __name__ == "__main__":
    x = [
        SongInfo(
            youtube_url = "https://www.youtube.com/watch?v=Oqrswo5KlCU",
            spotify_url="https://open.spotify.com/track/6eIdYm2beEFXDadXRCipHb",
        )
    ]
    download_songs(x)