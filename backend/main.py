"""
Music Composition Agentic Backend using AutoGen

This system provides:
1. Music Composition Processing: Generate music based on user parameters
2. Music Theory Knowledge Base: Query chord progressions and style references
3. User Preferences Integration: Track and utilize user composition history
4. Intelligent Agent System: Route requests to specialized musical agents

Uses Azure OpenAI for language model capabilities and AutoGen for the agent framework.
"""

import os
import json
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

class MusicTheoryQuery(BaseModel):
    query: str  # e.g., "common jazz chord progressions"
    style: Optional[str] = None
    key: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class UserPreferencesQuery(BaseModel):
    user_id: str
    query_type: str  # history, favorites, custom_progressions, etc.
    context: Optional[Dict[str, Any]] = None

class CompositionRequest(BaseModel):
    parameters: MusicParameters
    reference_composition_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class GenericRequest(BaseModel):
    query: str
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
    
    def generate_chat_completion(self, messages, max_tokens=1000, temperature=0.7):
        """Generate chat completion using Azure OpenAI"""
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
            logger.error(f"Azure OpenAI API error: {str(e)}")
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
                # Create note on messages for chord notes
                for note_value in chord_item["notes"]:
                    chord_track.append(
                        mido.Message('note_on', note=note_value, velocity=64, time=0)
                    )
                
                # Duration calculation (simplified)
                duration_ticks = int(chord_item["duration"] * ticks_per_beat)
                
                # Create note off messages for chord notes
                for i, note_value in enumerate(chord_item["notes"]):
                    time_value = duration_ticks if i == 0 else 0  # Only first note has the time value
                    chord_track.append(
                        mido.Message('note_off', note=note_value, velocity=64, time=time_value)
                    )
            
            # Process melody (simplified example)
            for note_item in melody:
                # Note on
                melody_track.append(
                    mido.Message('note_on', note=note_item["pitch"], velocity=note_item["velocity"], time=0)
                )
                
                # Duration calculation (simplified)
                duration_ticks = int(note_item["duration"] * ticks_per_beat)
                
                # Note off
                melody_track.append(
                    mido.Message('note_off', note=note_item["pitch"], velocity=0, time=duration_ticks)
                )
            
            # Process drums (simplified example)
            for drum_hit in drums:
                # Note on (drums use channel 9 by convention, 0-indexed)
                drum_track.append(
                    mido.Message('note_on', note=drum_hit["instrument"], velocity=drum_hit["velocity"], 
                                 channel=9, time=0)
                )
                
                # Short duration for drum hits
                drum_track.append(
                    mido.Message('note_off', note=drum_hit["instrument"], velocity=0, 
                                 channel=9, time=int(0.1 * ticks_per_beat))
                )
            
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
                # Create note
                n = note.Note(note_item["pitch"])
                n.quarterLength = note_item["duration"]
                melody_part.append(n)
            
            # Process chord progression
            for chord_item in chord_progression:
                # Create chord
                c = chord.Chord(chord_item["notes"])
                c.quarterLength = chord_item["duration"]
                chord_part.append(c)
            
            # Add parts to score
            score.append(melody_part)
            score.append(chord_part)
            
            # Save to a BytesIO object as MusicXML
            musicxml_file = io.BytesIO()
            score.write('musicxml', fp=musicxml_file)
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

# Mock music library and style references
class MusicLibrary:
    @staticmethod
    def get_chord_progression(style, key):
        """Get common chord progressions for a specific style and key"""
        # Map of common chord progressions by style
        progressions = {
            "jazz": {
                "ii-V-I": "Common jazz progression",
                "i-VI-ii-V": "Minor jazz progression",
                "iii-VI-ii-V": "Extended jazz progression"
            },
            "rock": {
                "I-IV-V": "Classic rock progression",
                "I-V-vi-IV": "Pop rock progression",
                "i-VII-VI-V": "Minor rock progression"
            },
            "pop": {
                "I-V-vi-IV": "Common pop progression",
                "vi-IV-I-V": "Pop progression variant",
                "I-vi-IV-V": "50s progression"
            },
            "classical": {
                "I-IV-V-I": "Classical cadence",
                "I-vi-IV-V": "Classical period progression",
                "i-iv-V-i": "Minor classical progression"
            },
            "blues": {
                "I-IV-I-V-IV-I": "12-bar blues",
                "i-iv-i-v-iv-i": "Minor blues",
                "I-I7-IV-IV7": "Blues with seventh chords"
            }
        }
        
        # Get progressions for the requested style
        style_progressions = progressions.get(style.lower(), progressions["pop"])
        
        # Transform progression notation to the requested key (simplified)
        key_progressions = {}
        for name, description in style_progressions.items():
            key_progressions[name] = {
                "description": description,
                "progression": f"Progression in {key}: {name}"  # Placeholder for actual key transposition
            }
        
        return key_progressions
    
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
            # Add more keys as needed
        }
        
        # Default to C major if key not found
        return scales.get(key, scales["C major"])
    
    @staticmethod
    def get_style_characteristics(style):
        """Get musical characteristics for a specific style"""
        characteristics = {
            "jazz": {
                "harmony": "Extended chords (7th, 9th, 13th), altered dominants",
                "rhythm": "Swing feel, syncopation",
                "typical_instruments": "Piano, bass, drums, saxophone, trumpet",
                "common_forms": "AABA (32-bar), 12-bar blues"
            },
            "rock": {
                "harmony": "Power chords, pentatonic harmony",
                "rhythm": "Strong backbeat, 4/4 time signature",
                "typical_instruments": "Electric guitar, bass, drums, vocals",
                "common_forms": "Verse-chorus form"
            },
            "pop": {
                "harmony": "Diatonic harmony, simple chord progressions",
                "rhythm": "Regular 4/4 beats, catchy patterns",
                "typical_instruments": "Vocals, guitars, keyboards, electronic elements",
                "common_forms": "Verse-chorus-bridge"
            },
            "classical": {
                "harmony": "Functional harmony, cadences",
                "rhythm": "Regular meters, rubato in Romantic period",
                "typical_instruments": "Orchestra, piano, string quartet",
                "common_forms": "Sonata form, theme and variations"
            },
            "blues": {
                "harmony": "Dominant 7th chords, 12-bar form",
                "rhythm": "Shuffle rhythm, swing feel",
                "typical_instruments": "Guitar, harmonica, piano, vocals",
                "common_forms": "12-bar blues, 8-bar blues"
            }
        }
        
        return characteristics.get(style.lower(), characteristics["pop"])
    
    @staticmethod
    def get_melody_patterns(style):
        """Get typical melody patterns for a specific style"""
        patterns = {
            "jazz": [
                "Bebop scale runs",
                "Approach notes and chromatic passing tones",
                "Rhythmic variety with syncopation"
            ],
            "rock": [
                "Pentatonic riffs",
                "Blues-based phrases",
                "Power chord-derived melodies"
            ],
            "pop": [
                "Stepwise diatonic movement",
                "Catchy repeated motifs",
                "Arpeggiated chord tones"
            ],
            "classical": [
                "Motivic development",
                "Question and answer phrases",
                "Scalar passages"
            ],
            "blues": [
                "Blues scale riffs",
                "Bent notes and microtones",
                "Call and response patterns"
            ]
        }
        
        return patterns.get(style.lower(), patterns["pop"])
    
    @staticmethod
    def get_drum_patterns(style):
        """Get typical drum patterns for a specific style"""
        patterns = {
            "jazz": [
                "Ride cymbal pattern with feathered bass drum",
                "Swing pattern with brushes",
                "Bebop comping patterns"
            ],
            "rock": [
                "Backbeat with bass drum on 1 and 3, snare on 2 and 4",
                "Eighth note patterns on hi-hat",
                "Fill patterns around toms"
            ],
            "pop": [
                "Four-on-the-floor kick pattern",
                "Programmed electronic patterns",
                "Layered percussion elements"
            ],
            "classical": [
                "Timpani patterns",
                "Orchestral percussion accents",
                "Dramatic cymbal crashes"
            ],
            "blues": [
                "Shuffle pattern",
                "Half-time feel",
                "Train beat pattern"
            ]
        }
        
        return patterns.get(style.lower(), patterns["pop"])

# Mock user preferences system
class UserPreferencesSystem:
    @staticmethod
    def get_user_history(user_id):
        """Get a user's composition history"""
        # In production: Connect to a database to retrieve real user history
        return {
            "recent_compositions": [
                {"id": "comp1", "title": "Jazz Experiment 1", "style": "jazz", "key": "C minor", "created_at": "2025-04-10"},
                {"id": "comp2", "title": "Rock Ballad", "style": "rock", "key": "G major", "created_at": "2025-03-25"}
            ],
            "favorite_styles": ["jazz", "blues"],
            "preferred_keys": ["C minor", "G major"]
        }
    
    @staticmethod
    def get_user_custom_progressions(user_id):
        """Get a user's saved custom chord progressions"""
        # In production: Connect to a database to retrieve real user data
        return [
            {"name": "My Jazz Thing", "progression": "ii7-V7-Imaj7-VIm7", "key": "C major"},
            {"name": "Blues Variant", "progression": "I7-IV7-I7-V7-IV7-I7", "key": "A minor"}
        ]
    
    @staticmethod
    def get_user_preferences(user_id):
        """Get a user's general music preferences"""
        # In production: Connect to a database to retrieve real user preferences
        return {
            "preferred_tempo_range": [90, 120],
            "preferred_complexity": "medium",  # simple, medium, complex
            "preferred_instruments": ["piano", "guitar", "drums"],
            "preferred_time_signatures": ["4/4", "3/4"]
        }

# Tool functions for AutoGen agents
def generate_chord_progression(style: str, key: str, length: int = 4, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a chord progression based on style and key"""
    try:
        # Get chord progressions from the music library
        progressions = MusicLibrary.get_chord_progression(style, key)
        
        # Get scale notes for the key
        scale = MusicLibrary.get_scale(key)
        
        # Prepare system message
        system_message = "You are a music composition assistant specialized in harmony and chord progressions."
        
        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Generate a {length}-measure chord progression in {key} for {style} style music. Return it in JSON format with the following structure for each chord: {{\"chord_name\": \"Cmaj7\", \"notes\": [60, 64, 67, 71], \"duration\": 1.0}} where notes are MIDI note numbers and duration is in quarter notes."}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Add information about scales and progressions
        messages.append({"role": "user", "content": f"Scale notes for {key}: {', '.join(scale)}. Common progressions for {style}: {json.dumps(progressions)}"})
        
        # Generate chord progression
        chord_progression_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Parse the result (assuming it's in JSON format)
        try:
            chord_progression = json.loads(chord_progression_str)
        except json.JSONDecodeError:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning("LLM didn't return valid JSON for chord progression, using simplified format")
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
            "source": "chord_progression_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_melody(chord_progression: List[Dict], style: str, key: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a melody based on chord progression, style, and key"""
    try:
        # Get scale notes for the key
        scale = MusicLibrary.get_scale(key)
        
        # Get typical melody patterns for the style
        patterns = MusicLibrary.get_melody_patterns(style)
        
        # Prepare system message
        system_message = "You are a music composition assistant specialized in melody creation."
        
        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Generate a melody in {key} for {style} style music that fits over this chord progression: {json.dumps(chord_progression)}. Return it in JSON format with the following structure for each note: {{\"pitch\": 60, \"duration\": 0.5, \"velocity\": 80}} where pitch is MIDI note number, duration is in quarter notes, and velocity is 0-127."}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Add information about scales and melody patterns
        messages.append({"role": "user", "content": f"Scale notes for {key}: {', '.join(scale)}. Typical {style} melody patterns: {json.dumps(patterns)}"})
        
        # Generate melody
        melody_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Parse the result (assuming it's in JSON format)
        try:
            melody = json.loads(melody_str)
        except json.JSONDecodeError:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning("LLM didn't return valid JSON for melody, using simplified format")
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
            "source": "melody_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_drums(style: str, length: int = 4, time_signature: str = "4/4", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate drum patterns based on style and time signature"""
    try:
        # Get typical drum patterns for the style
        patterns = MusicLibrary.get_drum_patterns(style)
        
        # Prepare system message
        system_message = "You are a music composition assistant specialized in drum programming."
        
        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Generate a {length}-measure drum pattern in {time_signature} time for {style} style music. Return it in JSON format with the following structure for each drum hit: {{\"instrument\": 36, \"velocity\": 90, \"position\": 0.0}} where instrument is MIDI note number (36=bass drum, 38=snare, 42=hi-hat closed, 46=hi-hat open, 51=ride), velocity is 0-127, and position is the beat position in the measure (0.0 is the first beat)."}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Add information about drum patterns
        messages.append({"role": "user", "content": f"Typical {style} drum patterns: {json.dumps(patterns)}"})
        
        # Generate drum pattern
        drums_str = ai_client.generate_chat_completion(messages=messages, max_tokens=1000, temperature=0.7)
        
        # Parse the result (assuming it's in JSON format)
        try:
            drums = json.loads(drums_str)
        except json.JSONDecodeError:
            # Fallback in case the LLM doesn't return valid JSON
            logger.warning("LLM didn't return valid JSON for drums, using simplified format")
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
                    "instrument": hit["instrument"],
                    "velocity": hit["velocity"],
                    "position": hit["position"] + (measure * measure_length)
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
        return {
            "error": str(e),
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
        
        # Assemble the composition data
        composition = {
            "title": title,
            "style": style,
            "key": key,
            "tempo": tempo,
            "time_signature": time_signature,
            "chord_progression": chord_progression.get("chord_progression", []),
            "melody": melody.get("melody", []),
            "drums": drums.get("drums", []),
            "creation_date": datetime.now().isoformat()
        }
        
        return {
            "composition": composition,
            "source": "composition_assembler",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in assemble_composition: {str(e)}")
        return {
            "error": str(e),
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
        
        # Create the router agent (LLM-based)
        self.router_agent = AssistantAgent(
            name="RouterAgent",
            system_message="""You are a music composition router. Your job is to determine which specialist to route 
            user queries to based on the content. You have four specialists available:
            1. ChordSpecialist - For generating chord progressions
            2. MelodySpecialist - For creating melodies
            3. DrumSpecialist - For programming drum patterns
            4. CompositionAssembler - For combining all elements into a complete composition
            
            Determine which specialist should handle the query and route it appropriately.
            """,
            llm_config={
                **llm_config,
                "functions": [
                    {
                        "name": "route_to_specialist",
                        "description": "Route the request to the appropriate specialist",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "specialist": {
                                    "type": "string",
                                    "description": "The specialist to route to",
                                    "enum": ["ChordSpecialist", "MelodySpecialist", "DrumSpecialist", "CompositionAssembler"]
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Reason for selecting this specialist"
                                }
                            },
                            "required": ["specialist"]
                        }
                    }
                ]
            }
        )
        
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
        
        # Map specialists to their respective functions for direct execution
        self.specialist_function_map = {
            "ChordSpecialist": self.function_map["generate_chords"]["function"],
            "MelodySpecialist": self.function_map["generate_melody"]["function"],
            "DrumSpecialist": self.function_map["generate_drums"]["function"],
            "CompositionAssembler": self.function_map["assemble_composition"]["function"]
        }
    
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
            chord_result = generate_chord_progression(
                style=style,
                key=key,
                length=length,
                context=context
            )
            
            # Step 2: Generate melody based on the chord progression
            melody_result = generate_melody(
                chord_progression=chord_result["chord_progression"],
                style=style,
                key=key,
                context=context
            )
            
            # Step 3: Generate drum pattern
            drum_result = generate_drums(
                style=style,
                length=length,
                time_signature=time_signature,
                context=context
            )
            
            # Step 4: Assemble the composition
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
            composition_data = composition_result["composition"]
            midi_file = MusicProcessor.create_midi_from_composition(composition_data)
            
            # Step 6: Generate sheet music
            sheet_music_file = MusicProcessor.create_sheet_music(composition_data)
            
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
    
    async def get_music_theory(self, query: str, style: Optional[str] = None, key: Optional[str] = None) -> Response:
        """Query music theory information"""
        try:
            # Prepare context
            context = {}
            if style:
                context["style"] = style
                # Get style characteristics
                context["style_characteristics"] = MusicLibrary.get_style_characteristics(style)
            
            if key:
                context["key"] = key
                # Get scale for the key
                context["scale"] = MusicLibrary.get_scale(key)
                
                if style:
                    # Get chord progressions for the style and key
                    context["chord_progressions"] = MusicLibrary.get_chord_progression(style, key)
            
            # Prepare system message
            system_message = "You are a music theory assistant with expertise in different musical styles, harmony, melody, and rhythm. Provide clear and accurate music theory information."
            
            # Prepare messages for the LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Music theory question: {query}"}
            ]
            
            # Add context if available
            if context:
                context_str = json.dumps(context)
                messages.append({"role": "user", "content": f"Additional context: {context_str}"})
            
            # Generate response
            theory_response = ai_client.generate_chat_completion(messages=messages, max_tokens=1000)
            
            # Create result
            result = {
                "query": query,
                "answer": theory_response,
                "context_used": context
            }
            
            return Response(
                result=result,
                source="music_theory",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error in get_music_theory: {str(e)}")
            return Response(
                result=f"Error querying music theory: {str(e)}",
                source="theory_error",
                timestamp=datetime.now().isoformat()
            )
    
    async def get_user_music_data(self, user_id: str, query_type: str) -> Response:
        """Get user music preferences and history"""
        try:
            result = None
            
            if query_type == "history":
                result = UserPreferencesSystem.get_user_history(user_id)
            elif query_type == "custom_progressions":
                result = UserPreferencesSystem.get_user_custom_progressions(user_id)
            elif query_type == "preferences":
                result = UserPreferencesSystem.get_user_preferences(user_id)
            else:
                # Default to getting all user data
                result = {
                    "history": UserPreferencesSystem.get_user_history(user_id),
                    "custom_progressions": UserPreferencesSystem.get_user_custom_progressions(user_id),
                    "preferences": UserPreferencesSystem.get_user_preferences(user_id)
                }
            
            return Response(
                result=result,
                source="user_music_data",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Error in get_user_music_data: {str(e)}")
            return Response(
                result=f"Error retrieving user music data: {str(e)}",
                source="user_data_error",
                timestamp=datetime.now().isoformat()
            )

# Initialize the music composition system
music_composition_system = MusicCompositionSystem()

# API endpoints
@app.post("/api/compose", response_model=Response)
async def compose_music(request: CompositionRequest):
    """Create a new music composition based on parameters"""
    return await music_composition_system.compose_music(request.parameters)

@app.post("/api/theory", response_model=Response)
async def query_music_theory(request: MusicTheoryQuery):
    """Query music theory and style information"""
    return await music_composition_system.get_music_theory(
        query=request.query,
        style=request.style,
        key=request.key
    )

@app.post("/api/user-data", response_model=Response)
async def get_user_data(request: UserPreferencesQuery):
    """Get user music preferences and history"""
    return await music_composition_system.get_user_music_data(
        user_id=request.user_id,
        query_type=request.query_type
    )

@app.get("/api/composition/{composition_id}/midi")
async def get_midi_file(composition_id: str):
    """Get the MIDI file for a composition"""
    file_path = f"compositions/{composition_id}.mid"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Composition MIDI file not found")
    return FileResponse(file_path, media_type="audio/midi", filename=f"{composition_id}.mid")

@app.get("/api/composition/{composition_id}/sheet")
async def get_sheet_music(composition_id: str):
    """Get the sheet music for a composition"""
    file_path = f"compositions/{composition_id}.musicxml"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Composition sheet music not found")
    return FileResponse(file_path, media_type="application/vnd.recordare.musicxml+xml", filename=f"{composition_id}.musicxml")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)