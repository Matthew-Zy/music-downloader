from just_playback import Playback, SUPPORTED_AUDIO_FORMATS

from pathlib import Path
from dataclasses import dataclass, field
from collections import deque
from queue import Queue
print(SUPPORTED_AUDIO_FORMATS)

def is_supported_audio(audio_file: Path) -> bool:
    if audio_file.suffix in SUPPORTED_AUDIO_FORMATS:
        return True 

    try:
        tester = Playback()
        tester.load_file(str(audio_file))
        return True
    except Exception:
        return False

@dataclass 
class Playlist:
    folder: Path 
    music_files: list[Path] = field(default_factory=list)
    playlists: list[Playlist] = field(default_factory=list)

    @property 
    def name(self) -> str:
        return self.folder.name 

    def is_empty(self) -> bool:
        return len(self.music_files) == 0 and len(self.playlists) == 0

    def __eq__(self, other: Playlist) -> bool:
        if not isinstance(other, Playlist):
            raise TypeError(f"__eq__ only supports: {__class__.__name__} Objects. Received: {other.__class__.__name__}")

        return self.folder == other.folder and self.music_files == other.music_files
        
    def __contains__(self, other: Playlist) -> bool:
        if not isinstance(other, Playlist):
            raise TypeError(f"__contains__ only supports: {__class__.__name__} Objects. Received: {other.__class__.__name__}")
        if self == other:
            return True
        for p in self.playlists:
            if other in p:
                return True 
        return False 
        

class MDapp:
    available_playlists: list[Playlist] 
    playlist: Playlist | None 
    queue: Queue
    player: Playback


    def __init__(self):
        self.available_playlists = []
        self.playlist = None 
        self.queue = Queue()
        self.player = Playback()
        

    def scan_for_playlists(self, folders: str | list[str]):
        def scan_folder(folder: Path, pl: Playlist):
            cur_folder_pl = Playlist(folder)
            for item in folder.iterdir():
                if item.is_dir(follow_symlinks=True):
                    scan_folder(item, cur_folder_pl)
                elif item.is_file(follow_symlinks=True):
                    if not is_supported_audio(item):
                        continue 
                    cur_folder_pl.music_files.append(item)
            if cur_folder_pl.is_empty():
                return 
            pl.playlists.append(cur_folder_pl)
        
        folders = [folders] if isinstance(folders, str) else folders
        for f in folders:
            f = Path(f)
            p = Playlist(f)
            scan_folder(f, p)
            if p.is_empty():
                return 
            self.available_playlists += p.playlists

    def select_playlist(self, pl: Playlist):
        self.playlist = pl 
        self.queue.put() 


    def play_next(self):
        pass 

    def toggle_pause_play(self):
        if not self.player.active:
            return
        if self.player.paused:
            self.player.resume()
        else:
            self.player.pause()

if __name__ == '__main__':
    from pprint import pprint
    fat = MDapp()

    fat.scan_for_playlists(["playlist", "music"])
    pprint(fat.available_playlists)