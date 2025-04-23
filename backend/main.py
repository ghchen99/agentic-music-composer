import os
import json
import tempfile  # Add this import
from dotenv import load_dotenv
import openai
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import io
import mido
from music21 import stream, note, chord, meter, key, clef, metadata
from music21 import converter as music21_converter
from autogen import AssistantAgent, UserProxyAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Music Composition Assistant API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class MusicParameters(BaseModel):
    style: str  # e.g., "jazz", "classical", "rock", "pop", etc.
    key: str  # e.g., "C major", "A minor", etc.
    tempo: int = 120  # BPM
    length: int = 16  # number of measures
    time_signature: str = "4/4"  # e.g., "3/4", "4/4", etc.
    additional_notes: Optional[str] = None

class CompositionRequest(BaseModel):
    parameters: MusicParameters
    reference_composition_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class Response(BaseModel):
    result: Any
    source: str
    timestamp: str

# Azure OpenAI Client
class AzureOpenAIClient:
    def __init__(self):
        self.model = os.getenv("MODEL_NAME")
        # Using newer SDK approach
        self.client = openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.token_usage = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0
        }
    
    def generate_chat_completion(self, messages, max_tokens=1000, temperature=0.7, retries=2):
        """Generate chat completion using Azure OpenAI with retry logic"""
        for attempt in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Track token usage if available
                if hasattr(response, 'usage'):
                    self.token_usage["total_prompt_tokens"] += response.usage.prompt_tokens
                    self.token_usage["total_completion_tokens"] += response.usage.completion_tokens
                    self.token_usage["total_tokens"] += response.usage.total_tokens
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt < retries:
                    logger.warning(f"Attempt {attempt+1} failed with error: {str(e)}. Retrying...")
                    continue
                logger.error(f"Azure OpenAI API error after {retries+1} attempts: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Azure OpenAI API error: {str(e)}")
    
    def get_token_usage(self):
        """Return the current token usage statistics"""
        return self.token_usage

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

# Music processor for different music formats
class MusicProcessor:
    @staticmethod
    def create_midi_from_composition(composition_data):
        """Create a MIDI file from composition data"""
        try:
            # Extract composition components
            key_sig = composition_data.get("key", "C major")
            tempo = composition_data.get("tempo", 120)
            time_sig = composition_data.get("time_signature", "4/4")
            chord_progression = composition_data.get("chord_progression", [])
            melody = composition_data.get("melody", [])
            drums = composition_data.get("drums", [])
            
            # Validate components
            if not isinstance(chord_progression, list):
                logger.warning("Invalid chord_progression format, using empty list")
                chord_progression = []
            
            if not isinstance(melody, list):
                logger.warning("Invalid melody format, using empty list")
                melody = []
                
            if not isinstance(drums, list):
                logger.warning("Invalid drums format, using empty list")
                drums = []
            
            # Create a new MIDI file
            mid = mido.MidiFile()
            
            # Create tracks for different instruments
            melody_track = mido.MidiTrack()
            chord_track = mido.MidiTrack()
            drum_track = mido.MidiTrack()
            
            # Add tracks to the MIDI file
            mid.tracks.append(melody_track)
            mid.tracks.append(chord_track)
            mid.tracks.append(drum_track)
            
            # Set tempo
            tempo_in_microseconds = mido.bpm2tempo(tempo)
            melody_track.append(mido.MetaMessage('set_tempo', tempo=tempo_in_microseconds))
            
            # Set time signature
            numerator, denominator = map(int, time_sig.split('/'))
            melody_track.append(mido.MetaMessage('time_signature', numerator=numerator, denominator=denominator))
            
            # Process chord progression (simplified example)
            ticks_per_beat = mid.ticks_per_beat
            for chord_item in chord_progression:
                try:
                    # Create note on messages for chord notes
                    notes = chord_item.get("notes", [])
                    if not isinstance(notes, list):
                        logger.warning(f"Invalid notes format in chord: {chord_item}, skipping")
                        continue
                        
                    for note_value in notes:
                        chord_track.append(
                            mido.Message('note_on', note=note_value, velocity=64, time=0)
                        )
                    
                    # Duration calculation (simplified)
                    duration = chord_item.get("duration", 1.0)
                    duration_ticks = int(duration * ticks_per_beat)
                    
                    # Create note off messages for chord notes
                    for i, note_value in enumerate(notes):
                        time_value = duration_ticks if i == 0 else 0  # Only first note has the time value
                        chord_track.append(
                            mido.Message('note_off', note=note_value, velocity=64, time=time_value)
                        )
                except Exception as e:
                    logger.warning(f"Error processing chord {chord_item}: {str(e)}")
                    continue
            
            # Process melody (simplified example)
            for note_item in melody:
                try:
                    # Note on
                    pitch = note_item.get("pitch", 60)
                    velocity = note_item.get("velocity", 64)
                    duration = note_item.get("duration", 1.0)
                    
                    melody_track.append(
                        mido.Message('note_on', note=pitch, velocity=velocity, time=0)
                    )
                    
                    # Duration calculation (simplified)
                    duration_ticks = int(duration * ticks_per_beat)
                    
                    # Note off
                    melody_track.append(
                        mido.Message('note_off', note=pitch, velocity=0, time=duration_ticks)
                    )
                except Exception as e:
                    logger.warning(f"Error processing melody note {note_item}: {str(e)}")
                    continue
            
            # Process drums (simplified example)
            for drum_hit in drums:
                try:
                    # Note on (drums use channel 9 by convention, 0-indexed)
                    instrument = drum_hit.get("instrument", 36)
                    velocity = drum_hit.get("velocity", 64)
                    
                    drum_track.append(
                        mido.Message('note_on', note=instrument, velocity=velocity, 
                                     channel=9, time=0)
                    )
                    
                    # Short duration for drum hits
                    drum_track.append(
                        mido.Message('note_off', note=instrument, velocity=0, 
                                     channel=9, time=int(0.1 * ticks_per_beat))
                    )
                except Exception as e:
                    logger.warning(f"Error processing drum hit {drum_hit}: {str(e)}")
                    continue
            
            # Save to a BytesIO object
            midi_file = io.BytesIO()
            mid.save(file=midi_file)
            midi_file.seek(0)
            
            return midi_file
        except Exception as e:
            logger.error(f"Error creating MIDI: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MIDI creation error: {str(e)}")
    
    @staticmethod
    def create_sheet_music(composition_data):
        """Create sheet music from composition data"""
        try:
            # Extract composition components
            key_sig = composition_data.get("key", "C major")
            tempo = composition_data.get("tempo", 120)
            time_sig = composition_data.get("time_signature", "4/4")
            title = composition_data.get("title", "Composition")
            chord_progression = composition_data.get("chord_progression", [])
            melody = composition_data.get("melody", [])
            
            # Validate components
            if not isinstance(chord_progression, list):
                logger.warning("Invalid chord_progression format, using empty list")
                chord_progression = []
            
            if not isinstance(melody, list):
                logger.warning("Invalid melody format, using empty list")
                melody = []
            
            # Create a new music21 score
            score = stream.Score()
            
            # Add metadata
            score_metadata = metadata.Metadata()
            score_metadata.title = title
            score.metadata = score_metadata
            
            # Create parts for melody and chords
            melody_part = stream.Part()
            chord_part = stream.Part()
            
            # Set clef, key signature, time signature for melody
            melody_part.append(clef.TrebleClef())
            
            # Parse key (simplified)
            key_name = key_sig.split()[0]  # e.g., "C" from "C major"
            mode = "major" if "major" in key_sig.lower() else "minor"
            melody_part.append(key.Key(key_name, mode))
            
            # Parse time signature
            ts_parts = time_sig.split('/')
            melody_part.append(meter.TimeSignature(time_sig))
            
            # Set the same for chord part
            chord_part.append(clef.TrebleClef())
            chord_part.append(key.Key(key_name, mode))
            chord_part.append(meter.TimeSignature(time_sig))
            
            # Process melody notes
            for note_item in melody:
                try:
                    # Create note
                    pitch = note_item.get("pitch", 60)
                    duration = note_item.get("duration", 1.0)
                    
                    n = note.Note(pitch)
                    n.quarterLength = duration
                    melody_part.append(n)
                except Exception as e:
                    logger.warning(f"Error processing melody note {note_item}: {str(e)}")
                    continue
            
            # Process chord progression
            for chord_item in chord_progression:
                try:
                    # Create chord
                    notes = chord_item.get("notes", [60, 64, 67])  # C major by default
                    duration = chord_item.get("duration", 1.0)
                    
                    c = chord.Chord(notes)
                    c.quarterLength = duration
                    chord_part.append(c)
                except Exception as e:
                    logger.warning(f"Error processing chord {chord_item}: {str(e)}")
                    continue
            
            # Add parts to score
            score.append(melody_part)
            score.append(chord_part)
            
            # Save to a BytesIO object as MusicXML - FIXED VERSION
            musicxml_file = io.BytesIO()
            
            # Create a temporary file to write the score
            with tempfile.NamedTemporaryFile(suffix='.musicxml', delete=True) as temp_file:
                filename = temp_file.name
                score.write('musicxml', fp=filename)
                
                # Read the written file and write its contents to our BytesIO
                with open(filename, 'rb') as f:
                    musicxml_file.write(f.read())
                    
            musicxml_file.seek(0)
            
            return musicxml_file
        except Exception as e:
            logger.error(f"Error creating sheet music: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Sheet music creation error: {str(e)}")
        
    @staticmethod
    def parse_midi_file(file_content):
        """Parse a MIDI file and extract musical elements"""
        try:
            midi_file = io.BytesIO(file_content)
            mid = mido.MidiFile(file=midi_file)
            
            # Extract MIDI data
            tracks = []
            for i, track in enumerate(mid.tracks):
                notes = []
                current_time = 0
                open_notes = {}  # Dictionary to track open notes
                
                for msg in track:
                    current_time += msg.time
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Note started
                        open_notes[msg.note] = {
                            'start_time': current_time,
                            'velocity': msg.velocity
                        }
                    elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                        # Note ended
                        if msg.note in open_notes:
                            start_data = open_notes[msg.note]
                            duration = current_time - start_data['start_time']
                            notes.append({
                                'pitch': msg.note,
                                'start_time': start_data['start_time'],
                                'duration': duration,
                                'velocity': start_data['velocity']
                            })
                            del open_notes[msg.note]
                
                tracks.append({
                    'track_number': i,
                    'name': track.name if hasattr(track, 'name') else f"Track {i}",
                    'notes': notes
                })
            
            # Extract tempo information (from the first tempo message found)
            tempo = 120  # Default
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'set_tempo':
                        tempo = mido.tempo2bpm(msg.tempo)
                        break
                if tempo != 120:
                    break
            
            # Extract time signature (from the first time_signature message found)
            time_sig = "4/4"  # Default
            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'time_signature':
                        time_sig = f"{msg.numerator}/{msg.denominator}"
                        break
                if time_sig != "4/4":
                    break
            
            return {
                "tracks": tracks,
                "tempo": tempo,
                "time_signature": time_sig,
                "ticks_per_beat": mid.ticks_per_beat
            }
        except Exception as e:
            logger.error(f"Error parsing MIDI file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MIDI parsing error: {str(e)}")

# Basic music reference data for agents
class MusicReference:
    @staticmethod
    def get_scale(key):
        """Get the notes of a scale for a specific key"""
        # Basic mapping of keys to scales (simplified)
        scales = {
            "C major": ["C", "D", "E", "F", "G", "A", "B"],
            "C minor": ["C", "D", "Eb", "F", "G", "Ab", "Bb"],
            "G major": ["G", "A", "B", "C", "D", "E", "F#"],
            "E minor": ["E", "F#", "G", "A", "B", "C", "D"],
            "F major": ["F", "G", "A", "Bb", "C", "D", "E"],
            "D minor": ["D", "E", "F", "G", "A", "Bb", "C"],
            # Add more key signatures as needed
            "A minor": ["A", "B", "C", "D", "E", "F", "G"],
            "D major": ["D", "E", "F#", "G", "A", "B", "C#"],
            "Bb major": ["Bb", "C", "D", "Eb", "F", "G", "A"],
            "G minor": ["G", "A", "Bb", "C", "D", "Eb", "F"],
        }
        
        # Default to C major if key not found
        if key not in scales:
            logger.warning(f"Scale for key '{key}' not found, defaulting to C major")
        return scales.get(key, scales["C major"])

# Improved tool functions for AutoGen agents
def generate_chord_progression(style: str, key: str, length: int = 4, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a chord progression based on style and key"""
    try:
        # Get scale notes for the key
        scale = MusicReference.get_scale(key)
        
        # Prepare system message
        system_message = "You are a music composition assistant specialized in harmony and chord progressions."
        
        # Prepare messages for the LLM with improved JSON instructions
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"""
Generate a {length}-measure chord progression in {key} for {style} style music.

IMPORTANT: You must return ONLY a valid JSON array that I can parse directly with json.loads().
Format each chord as:
{{"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0}}

Your response must begin with '[' and end with ']' with no other text before or after.
Example of a valid response format:
[
  {{"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0}},
  {{"chord_name": "Dm7", "notes": [62, 65, 69, 72], "duration": 1.0}},
  {{"chord_name": "G7", "notes": [67, 71, 74, 77], "duration": 1.0}},
  {{"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0}}
]

Do not include any explanation, just the JSON array.
"""}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Add information about scales
        messages.append({"role": "user", "content": f"Scale notes for {key}: {', '.join(scale)}."})
        
        # Generate chord progression
        chord_progression_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Clean the result to ensure it's valid JSON
        chord_progression_str = chord_progression_str.strip()
        
        # If there's text before the opening bracket, remove it
        if '[' in chord_progression_str and not chord_progression_str.startswith('['):
            chord_progression_str = chord_progression_str[chord_progression_str.find('['):]
            
        # If there's text after the closing bracket, remove it
        if ']' in chord_progression_str and not chord_progression_str.endswith(']'):
            chord_progression_str = chord_progression_str[:chord_progression_str.rfind(']')+1]
        
        # Parse the result
        try:
            chord_progression = json.loads(chord_progression_str)
            if not isinstance(chord_progression, list):
                raise json.JSONDecodeError("Not a list", chord_progression_str, 0)
        except json.JSONDecodeError as e:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning(f"LLM didn't return valid JSON for chord progression: {str(e)}, using simplified format")
            # Create a simple example chord progression
            chord_progression = [
                {"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0},
                {"chord_name": "Dm7", "notes": [62, 65, 69, 72], "duration": 1.0},
                {"chord_name": "G7", "notes": [67, 71, 74, 77], "duration": 1.0},
                {"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0}
            ]
        
        return {
            "chord_progression": chord_progression,
            "key": key,
            "style": style,
            "source": "chord_progression_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_chord_progression: {str(e)}")
        return {
            "error": str(e),
            "chord_progression": [
                {"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0},
                {"chord_name": "Dm7", "notes": [62, 65, 69, 72], "duration": 1.0},
                {"chord_name": "G7", "notes": [67, 71, 74, 77], "duration": 1.0},
                {"chord_name": "Cmaj7", "notes": [60, 64, 67, 71], "duration": 1.0}
            ],
            "source": "chord_progression_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_melody(chord_progression: List[Dict], style: str, key: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a melody based on chord progression, style, and key"""
    try:
        # Get scale notes for the key
        scale = MusicReference.get_scale(key)
        
        # Prepare system message
        system_message = "You are a music composition assistant specialized in melody creation."
        
        # Prepare messages for the LLM with improved JSON instructions
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"""
Generate a melody in {key} for {style} style music that fits over this chord progression: {json.dumps(chord_progression)}

IMPORTANT: You must return ONLY a valid JSON array that I can parse directly with json.loads().
Format each note as:
{{"pitch": 60, "duration": 0.5, "velocity": 80}}

Your response must begin with '[' and end with ']' with no other text before or after.
Example of a valid response format:
[
  {{"pitch": 60, "duration": 0.5, "velocity": 80}},
  {{"pitch": 62, "duration": 0.5, "velocity": 80}},
  {{"pitch": 64, "duration": 0.5, "velocity": 80}},
  {{"pitch": 65, "duration": 0.5, "velocity": 80}},
  {{"pitch": 67, "duration": 1.0, "velocity": 90}}
]

Do not include any explanation, just the JSON array.
"""}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Add information about scales
        messages.append({"role": "user", "content": f"Scale notes for {key}: {', '.join(scale)}."})
        
        # Generate melody
        melody_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Clean the result to ensure it's valid JSON
        melody_str = melody_str.strip()
        
        # If there's text before the opening bracket, remove it
        if '[' in melody_str and not melody_str.startswith('['):
            melody_str = melody_str[melody_str.find('['):]
            
        # If there's text after the closing bracket, remove it
        if ']' in melody_str and not melody_str.endswith(']'):
            melody_str = melody_str[:melody_str.rfind(']')+1]
        
        # Parse the result
        try:
            melody = json.loads(melody_str)
            if not isinstance(melody, list):
                raise json.JSONDecodeError("Not a list", melody_str, 0)
        except json.JSONDecodeError as e:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning(f"LLM didn't return valid JSON for melody: {str(e)}, using simplified format")
            # Create a simple example melody
            melody = [
                {"pitch": 60, "duration": 0.5, "velocity": 80},
                {"pitch": 62, "duration": 0.5, "velocity": 80},
                {"pitch": 64, "duration": 0.5, "velocity": 80},
                {"pitch": 65, "duration": 0.5, "velocity": 80},
                {"pitch": 67, "duration": 1.0, "velocity": 90},
                {"pitch": 65, "duration": 0.5, "velocity": 80},
                {"pitch": 64, "duration": 0.5, "velocity": 80},
                {"pitch": 62, "duration": 0.5, "velocity": 80},
                {"pitch": 60, "duration": 1.0, "velocity": 90}
            ]
        
        return {
            "melody": melody,
            "key": key,
            "style": style,
            "source": "melody_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_melody: {str(e)}")
        return {
            "error": str(e),
            "melody": [
                {"pitch": 60, "duration": 0.5, "velocity": 80},
                {"pitch": 62, "duration": 0.5, "velocity": 80},
                {"pitch": 64, "duration": 0.5, "velocity": 80},
                {"pitch": 65, "duration": 0.5, "velocity": 80},
                {"pitch": 67, "duration": 1.0, "velocity": 90},
                {"pitch": 65, "duration": 0.5, "velocity": 80},
                {"pitch": 64, "duration": 0.5, "velocity": 80},
                {"pitch": 62, "duration": 0.5, "velocity": 80},
                {"pitch": 60, "duration": 1.0, "velocity": 90}
            ],
            "source": "melody_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_drums(style: str, length: int = 4, time_signature: str = "4/4", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate drum patterns based on style and time signature"""
    try:
        # Prepare system message
        system_message = "You are a music composition assistant specialized in drum programming."
        
        # Prepare messages for the LLM with improved JSON instructions
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"""
Generate a {length}-measure drum pattern in {time_signature} time for {style} style music.

IMPORTANT: You must return ONLY a valid JSON array that I can parse directly with json.loads().
Format each drum hit as:
{{"instrument": 36, "velocity": 90, "position": 0.0}}

Where:
- instrument is MIDI note number (36=bass drum, 38=snare, 42=hi-hat closed, 46=hi-hat open, 51=ride)
- velocity is 0-127
- position is the beat position in the measure (0.0 is the first beat)

Your response must begin with '[' and end with ']' with no other text before or after.
Example of a valid response format:
[
  {{"instrument": 36, "velocity": 90, "position": 0.0}},
  {{"instrument": 38, "velocity": 90, "position": 1.0}},
  {{"instrument": 42, "velocity": 70, "position": 0.0}},
  {{"instrument": 42, "velocity": 70, "position": 0.5}}
]

Do not include any explanation, just the JSON array.
"""}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Generate drum pattern
        drums_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Clean the result to ensure it's valid JSON
        drums_str = drums_str.strip()
        
        # If there's text before the opening bracket, remove it
        if '[' in drums_str and not drums_str.startswith('['):
            drums_str = drums_str[drums_str.find('['):]
            
        # If there's text after the closing bracket, remove it
        if ']' in drums_str and not drums_str.endswith(']'):
            drums_str = drums_str[:drums_str.rfind(']')+1]
        
        # Parse the result
        try:
            drums = json.loads(drums_str)
            if not isinstance(drums, list):
                raise json.JSONDecodeError("Not a list", drums_str, 0)
        except json.JSONDecodeError as e:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning(f"LLM didn't return valid JSON for drums: {str(e)}, using simplified format")
            # Create a simple example drum pattern
            if time_signature == "4/4":
                drums = [
                    {"instrument": 36, "velocity": 90, "position": 0.0},  # Bass drum on beat 1
                    {"instrument": 38, "velocity": 90, "position": 1.0},  # Snare on beat 2
                    {"instrument": 36, "velocity": 90, "position": 2.0},  # Bass drum on beat 3
                    {"instrument": 38, "velocity": 90, "position": 3.0},  # Snare on beat 4
                    {"instrument": 42, "velocity": 70, "position": 0.0},  # Hi-hat on each eighth note
                    {"instrument": 42, "velocity": 70, "position": 0.5},
                    {"instrument": 42, "velocity": 70, "position": 1.0},
                    {"instrument": 42, "velocity": 70, "position": 1.5},
                    {"instrument": 42, "velocity": 70, "position": 2.0},
                    {"instrument": 42, "velocity": 70, "position": 2.5},
                    {"instrument": 42, "velocity": 70, "position": 3.0},
                    {"instrument": 42, "velocity": 70, "position": 3.5}
                ]
            else:
                # Simple 3/4 pattern
                drums = [
                    {"instrument": 36, "velocity": 90, "position": 0.0},  # Bass drum on beat 1
                    {"instrument": 38, "velocity": 90, "position": 1.0},  # Snare on beat 2
                    {"instrument": 38, "velocity": 90, "position": 2.0},  # Snare on beat 3
                    {"instrument": 42, "velocity": 70, "position": 0.0},  # Hi-hat on each beat
                    {"instrument": 42, "velocity": 70, "position": 1.0},
                    {"instrument": 42, "velocity": 70, "position": 2.0}
                ]
        
        # Transform to the expected format for the composition
        drum_hits = []
        for hit in drums:
            # Convert position to time-based format
            measure_length = 4.0  # In quarter notes for 4/4
            if time_signature == "3/4":
                measure_length = 3.0
            
            # Create multiple measures
            for measure in range(length):
                drum_hits.append({
                    "instrument": hit.get("instrument", 36),
                    "velocity": hit.get("velocity", 80),
                    "position": hit.get("position", 0.0) + (measure * measure_length)
                })
        
        return {
            "drums": drum_hits,
            "style": style,
            "time_signature": time_signature,
            "source": "drum_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_drums: {str(e)}")
        # Create a simple fallback drum pattern
        if time_signature == "4/4":
            drum_hits = [
                {"instrument": 36, "velocity": 90, "position": 0.0},  # Bass drum on beat 1
                {"instrument": 38, "velocity": 90, "position": 1.0},  # Snare on beat 2
                {"instrument": 36, "velocity": 90, "position": 2.0},  # Bass drum on beat 3
                {"instrument": 38, "velocity": 90, "position": 3.0},  # Snare on beat 4
            ]
            # Repeat for all measures
            for measure in range(1, length):
                for hit in drum_hits[:]:
                    drum_hits.append({
                        "instrument": hit["instrument"],
                        "velocity": hit["velocity"],
                        "position": hit["position"] + (measure * 4.0)
                    })
        else:
            # Simple 3/4 pattern
            drum_hits = [
                {"instrument": 36, "velocity": 90, "position": 0.0},  # Bass drum on beat 1
                {"instrument": 38, "velocity": 90, "position": 1.0},  # Snare on beat 2
                {"instrument": 38, "velocity": 90, "position": 2.0},  # Snare on beat 3
            ]
            # Repeat for all measures
            for measure in range(1, length):
                for hit in drum_hits[:]:
                    drum_hits.append({
                        "instrument": hit["instrument"],
                        "velocity": hit["velocity"],
                        "position": hit["position"] + (measure * 3.0)
                    })
            
        return {
            "error": str(e),
            "drums": drum_hits,
            "source": "drum_error",
            "timestamp": datetime.now().isoformat()
        }

def assemble_composition(
    chord_progression: Dict[str, Any],
    melody: Dict[str, Any],
    drums: Dict[str, Any],
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Assemble all musical components into a complete composition"""
    try:
        # Extract parameters
        style = parameters.get("style", "pop")
        key = parameters.get("key", "C major")
        tempo = parameters.get("tempo", 120)
        time_signature = parameters.get("time_signature", "4/4")
        title = parameters.get("title", f"{style.capitalize()} Composition in {key}")
        
        # Extract components with fallbacks
        chords = chord_progression.get("chord_progression", [])
        if not isinstance(chords, list):
            logger.warning("Invalid chord_progression, using empty list")
            chords = []
            
        melody_notes = melody.get("melody", [])
        if not isinstance(melody_notes, list):
            logger.warning("Invalid melody, using empty list")
            melody_notes = []
            
        drum_hits = drums.get("drums", [])
        if not isinstance(drum_hits, list):
            logger.warning("Invalid drums, using empty list")
            drum_hits = []
        
        # Assemble the composition data
        composition = {
            "title": title,
            "style": style,
            "key": key,
            "tempo": tempo,
            "time_signature": time_signature,
            "chord_progression": chords,
            "melody": melody_notes,
            "drums": drum_hits,
            "creation_date": datetime.now().isoformat()
        }
        
        return {
            "composition": composition,
            "source": "composition_assembler",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in assemble_composition: {str(e)}")
        # Return a basic composition with empty components
        composition = {
            "title": f"Composition in C major",
            "style": "pop",
            "key": "C major",
            "tempo": 120,
            "time_signature": "4/4",
            "chord_progression": [],
            "melody": [],
            "drums": [],
            "creation_date": datetime.now().isoformat()
        }
        return {
            "error": str(e),
            "composition": composition,
            "source": "composition_error",
            "timestamp": datetime.now().isoformat()
        }

# Define AutoGen tool functions with proper format
def register_autogen_functions():
    """Register functions as tools for AutoGen agents"""
    function_map = {
        "generate_chords": {
            "name": "generate_chords",
            "description": "Generate chord progressions based on style and key",
            "parameters": {
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "Musical style (e.g., jazz, rock, pop, classical)"
                    },
                    "key": {
                        "type": "string",
                        "description": "Musical key (e.g., C major, A minor)"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Number of measures in the progression",
                        "default": 4
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for the chord progression"
                    }
                },
                "required": ["style", "key"]
            },
            "function": generate_chord_progression
        },
        "generate_melody": {
            "name": "generate_melody",
            "description": "Generate a melody that fits over a chord progression",
            "parameters": {
                "type": "object",
                "properties": {
                    "chord_progression": {
                        "type": "array",
                        "description": "The chord progression to fit the melody to"
                    },
                    "style": {
                        "type": "string",
                        "description": "Musical style (e.g., jazz, rock, pop, classical)"
                    },
                    "key": {
                        "type": "string",
                        "description": "Musical key (e.g., C major, A minor)"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for the melody"
                    }
                },
                "required": ["chord_progression", "style", "key"]
            },
            "function": generate_melody
        },
        "generate_drums": {
            "name": "generate_drums",
            "description": "Generate drum patterns based on style and time signature",
            "parameters": {
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "Musical style (e.g., jazz, rock, pop, classical)"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Number of measures in the pattern",
                        "default": 4
                    },
                    "time_signature": {
                        "type": "string",
                        "description": "Time signature (e.g., 4/4, 3/4, 6/8)",
                        "default": "4/4"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for the drum pattern"
                    }
                },
                "required": ["style"]
            },
            "function": generate_drums
        },
        "assemble_composition": {
            "name": "assemble_composition",
            "description": "Assemble all musical components into a complete composition",
            "parameters": {
                "type": "object",
                "properties": {
                    "chord_progression": {
                        "type": "object",
                        "description": "The chord progression data"
                    },
                    "melody": {
                        "type": "object",
                        "description": "The melody data"
                    },
                    "drums": {
                        "type": "object",
                        "description": "The drum pattern data"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional composition parameters"
                    }
                },
                "required": ["chord_progression", "melody", "drums", "parameters"]
            },
            "function": assemble_composition
        }
    }
    
    return function_map

# AutoGen Agent System
class MusicCompositionSystem:
    def __init__(self):
        """Initialize the AutoGen-based music composition system"""
        # Configure AutoGen for Azure OpenAI
        llm_config = {
            "config_list": [
                {
                    "model": os.getenv("MODEL_NAME"),
                    "api_type": "azure",
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "api_version": os.getenv("API_VERSION"),
                }
            ],
            "temperature": 0.7
        }
        
        # Register tool functions
        self.function_map = register_autogen_functions()
        
        # Create specialist agents with their tools
        self.chord_specialist = AssistantAgent(
            name="ChordSpecialist",
            system_message="You are a music harmony specialist. You can generate chord progressions based on style, key, and other parameters.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_chords"]
                ]
            }
        )
        
        self.melody_specialist = AssistantAgent(
            name="MelodySpecialist",
            system_message="You are a melody creation specialist. You can generate melodies that fit over chord progressions for various styles and keys.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_melody"]
                ]
            }
        )
        
        self.drum_specialist = AssistantAgent(
            name="DrumSpecialist",
            system_message="You are a rhythm and percussion specialist. You can generate drum patterns for various styles and time signatures.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_drums"]
                ]
            }
        )
        
        self.composition_assembler = AssistantAgent(
            name="CompositionAssembler",
            system_message="You are a music composition assembler. You can combine chord progressions, melodies, and drum patterns into complete musical compositions.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["assemble_composition"]
                ]
            }
        )
        
        # Create a human proxy agent to act as the interface
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",  # No actual human input needed
            code_execution_config=False  # Disable code execution
        )
    
    async def compose_music(self, parameters: MusicParameters) -> Response:
        """Create a full music composition based on the provided parameters"""
        try:
            # Extract parameters
            style = parameters.style
            key = parameters.key
            tempo = parameters.tempo
            length = parameters.length
            time_signature = parameters.time_signature
            additional_notes = parameters.additional_notes
            
            # Context for the specialists
            context = {}
            if additional_notes:
                context["additional_notes"] = additional_notes
            
            # Step 1: Generate chord progression
            logger.info(f"Generating chord progression for {style} in {key}")
            chord_result = generate_chord_progression(
                style=style,
                key=key,
                length=length,
                context=context
            )
            
            # Step 2: Generate melody based on the chord progression
            logger.info(f"Generating melody for {style} in {key}")
            melody_result = generate_melody(
                chord_progression=chord_result["chord_progression"],
                style=style,
                key=key,
                context=context
            )
            
            # Step 3: Generate drum pattern
            logger.info(f"Generating drum pattern for {style} in {time_signature}")
            drum_result = generate_drums(
                style=style,
                length=length,
                time_signature=time_signature,
                context=context
            )
            
            # Step 4: Assemble the composition
            logger.info("Assembling composition")
            composition_params = {
                "style": style,
                "key": key,
                "tempo": tempo,
                "time_signature": time_signature,
                "title": f"{style.capitalize()} Composition in {key}"
            }
            
            composition_result = assemble_composition(
                chord_progression=chord_result,
                melody=melody_result,
                drums=drum_result,
                parameters=composition_params
            )
            
            # Step 5: Generate MIDI file from the composition
            logger.info("Creating MIDI file")
            composition_data = composition_result["composition"]
            midi_file = MusicProcessor.create_midi_from_composition(composition_data)
            
            # Step 6: Generate sheet music
            logger.info("Creating sheet music")
            sheet_music_file = MusicProcessor.create_sheet_music(composition_data)
            
            # Ensure both files were created successfully
            if not midi_file or not sheet_music_file:
                raise ValueError("Failed to create MIDI or sheet music file")
                
            # Save files to disk with unique IDs
            composition_id = f"comp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            midi_path = f"compositions/{composition_id}.mid"
            sheet_music_path = f"compositions/{composition_id}.musicxml"
            
            # Ensure directory exists
            os.makedirs("compositions", exist_ok=True)
            
            # Write files
            with open(midi_path, "wb") as f:
                f.write(midi_file.getvalue())
            
            with open(sheet_music_path, "wb") as f:
                f.write(sheet_music_file.getvalue())
            
            logger.info(f"Composition created successfully with ID: {composition_id}")
            
            # Create response
            result = {
                "composition_id": composition_id,
                "title": composition_data["title"],
                "style": style,
                "key": key,
                "tempo": tempo,
                "time_signature": time_signature,
                "length": length,
                "midi_file": midi_path,
                "sheet_music_file": sheet_music_path,
                "composition_data": composition_data
            }
            
            return Response(
                result=result,
                source="music_composition_system",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error in compose_music: {str(e)}")
            return Response(
                result=f"Error composing music: {str(e)}",
                source="composition_error",
                timestamp=datetime.now().isoformat()
            )

# Initialize the music composition system
music_composition_system = MusicCompositionSystem()

# API endpoints
@app.post("/api/compose", response_model=Response)
async def compose_music(request: CompositionRequest):
    """Create a new music composition based on parameters"""
    try:
        logger.info(f"Received composition request for {request.parameters.style} in {request.parameters.key}")
        return await music_composition_system.compose_music(request.parameters)
    except Exception as e:
        logger.error(f"Error in compose_music endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error composing music: {str(e)}")

@app.get("/api/composition/{composition_id}/midi")
async def get_midi_file(composition_id: str):
    """Get the MIDI file for a composition"""
    file_path = f"compositions/{composition_id}.mid"
    if not os.path.exists(file_path):
        logger.error(f"Composition MIDI file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Composition MIDI file not found")
    return FileResponse(file_path, media_type="audio/midi", filename=f"{composition_id}.mid")

@app.get("/api/composition/{composition_id}/sheet")
async def get_sheet_music(composition_id: str):
    """Get the sheet music for a composition"""
    file_path = f"compositions/{composition_id}.musicxml"
    if not os.path.exists(file_path):
        logger.error(f"Composition sheet music file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Composition sheet music not found")
    return FileResponse(file_path, media_type="application/vnd.recordare.musicxml+xml", filename=f"{composition_id}.musicxml")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Simple test endpoint to verify fixes
@app.get("/test")
async def test_endpoint():
    """Test the main components of the system without creating a full composition"""
    try:
        # Test chord progression generation
        chord_result = generate_chord_progression(
            style="jazz",
            key="C major",
            length=4
        )
        
        # Test melody generation
        melody_result = generate_melody(
            chord_progression=chord_result["chord_progression"],
            style="jazz",
            key="C major"
        )
        
        # Test MIDI creation (small test)
        test_composition = {
            "title": "Test Composition",
            "key": "C major",
            "tempo": 120,
            "time_signature": "4/4",
            "chord_progression": chord_result["chord_progression"][:2],
            "melody": melody_result["melody"][:4],
            "drums": []
        }
        
        midi_file = MusicProcessor.create_midi_from_composition(test_composition)
        sheet_music_file = MusicProcessor.create_sheet_music(test_composition)
        
        # Both should be BytesIO objects
        return {
            "status": "success",
            "chord_progression_length": len(chord_result["chord_progression"]),
            "melody_length": len(melody_result["melody"]),
            "midi_created": midi_file is not None,
            "sheet_music_created": sheet_music_file is not None
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)