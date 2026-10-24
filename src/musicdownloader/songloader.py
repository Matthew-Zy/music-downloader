from typing import Optional
from dataclasses import dataclass

@dataclass 
class SongMetaData: 
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    track_number: Optional[int]
    year: Optional[int]
    comment: Optional[str]
    bpm: Optional[int]
    lyrics: Optional[str]


@dataclass
class SongInfo:
    youtube_url: str
    spotify_url: Optional[str] = None  
    name: Optional[str] = None 
    metadata_overrides: Optional[SongMetaData] = None 
