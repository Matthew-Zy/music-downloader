from dataclasses import dataclass 
from typing import Optional 
from pathlib import Path 



DEFAULT_FILE_LOCATION: Path = Path("music/songs.toml")
DEFAULT_OUTPUT_LOCATION: Path = DEFAULT_FILE_LOCATION.parent / "output"
DEFAULT_PREV_STORE_LOCATION: Path = DEFAULT_FILE_LOCATION.parent / ".prev-downloaded.json"
DEFAULT_DOWNLOAD_ALL: bool = False
DEFAULT_MAX_TRIES: int = 5


@dataclass 
class DownloadConfig:
    download_all: bool = DEFAULT_DOWNLOAD_ALL
    output_location: Path = DEFAULT_OUTPUT_LOCATION
    max_tries: int = DEFAULT_MAX_TRIES
    cookies: Optional[str] = None 
    browser_cookies: Optional[str] = None

DEFAULT_DOWNLOAD_CONFIG: DownloadConfig = DownloadConfig()

