from just_playback import Playback, SUPPORTED_AUDIO_FORMATS

from pathlib import Path
from dataclasses import dataclass, field
from collections import deque
import random 

from . import config

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

    def get_all_songs_list(self, include_sub_playlists: bool = True) -> list[Path]:
        if not include_sub_playlists:
            return self.music_files
        songs = []
        pls = deque([self])
       
        while pls: 
            node = pls.popleft()
            for p in node.playlists:
                pls.append(p)
            songs += node.music_files
        return songs 

    def get_random_song(self, include_sub_playlists: bool = True):
        if not include_sub_playlists:
            rng = random.randint(0, len(self.music_files) - 1)
            return self.music_files[rng]
        
        chosen_songs: Path | None = self.get_all_songs_list(include_sub_playlists=True)
        return chosen_songs[random.randint(0, len(chosen_songs)-1)]

@dataclass 
class MusicNode:
    song: Path 
    prev: MusicNode = None 
    next: MusicNode = None 

    

    

class MDapp:
    available_playlists: list[Playlist] 
    playlist: Playlist | None 
    queue: MusicNode
    player: Playback
    conf: config.MDappConfig



    def __init__(self, conf: config.MDappConfig = config.DEFAULT_MDAPPCONF):
        self.available_playlists = []
        self.playlist = None 
        self.player = Playback()
        
        self.queue = None 
        self.conf = conf
        self.scan_for_playlists(self.conf.playlist_folders)
        self.playlist = self.available_playlists[0]
        

    def scan_for_playlists(self, folders: str | list[str]):
        def scan_folder(folder: Path, pl: Playlist):
            cur_folder_pl = Playlist(folder)
            for item in folder.iterdir():
                if item.is_dir(follow_symlinks=True):
                    scan_folder(item, cur_folder_pl)
                elif item.is_file(follow_symlinks=True):
                    if is_supported_audio(item):
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


    def play_next(self):
        if self.queue and self.queue.next:
            next_node = self.queue.next
        elif self.conf.shuffle:
            next_node = self._get_next_shuffle()
        else:
            next_node = self._get_next_not_shuffle()
        
        if next_node is None:
            return
        self.queue = next_node
        self.player.load_file(self.queue.song)
        self.player.play()
        
    def _get_next_shuffle(self) -> MusicNode | None:
        prevs = self._get_prev_played()
        r = self.playlist.get_random_song(self.conf.play_subplaylists)
        if r is None:
            return None 
        while r in prevs:
            r = self.playlist.get_random_song(self.conf.play_subplaylists)
        if r is None:
            return None 
        else:
            return MusicNode(
                song=r
            )
            
    def _get_next_not_shuffle(self):
        songs = self.playlist.get_all_songs_list(self.conf.play_subplaylists)
        try:
            if not self.queue:
                return MusicNode(song=songs[0])                
        except IndexError:
            return None
        for i in range(len(songs)):
            if songs[i] == self.queue.song:
                return MusicNode(
                    song=songs[(i + 1) % len(songs)]
                )
        return None 
        
        
    def _get_prev_played(self):
        prev_played: list[Path] = []
        cur = self.queue
        while len(prev_played) <= self.conf.songs_before_reshuffle and cur:
            prev_played.append(cur.song)
            cur = cur.prev 
        return prev_played 

    def toggle_pause_play(self):
        if not self.player.active:
            return
        if self.player.paused:
            self.player.resume()
        else:
            self.player.pause()
    
    def pause(self):
        self.player.pause()
    def play(self):
        self.player.play()








def main():
    from pprint import pprint
    fat = MDapp()

    fat.scan_for_playlists(["playlist", "music"])

    pprint(fat.available_playlists)
    pprint(fat.available_playlists[1].get_all_songs_list())