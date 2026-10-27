from dataclasses import dataclass 
from typing import Optional 
from pathlib import Path 



DEFAULT_FILE_LOCATION: Path = Path("music/songs.toml")
DEFAULT_OUTPUT_FOLDER: Path = DEFAULT_FILE_LOCATION.parent / DEFAULT_FILE_LOCATION.stem
DEFAULT_PREV_STORE_LOCATION: Path = DEFAULT_FILE_LOCATION.parent / f"{DEFAULT_FILE_LOCATION.stem}-downloaded.json"
DEFAULT_DOWNLOAD_ALL: bool = False
DEFAULT_MAX_TRIES: int = 5


@dataclass 
class DownloadConfig:
    download_all: bool = DEFAULT_DOWNLOAD_ALL
    output_folder: Path = DEFAULT_OUTPUT_FOLDER
    max_tries: int = DEFAULT_MAX_TRIES
    cookies: Optional[str] = None 
    browser_cookies: Optional[str] = None

DEFAULT_DOWNLOAD_CONFIG: DownloadConfig = DownloadConfig()

