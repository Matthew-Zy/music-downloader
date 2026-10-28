from pathlib import Path 
from collections import deque 

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
    


if __name__ == "__main__":
    rm_audio("test")