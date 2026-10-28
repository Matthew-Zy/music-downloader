import yt_dlp
from musicdownloader.musicloader import write_music_file_toml, read_music_file_toml
from musicdownloader.songloader import SongInfo 

def get_yt_music_tracks_with_titles(playlist_url):
    ydl_opts = {
        'extract_flat': True,  # Rapidly grabs metadata without full video parsing
        'skip_download': True,
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(playlist_url, download=False)
            
            if 'entries' in result:
                # Extract both the 'title' and 'id' fields from each entry
                return [
                    {
                        "title": entry.get("title"),
                        "url": f"https://music.youtube.com/watch?v={entry.get('id')}"
                    }
                    for entry in result['entries'] if entry
                ]
            return []
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return []


def yt_music_tracks_to_toml(playlist_url, file_output):
    converted = get_yt_music_tracks_with_titles(playlist_url)
    if len(converted) == 0:
        print("failed to convert playlist")
        return 
    songs: list[SongInfo] = []
    for s in converted:
        songs.append(SongInfo(
            youtube_url=s.get("url"),
            name=s.get("title")
        ))
        # me when infinite iq
        if file_output is None:
            print("[[song]]")
            print(f"youtube_url={s.get("url")}")
            print(f"name={s.get("title")}")
            print("")
    
    if file_output is not None:
        try:
            existing = read_music_file_toml(file_output)
            for s in songs:
                if s in existing:
                    continue 
                else:
                    existing.append(s)
        except FileNotFoundError:
            existing = songs 
            pass
        write_music_file_toml(file_output, existing)
        print(f"Sucessfully written to: {file_output}")

if __name__ == "__main__":
    yt_music_playlist = "https://music.youtube.com/playlist?list=PLaOgDfABCiaY"
    tracks = get_yt_music_tracks_with_titles(yt_music_playlist)

    print(f"Extracted {len(tracks)} tracks:\n")
    for track in tracks:
        print(f"Title: {track['title']}")
        print(f"Link:  {track['url']}\n")
        