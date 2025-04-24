"""
Pydantic models for request and response schemas
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

# Request models
class SongRequest(BaseModel):
    description: str
    inspirations: List[str]
    title: Optional[str] = None
    tempo: Optional[int] = 120  # Default tempo
    drum_style: Optional[str] = None  # Optional drum style parameter

class ChordProgressionRequest(BaseModel):
    description: str
    inspirations: List[str]
    context: Optional[Dict[str, Any]] = None

class LyricsRequest(BaseModel):
    description: str
    inspirations: List[str]
    chords: Dict[str, List[str]]  # e.g., {"verse": ["C", "G", "Am", "F"], "chorus": ["F", "C", "G", "Am"]}
    context: Optional[Dict[str, Any]] = None

class MelodyRequest(BaseModel):
    description: str
    inspirations: List[str]
    chords: Dict[str, List[str]]
    lyrics: Dict[str, str]  # e.g., {"verse": "lyrics here", "chorus": "chorus lyrics"}
    context: Optional[Dict[str, Any]] = None

class DrumPatternRequest(BaseModel):
    tempo: int
    style: Optional[str] = "basic"
    bars: Optional[int] = 8
    context: Optional[Dict[str, Any]] = None

class GenericRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

# Response models
class Response(BaseModel):
    result: Any
    source: str
    timestamp: str = datetime.now().isoformat()

class SongDetails(BaseModel):
    title: str
    description: Optional[str] = None
    inspirations: Optional[List[str]] = None
    tempo: Optional[int] = None
    chords: Optional[Dict[str, List[str]]] = None
    lyrics: Optional[Dict[str, str]] = None
    melody_summary: Optional[Dict[str, int]] = None
    drum_style: Optional[str] = None  # Added drum style field
    midi_file: Optional[str] = None
    creation_date: Optional[str] = None