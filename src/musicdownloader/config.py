from dataclasses import dataclass 
from typing import Optional 
from pathlib import Path 



DEFAULT_FILE_LOCATION: Path = Path("music/songs.toml")
DEFAULT_OUTPUT_LOCATION: Path = DEFAULT_FILE_LOCATION.parent 
DEFAULT_CACHE: Path = DEFAULT_FILE_LOCATION.parent / "downloaded.toml"
DEFAULT_DOWNLOAD_ALL: bool = False
DEFAULT_MAX_TRIES: int = 5


@dataclass 
class download_config:
    format: str = "mp3"
    output_location: Path = DEFAULT_OUTPUT_LOCATION
    max_tries: int = DEFAULT_MAX_TRIES



