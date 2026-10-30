# Music Downloader
A tool to download music from youtube music from .toml source files. Also remembers previous downloads and will only redownload songs if a higher quality version is available or unless prompted to. Would recommend getting the 1 month free trial of youtube music premium then downloading as much higher quality audio files during this trial before it ends.

Please use this tool at your own risk. Please refer to your country's laws on `stream-ripping`. It maybe illegal on paper, but is generally a gray zone. Again, please use at your own risk. The author of this software is not responsible for any legal responsibilities for those using this software. 

## Setup and Usage:
Clone and Install all dependencies with `uv`
```bash
git clone https://github.com/Matthew-Zy/music-downloader.git music-downloader && cd music-downloader
uv sync
```
Music Downloader Usage (Use `-h`/`--help` for help):
```bash
uv run musicdownloader [flags]
```
Example usages:
```bash
# Download all songs in .toml in the music folder without checking if there are better quality versions for existing songs and use cookies from firefox
# If you're premium account is signed in on chrome, please specify which profile. Exampe: --cookies-from-browser "chrome:Profile 1"
uv run musicdownloader -l ./music/ --no-check-quality-increase --cookies-from-browser firefox
# Download ALL songs even if they have been previously downloaded before from the music/songs.toml and output at ./output/ folder
uv run musicdownloader -o ./output/ --all
```

## Utility tool usage
The `mdutil` utility usage contains helpful commands to help you utilize musicdownloader
```bash
uv run mdutil -h
```
Example usages:
```bash
# Turn in a youtube music playlist url (must be a public playlist) to a toml file that can be used my musicdownloader. 
# if the given output file exists, it will append songs that are not in the existing file, and preserve any existing toml comments. 
uv run mdutil -ep [PLAYLIST_LINK] -o my_playlist.toml
# check the length of all playlist toml files in a folder, and check if there are any duplicate entries
uv run mdutil -ls [FOLDER_NAME]
# you may do multiple operations at once such as:
#  Check length and if there are any duplicates of a toml playlist, purge all audio files in a folder, and extract a playlist into a toml playlist
uv run mdutil -ls [FILE_NAME] -rm [FOLDER_NAME] -ep [PLAYLIST_LINK] -o my_playlist.toml
```

# Toml entries format
A quick note about the behavior of `musicdownloader`, is that when a folder is passed in as the source location, it will recursively download all valid `.toml` playlists down the folder. It will download songs from each `.toml` file in the same folder the `.toml` file is, and write the download records in the same folder as a `.json` file. The output location can be specified with `-o [OUTPUT_FOLDER]`.  
If a file is chosen for the source location, it will created a folder with the same name of the file and output the audio files there.

Example entries given below. The only required field is `youtube_url`, every other field is optional. The name field is purely cosmetic and there for readability purposes. 
```toml
[[song]]
name = "Iris"
youtube_url = "https://music.youtube.com/watch?v=Dy_eP-mqWow"

# metadata_overrides are great if a song cover isn't officially on youtube music, where the automatic metadata fetching may not be able to find some information
# For example, this amazing cover of Sign original by Aya Uchida in English
# Refer to src/musicdownloader/songloader.py for which metadata options you can add. These override any of those automatically fetched
[[song]]
name = "Sign - TQQ ending - English Cover"
youtube_url = "https://www.youtube.com/watch?v=g89-7dQMMjY"
[song.metadata_overrides]
title = "[Gotoubun no Hanayome ED 1] Sign (English Cover)"
artist = ["Chiisana", "Lunarveil", "Spiral", "Shiena", "Saki"] # Can also be a string for a single artist
bpm = 102 
album = "Ephemera"
track_number = 9
year = 2022
comment = "This cover is goated..."
lyrics = """Insert your
very long lyrics here
"""
```