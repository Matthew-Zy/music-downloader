from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ytmusicapi import YTMusic
from musicdownloader.musicloader import write_music_file_toml, read_music_file_toml

from musicdownloader.songloader import SongInfo 

def get_yt_music_tracks_with_titles(playlist_url):
    """Return public playlist tracks with titles and comma-separated artists."""
    try:
        playlist_ids = parse_qs(urlparse(playlist_url).query).get("list")
        if not playlist_ids:
            raise ValueError("Playlist URL must include a nonempty list parameter")

        playlist = YTMusic().get_playlist(playlist_ids[0], limit=None)
        return [
            {
                "title": track.get("title"),
                "artist": ", ".join(
                    artist["name"]
                    for artist in (track.get("artists") or [])
                    if artist.get("name")
                ),
                "url": f"https://music.youtube.com/watch?v={track['videoId']}",
            }
            for track in playlist.get("tracks", [])
            if track and track.get("videoId")
        ]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def yt_music_tracks_to_toml(playlist_url: str, file_output: str | Path):
    converted = get_yt_music_tracks_with_titles(playlist_url)
    if len(converted) == 0:
        print("failed to convert playlist")
        return 
    recv_songs: list[SongInfo] = []
    for s in converted:
        recv_songs.append(SongInfo(
            youtube_url=s.get("url"),
            name=f'{s.get("artist", "")} - {s.get("title", "")}'
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


if __name__ == "__main__":
    yt_music_playlist = "https://music.youtube.com/playlist?list=PLaOgDfABCiaY"
    tracks = get_yt_music_tracks_with_titles(yt_music_playlist)

    print(f"Extracted {len(tracks)} tracks:\n")
    for track in tracks:
        print(f"Title: {track['title']}")
        print(f"Link:  {track['url']}")
        print(f"Artist(s): {track['artist']}\n")
