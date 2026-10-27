from dataclasses import dataclass 
from typing import Optional 
from pathlib import Path 



DEFAULT_FILE_LOCATION: Path = Path("music/songs.toml")
DEFAULT_OUTPUT_FOLDER: Path = DEFAULT_FILE_LOCATION.parent / DEFAULT_FILE_LOCATION.stem
DEFAULT_PREV_STORE_LOCATION: Path = DEFAULT_FILE_LOCATION.parent / f"{DEFAULT_FILE_LOCATION.stem}-downloaded.json"
DEFAULT_DOWNLOAD_ALL: bool = False
DEFAULT_CHECK_QUALITY_INCREASE: bool = True
DEFAULT_MAX_TRIES: int = 5
DEFAULT_COOKIES_BROWSER: str = "firefox"

@dataclass 
class DownloadConfig:
    download_all: bool = DEFAULT_DOWNLOAD_ALL
    output_folder: Path = DEFAULT_OUTPUT_FOLDER
    max_tries: int = DEFAULT_MAX_TRIES
    cookies: Optional[str] = None 
    browser_cookies: Optional[str] = DEFAULT_COOKIES_BROWSER
    check_quality_increase: bool = DEFAULT_CHECK_QUALITY_INCREASE

    def cookie_options(self) -> dict:
        """Translate the selected cookie source into yt-dlp options."""
        if self.cookies and self.browser_cookies:
            raise ValueError("Choose a cookies file or browser cookies, not both")
        if self.cookies:
            return {"cookiefile": self.cookies}
        if self.browser_cookies:
            browser, separator, profile = self.browser_cookies.partition(":")
            if not browser or (separator and not profile):
                raise ValueError("Browser cookies must use BROWSER or BROWSER:PROFILE")
            return {"cookiesfrombrowser": (browser, profile) if separator else (browser,)}
        return {}

DEFAULT_DOWNLOAD_CONFIG: DownloadConfig = DownloadConfig()

