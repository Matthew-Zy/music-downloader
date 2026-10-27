import yt_dlp

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

# Example Usage:
# Works with both regular playlist links or YouTube Music 'VL' sharing links
def main():
    yt_music_playlist = "https://music.youtube.com/playlist?list=PLaOgDfABCiaY"
    tracks = get_yt_music_tracks_with_titles(yt_music_playlist)

    print(f"Extracted {len(tracks)} tracks:\n")
    for track in tracks:
        print(f"🎵 Title: {track['title']}")
        print(f"🔗 Link:  {track['url']}\n")
