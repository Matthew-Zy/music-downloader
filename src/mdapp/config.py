from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass 
class MDappConfig:
    playlist_folders: list[Path]
    shuffle: bool 
    songs_before_reshuffle: int
    play_subplaylists: bool
    last_played: None | Path


DEFAULT_MDAPPCONF = MDappConfig(
    playlist_folders = [],
    shuffle=False,
    songs_before_reshuffle=10,
    play_subplaylists=True,
    last_played=None, 
)


print(json.dumps(asdict(DEFAULT_MDAPPCONF)))


