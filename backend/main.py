"""
Songwriting Agentic Backend using AutoGen

This system provides:
1. Song Structure Processing: Determine chord progressions for verse and chorus
2. Lyrics Generation: Create lyrics based on song description and artist inspirations
3. Melody Creation: Assign notes and durations to lyric syllables
4. MIDI Generation: Convert the musical elements into a MIDI file with instruments

Uses Azure OpenAI for language model capabilities and AutoGen for the agent framework.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.schemas import (
    SongRequest, ChordProgressionRequest, LyricsRequest, 
    MelodyRequest, DrumPatternRequest, Response, SongDetails
)
from agents.agent_system import SongwritingAgentSystem
from agents.chord_agent import generate_chord_progression
from agents.lyrics_agent import generate_lyrics
from agents.melody_agent import generate_melody
from agents.drum_agent import generate_drum_pattern
from services.song_service import SongService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Songwriting Assistant API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the songwriting agent system
songwriting_agent_system = SongwritingAgentSystem()

# API endpoints
@app.post("/api/create-song", response_model=Response)
async def create_song(request: SongRequest):
    """Create a complete song based on description and inspirations"""
    return await songwriting_agent_system.create_song(
        description=request.description,
        inspirations=request.inspirations,
        title=request.title,
        tempo=request.tempo or 120
    )

@app.post("/api/generate-chords", response_model=Response)
async def generate_chords(request: ChordProgressionRequest):
    """Generate chord progressions for verse and chorus"""
    result = generate_chord_progression(
        description=request.description,
        inspirations=request.inspirations,
        context=request.context
    )
    
    return Response(
        result=result,
        source=result.get("source", "chord_generator"),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/generate-lyrics", response_model=Response)
async def generate_lyrics_endpoint(request: LyricsRequest):
    """Generate lyrics for verse and chorus"""
    result = generate_lyrics(
        description=request.description,
        inspirations=request.inspirations,
        chords=request.chords,
        context=request.context
    )
    
    return Response(
        result=result,
        source=result.get("source", "lyrics_generator"),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/generate-melody", response_model=Response)
async def generate_melody_endpoint(request: MelodyRequest):
    """Generate melody based on lyrics and chords"""
    result = generate_melody(
        description=request.description,
        inspirations=request.inspirations,
        chords=request.chords,
        lyrics=request.lyrics,
        context=request.context
    )
    
    return Response(
        result=result,
        source=result.get("source", "melody_generator"),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/generate-drums", response_model=Response)
async def generate_drums_endpoint(request: DrumPatternRequest):
    """Generate drum patterns for the song"""
    result = generate_drum_pattern(
        tempo=request.tempo,
        style=request.style,
        bars=request.bars,
        context=request.context
    )
    
    return Response(
        result=result,
        source=result.get("source", "drum_generator"),
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/download/{song_title}")
async def download_midi(song_title: str):
    """Download the generated MIDI file"""
    try:
        midi_path = SongService.get_midi_path(song_title)
        
        return FileResponse(
            path=midi_path,
            filename=f"{song_title}.mid",
            media_type="audio/midi"
        )
    except Exception as e:
        logger.error(f"Error downloading MIDI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading MIDI: {str(e)}")

# API endpoints for song management
@app.get("/api/songs")
def list_songs():
    """List all generated songs"""
    songs = SongService.list_songs()
    return {"songs": songs}

@app.get("/api/songs/{song_title}", response_model=SongDetails)
def get_song_details(song_title: str):
    """Get details of a specific song"""
    return SongService.get_song_details(song_title)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)