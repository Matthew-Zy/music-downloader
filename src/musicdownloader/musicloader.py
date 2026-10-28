import tomllib, json
from pathlib import Path
from typing import Literal
from dataclasses import dataclass, asdict
import dacite, tomli_w
from pprint import pprint

from .songloader import SongInfo

@dataclass 
class SongList:
    song: list[SongInfo]
def ignore_none_factory(data):
    return {k: v for k, v in data if v is not None}

def read_music_file_toml(file: Path | str, mode: Literal["f", "s"] = "f") -> list[SongInfo]:
    if mode == "f":
        with open(file, "rb") as f:
            data = tomllib.load(f)
    elif mode == "s":
        data = tomllib.loads(file)
    else:
        raise ValueError(f"Invalid mode received: {mode}")
    songs_list: SongList = dacite.from_dict(data_class=SongList, data=data)
    return songs_list.song

def read_music_files_from_folder(folder: Path | str) -> list[SongInfo]:
    if isinstance(folder, str):
        folder = Path(folder)

    songs: list[SongInfo] = []
    for file in folder.iterdir():
        if file.suffix == ".toml":
            songs.extend(read_music_file_toml(file))
    return songs

def write_music_file_toml(file: Path | str | None, song_contents: list[SongInfo], mode: Literal['w', 'a'] = 'w'):
    """
    Writes songs to a toml file.
    Pass in None to print to the standard output
    'a' appends to a file, while 'w' overwrites it completely
    """
    song_contents = SongList(song=song_contents)
    song_contents = asdict(song_contents, dict_factory=ignore_none_factory)
    toml_string = tomli_w.dumps(song_contents)
    if file is None:
        print(toml_string)
        return 
    file = Path(file) if isinstance(file, str) else file 
    if file.is_dir():
        raise ValueError("Given a folder directory instead of a file")
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    if mode == 'w':
        with open(file, 'wb') as f:
            tomli_w.dump(song_contents, f)
        pass 
    elif mode == 'a':
        with open(file, 'a+') as f:
            f.write("\n" + toml_string)
    else:
        raise ValueError(f"Invalid mode received: {mode}")

def read_music_file_json(file: Path | str) -> list[SongInfo]:
    with open(file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    songs_list: SongList = dacite.from_dict(data_class=SongList, data=data)
    return songs_list.song
    

def write_music_file_json(file: Path | str, song_contents: list[SongInfo]):
    file = Path(file) if isinstance(file, str) else file 
    if file.is_dir():
        raise ValueError("Given a folder directory instead of a file")
    if not file.parent.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
    song_contents = SongList(song=song_contents)
    song_contents = asdict(song_contents, dict_factory=ignore_none_factory) 
    with open(file, "w", encoding="utf-8") as file:
        json.dump(song_contents, file, indent=4)

if __name__ == '__main__':
    x = read_music_file_toml("./music/songs.toml")

    pprint(x)

    write_music_file_toml("test.toml", x)