from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic
from musicdownloader.musicloader import write_music_file_toml, read_music_file_toml

from musicdownloader.songloader import SongInfo 
from musicdownloader.download_songs import download_songs
from musicdownloader.config import DownloadConfig


def get_yt_music_tracks_information(url: str) -> list[dict[str, any]]:
    """
        Works with single urls AND playlist urls. 
        For a song that has a recommend list query, it will just extract the music file
        Return public playlist tracks with titles and comma-separated artists.
        For the dictionary, it returns, please refer to:
        https://ytmusicapi.readthedocs.io/en/stable/reference/playlists.html
    """
    playlist_ids = parse_qs(urlparse(url).query).get("list")
    song_id = parse_qs(urlparse(url).query).get("v")
    if song_id:
        song = YTMusic().get_watch_playlist(song_id[0], limit=1)
        if song.get("tracks") is None:
            raise ValueError("Could not get track from music url")
        tracks = song.get("tracks")
        tracks = [tracks[0]]
    else:

        playlist = YTMusic().get_playlist(playlist_ids[0], limit=None)

        if playlist.get("tracks") is None:
            raise ValueError("Could not get any tracks from playlist")
        tracks = playlist.get("tracks")

    good_tracks = filter(lambda t: t and t.get("videoId"), tracks)

    def modify(track):
        track["artist"] = ", ".join(
            artist["name"]
            for artist in (track.get("artists") or [])
            if artist.get("name")
        )
        track["album"] = (track.get("album") or {}).get("name")
        track["url"] = f"https://music.youtube.com/watch?v={track['videoId']}"
        return track
    
    good_tracks = map(modify, good_tracks)

    return list(good_tracks)



def yt_music_tracks_to_toml(url: str, file_output: str | Path | None) -> list[SongInfo]:
    """
    If None is passed in, it will print everything to stdout, and return the entire list in the SongInfo dataclass.
    """
    converted = get_yt_music_tracks_information(url)

    recv_songs: list[SongInfo] = []
    for s in converted:
        parts = [s.get("title"), s.get("album"), s.get("artist")]
        recv_songs.append(SongInfo(
            youtube_url=s.get("url"),
            name = " - ".join(part for part in parts if part)
        ))
    if file_output is None:
        write_music_file_toml(None, recv_songs)
    elif file_output:
        try:
            existing = read_music_file_toml(file_output)
        except FileNotFoundError:
            existing = [] 
            pass
        actual_new_songs: list[SongInfo] = []
        for s in recv_songs:
            if s not in existing:
                actual_new_songs.append(s)
        if len(actual_new_songs) <= 0:
            print(f"No new songs were added to existing {file_output} file")
        else:
            write_music_file_toml(file_output, actual_new_songs, mode="a")
            print(f"Sucessfully written to: {file_output}")

    return recv_songs

def download_songs_from_yt_playlist(url: str, output_location: str | Path, cookies: str) -> list[SongInfo]:
    """Cookies for this function will only support cookies from browser."""
    if output_location is None:
        return print("Please provide a valid output location")
    if isinstance(output_location, str):
        output_location = Path(output_location)
    extracted_songs: list[SongInfo] = yt_music_tracks_to_toml(url, None)
    Dconfig = DownloadConfig(
        download_all=True,
        output_folder=output_location, 
        browser_cookies=cookies,
    )
    
    successfully_downloaded_songs = download_songs(extracted_songs, None, Dconfig)

    # uses set differences here
    unsuccessful_downloads = list(set(extracted_songs) - set(successfully_downloaded_songs))

    if len(unsuccessful_downloads) > 0:
        print("Some songs were NOT downloaded:")
        for us in unsuccessful_downloads:
            print(f'name : "{us.name}; url : "{us.youtube_url}";')
    else:
        print(f"Successfully downloaded all songs in playlist: {url}")
    

if __name__ == "__main__":
    yt_music_playlist = "https://music.youtube.com/playlist?list=OLAK5uy_mJe9MXok92wfCA0Yo6NFMyNV2bK__iXdo"
    tracks = get_yt_music_tracks_information(yt_music_playlist)

    print(f"Extracted {len(tracks)} tracks:\n")
    for track in tracks:
        print(f"Title: {track['title']}")
        print(f"Link:  {track['url']}")
        print(f"Album: {track['album']}")
        print(f"Artist(s): {track['artist']}\n")
    yt_music_song = "https://music.youtube.com/watch?v=ulHcNwK1q_U"
    tracks = get_yt_music_tracks_information(yt_music_song)

    for track in tracks:
        print(f"Title: {track['title']}")
        print(f"Link:  {track['url']}")
        print(f"Album: {track['album']}")
        print(f"Artist(s): {track['artist']}\n")