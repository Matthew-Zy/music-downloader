import yt_dlp

url = "https://music.youtube.com/watch?v=Oqrswo5KlCU"

ydl_opts = {
    "format": "bestaudio/best",
    "cookiesfrombrowser": ("firefox",),
    "remote_components": ["ejs:github"],
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])