from pathlib import Path 
from collections import deque 
from musicdownloader.musicloader import read_music_file_toml

AUDIO_EXTENSIONS = [".opus", ".webm", ".mp3", ".wav", ".aac"]

# Mom can we have DFS?
# We have DFS at home
# DFS at home: 
def dfs_files(folder: Path | str, func_action: callable[any] = print):
    if isinstance(folder, str):
        folder = Path(folder)
    if folder.is_file() or not folder.exists():
        print(f'folder: "{folder}" does not exist')
        return 
     
    queue = deque([folder])
    while queue:
        current_dir = queue.popleft()
        for item in current_dir.iterdir():
            if item.is_dir():
                queue.append(item)
            else:
                func_action(item)
    
    
def rm_audio(folder: Path | str):
    def delete_file_if_audio(file: Path):
        for ae in AUDIO_EXTENSIONS:
            if file.suffix == ae:
                file.unlink(missing_ok=True)
                break 
    dfs_files(folder, delete_file_if_audio)
    

def playlist_lengths(path: Path | str):
    def playlist_len(playlist_file: Path):
        def warn_duplicate(lines: list[str], duplicate_url: str):
            instance = 0
            for i in range(len(lines)):
                if duplicate_url in lines[i]:
                    instance += 1
                    print(f"[{playlist_file.name}]:[{i+1}] Instance {instance} of duplicate url {duplicate_url}")
                pass
        if playlist_file.suffix != ".toml":
            return
        songs = read_music_file_toml(playlist_file)
        with open(playlist_file, "r") as f:
            line_numbers = f.read().split("\n")
        unique, seen = 0, []
        for s in songs:
            if s in seen:
                warn_duplicate(line_numbers, s.youtube_url)
                continue 
            unique += 1
            seen.append(s)
            
        print(f"{playlist_file.name:<12}-{len(songs):>3} Total; {unique:>3} Uniques; {(len(songs)-unique):>3} Duplicates")

    path = Path(path) if isinstance(path, str) else path
    if path.is_file():
        playlist_len(path)
    elif path.is_dir():
        dfs_files(path, playlist_len)

if __name__ == "__main__":
    rm_audio("test")