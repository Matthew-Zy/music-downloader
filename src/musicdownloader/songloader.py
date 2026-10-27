from typing import Optional
from dataclasses import dataclass


@dataclass 
class SongMetaData: 
    title: Optional[str] = None 
    artist: str | list[str] | None = None
    album: Optional[str] = None 
    track_number: Optional[int] = None 
    year: Optional[int] = None 
    comment: Optional[str] = None 
    bpm: Optional[int] = None 
    lyrics: Optional[str] = None 

@dataclass 
class QualityInfo:
    bitrate_kbps: Optional[float] = None
    channels: Optional[int] = None 
    codec: Optional[str] = None
    ext: Optional[str] = None 
    format_id: Optional[str] = None
    sample_rate_hz: Optional[int] = None 

@dataclass
class SongInfo:
    youtube_url: str
    spotify_url: Optional[str] = None  
    name: Optional[str] = None 
    metadata_overrides: Optional[SongMetaData] = None 
    quality: Optional[QualityInfo] = None 

    def __eq__(self, other: SongInfo) -> bool:
        return self.youtube_url == other.youtube_url
