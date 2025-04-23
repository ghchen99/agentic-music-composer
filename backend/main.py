"""
Songwriting Agentic Backend using AutoGen

This system provides:
1. Song Structure Processing: Determine chord progressions for verse and chorus
2. Lyrics Generation: Create lyrics based on song description and artist inspirations
3. Melody Creation: Assign notes and durations to lyric syllables
4. MIDI Generation: Convert the musical elements into a MIDI file with instruments

Uses Azure OpenAI for language model capabilities and AutoGen for the agent framework.
"""

import os
import json
from dotenv import load_dotenv
import openai
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import music21
import mido
from mido import Message, MidiFile, MidiTrack
import tempfile
import os.path
from autogen import AssistantAgent, UserProxyAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

# Data models
class SongRequest(BaseModel):
    description: str
    inspirations: List[str]
    title: Optional[str] = None
    tempo: Optional[int] = 120  # Default tempo

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
    
    def generate_chat_completion(self, messages, max_tokens=1000, temperature=0.7):  # Higher temperature for creativity
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

# Music21 and MIDI Processor for converting musical elements to MIDI
class MusicProcessor:
    @staticmethod
    def parse_chord(chord_name):
        """Parse a chord name into a music21 chord object"""
        try:
            return music21.harmony.ChordSymbol(chord_name)
        except Exception as e:
            logger.error(f"Error parsing chord {chord_name}: {str(e)}")
            # Fallback to a simple C major chord
            return music21.chord.Chord(['C4', 'E4', 'G4'])
    
    @staticmethod
    def parse_melody_note(note_info):
        """Parse a note info dict into a music21 note object"""
        try:
            # Expected format: {'pitch': 'C4', 'duration': 1.0, 'syllable': 'ly'}
            pitch = note_info.get('pitch', 'C4')
            duration = note_info.get('duration', 1.0)
            
            note = music21.note.Note(pitch)
            note.duration = music21.duration.Duration(duration)
            return note
        except Exception as e:
            logger.error(f"Error parsing note {note_info}: {str(e)}")
            # Fallback to a quarter note C
            return music21.note.Note('C4', type='quarter')
    
    @staticmethod
    def generate_midi_file(chords, melody, title="Song", tempo=120):
        """Generate a MIDI file with piano, drums, and strings"""
        try:
            # Create a MIDI file with three tracks: piano (chords), melody, and drums
            mid = MidiFile(type=1)
            
            # Track 0: Tempo and time signature
            track0 = MidiTrack()
            mid.tracks.append(track0)
            
            # Add tempo
            tempo_microseconds = mido.bpm2tempo(tempo)
            track0.append(mido.MetaMessage('set_tempo', tempo=tempo_microseconds, time=0))
            
            # Add time signature (4/4)
            track0.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
            
            # Track 1: Piano (chords)
            piano_track = MidiTrack()
            mid.tracks.append(piano_track)
            piano_track.append(mido.MetaMessage('track_name', name='Piano', time=0))
            piano_track.append(Message('program_change', program=0, time=0))  # Piano
            
            # Add chords
            time = 0
            for section, chord_list in chords.items():
                for chord_name in chord_list:
                    # Convert chord to music21 object
                    chord = MusicProcessor.parse_chord(chord_name)
                    
                    # Add each note in the chord
                    for note in chord.pitches:
                        # Convert to MIDI note number
                        midi_note = note.midi
                        piano_track.append(Message('note_on', note=midi_note, velocity=64, time=time))
                        time = 0  # Reset time for subsequent notes in chord
                    
                    # Set time for note_off
                    time = 480  # Quarter note (assuming 480 ticks per quarter note)
                    
                    # Add note_off messages
                    for note in chord.pitches:
                        midi_note = note.midi
                        piano_track.append(Message('note_off', note=midi_note, velocity=64, time=time))
                        time = 0  # Reset time for subsequent notes
            
            # Track 2: Melody
            melody_track = MidiTrack()
            mid.tracks.append(melody_track)
            melody_track.append(mido.MetaMessage('track_name', name='Melody', time=0))
            melody_track.append(Message('program_change', program=73, time=0))  # Flute
            
            # Add melody notes
            time = 0
            for section, notes in melody.items():
                for note_info in notes:
                    # Convert to music21 note
                    m21_note = MusicProcessor.parse_melody_note(note_info)
                    
                    # Convert to MIDI note number
                    midi_note = m21_note.pitch.midi
                    
                    # Calculate duration in ticks (assuming 480 ticks per quarter note)
                    duration_ticks = int(480 * m21_note.duration.quarterLength)
                    
                    # Add note_on
                    melody_track.append(Message('note_on', note=midi_note, velocity=80, time=time))
                    time = 0
                    
                    # Add note_off
                    melody_track.append(Message('note_off', note=midi_note, velocity=0, time=duration_ticks))
                    time = 0
            
            # Track 3: Strings (pad)
            strings_track = MidiTrack()
            mid.tracks.append(strings_track)
            strings_track.append(mido.MetaMessage('track_name', name='Strings', time=0))
            strings_track.append(Message('program_change', program=48, time=0))  # String Ensemble
            
            # Add basic string pad following the chord progression
            time = 0
            for section, chord_list in chords.items():
                for chord_name in chord_list:
                    # Convert chord to music21 object
                    chord = MusicProcessor.parse_chord(chord_name)
                    
                    # Add only root and fifth for a pad sound
                    notes_to_play = [chord.root().midi, chord.getChordStep(5).midi]
                    
                    # Add note_on messages
                    for midi_note in notes_to_play:
                        strings_track.append(Message('note_on', note=midi_note, velocity=50, time=time))
                        time = 0
                    
                    # Set time for note_off
                    time = 960  # Half note
                    
                    # Add note_off messages
                    for midi_note in notes_to_play:
                        strings_track.append(Message('note_off', note=midi_note, velocity=0, time=time))
                        time = 0
            
            # Track 4: Drums
            drum_track = MidiTrack()
            mid.tracks.append(drum_track)
            drum_track.append(mido.MetaMessage('track_name', name='Drums', time=0))
            drum_track.append(Message('program_change', program=0, channel=9, time=0))  # Drums channel
            
            # Add a basic drum pattern (kick on 1 and 3, snare on 2 and 4, hi-hat on every 8th note)
            kick_drum = 36
            snare_drum = 38
            closed_hihat = 42
            
            # Pattern for two measures (8 beats in 4/4 time)
            for _ in range(2 * (len(chords.get('verse', [])) + len(chords.get('chorus', [])))):  # Repeat for each chord
                # Beat 1: Kick + Hi-hat
                drum_track.append(Message('note_on', note=kick_drum, velocity=100, channel=9, time=0))
                drum_track.append(Message('note_on', note=closed_hihat, velocity=80, channel=9, time=0))
                drum_track.append(Message('note_off', note=kick_drum, velocity=0, channel=9, time=10))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=110))
                
                # 8th note: Hi-hat
                drum_track.append(Message('note_on', note=closed_hihat, velocity=60, channel=9, time=0))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=120))
                
                # Beat 2: Snare + Hi-hat
                drum_track.append(Message('note_on', note=snare_drum, velocity=90, channel=9, time=0))
                drum_track.append(Message('note_on', note=closed_hihat, velocity=80, channel=9, time=0))
                drum_track.append(Message('note_off', note=snare_drum, velocity=0, channel=9, time=10))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=110))
                
                # 8th note: Hi-hat
                drum_track.append(Message('note_on', note=closed_hihat, velocity=60, channel=9, time=0))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=120))
                
                # Beat 3: Kick + Hi-hat
                drum_track.append(Message('note_on', note=kick_drum, velocity=100, channel=9, time=0))
                drum_track.append(Message('note_on', note=closed_hihat, velocity=80, channel=9, time=0))
                drum_track.append(Message('note_off', note=kick_drum, velocity=0, channel=9, time=10))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=110))
                
                # 8th note: Hi-hat
                drum_track.append(Message('note_on', note=closed_hihat, velocity=60, channel=9, time=0))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=120))
                
                # Beat 4: Snare + Hi-hat
                drum_track.append(Message('note_on', note=snare_drum, velocity=90, channel=9, time=0))
                drum_track.append(Message('note_on', note=closed_hihat, velocity=80, channel=9, time=0))
                drum_track.append(Message('note_off', note=snare_drum, velocity=0, channel=9, time=10))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=110))
                
                # 8th note: Hi-hat
                drum_track.append(Message('note_on', note=closed_hihat, velocity=60, channel=9, time=0))
                drum_track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=120))
            
            # Create a song directory structure
            # Base songs directory
            songs_dir = os.path.join(os.getcwd(), "songs")
            if not os.path.exists(songs_dir):
                os.makedirs(songs_dir)
            
            # Clean the title to create a valid folder name
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            if not safe_title:
                safe_title = "song"
                
            # Create a subfolder for this song
            song_dir = os.path.join(songs_dir, safe_title.replace(' ', '_'))
            if not os.path.exists(song_dir):
                os.makedirs(song_dir)
            
            # Save the MIDI file in the song's directory
            midi_path = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
            
            # Save the MIDI file
            mid.save(midi_path)
            
            # Also save a song info JSON file with metadata
            song_info = {
                "title": title,
                "tempo": tempo,
                "creation_date": datetime.now().isoformat(),
                "chords": chords,
                "melody_info": {
                    "verse_notes": len(melody.get("verse", [])),
                    "chorus_notes": len(melody.get("chorus", []))
                }
            }
            
            with open(os.path.join(song_dir, "song_info.json"), "w") as f:
                json.dump(song_info, f, indent=2)
            
            return midi_path
        
        except Exception as e:
            logger.error(f"Error generating MIDI file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MIDI generation error: {str(e)}")

# Tool functions for AutoGen agents
def generate_chord_progression(description: str, inspirations: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate chord progressions for verse and chorus"""
    try:
        # Prepare system message for chord progression generation
        system_message = """You are a music theory expert specializing in songwriting. 
        You'll create chord progressions for a verse and chorus based on a song description and musical inspirations.
        Focus on creating ONE 4-chord progression for the verse and ONE 4-chord progression for the chorus in 4/4 time.
        Use standard chord notation (e.g., C, G, Am, F).
        Your response should be in JSON format with 'verse' and 'chorus' keys, each with an array of 4 chords."""
        
        # Prepare messages for the LLM
        inspirations_str = ", ".join(inspirations)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Create chord progressions for a song with this description: {description}\n\nMusical inspirations: {inspirations_str}"}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Generate chord progression
        chord_progression_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.7  # Higher temperature for creative variations
        )
        
        # Extract JSON from the response (handling potential text before/after the JSON)
        import re
        json_match = re.search(r'({.*?})', chord_progression_response.replace('\n', ''), re.DOTALL)
        
        if json_match:
            chord_progression_json = json_match.group(1)
            chord_progression = json.loads(chord_progression_json)
        else:
            # Fallback to parsing manually if JSON format is not perfect
            logger.warning("Couldn't parse JSON directly, attempting manual extraction")
            
            verse_match = re.search(r'verse"?\s*:\s*\[(.*?)\]', chord_progression_response, re.DOTALL)
            chorus_match = re.search(r'chorus"?\s*:\s*\[(.*?)\]', chord_progression_response, re.DOTALL)
            
            verse_chords = []
            chorus_chords = []
            
            if verse_match:
                verse_str = verse_match.group(1).strip()
                verse_chords = [chord.strip().strip('"\'') for chord in verse_str.split(',')]
            
            if chorus_match:
                chorus_str = chorus_match.group(1).strip()
                chorus_chords = [chord.strip().strip('"\'') for chord in chorus_str.split(',')]
            
            chord_progression = {
                "verse": verse_chords if verse_chords else ["C", "G", "Am", "F"],  # Fallback
                "chorus": chorus_chords if chorus_chords else ["F", "C", "G", "Am"]  # Fallback
            }
        
        # Ensure there are exactly 4 chords in each section
        if len(chord_progression.get("verse", [])) != 4:
            chord_progression["verse"] = chord_progression.get("verse", [])[:4]
            # Pad if needed
            while len(chord_progression["verse"]) < 4:
                chord_progression["verse"].append("C")
        
        if len(chord_progression.get("chorus", [])) != 4:
            chord_progression["chorus"] = chord_progression.get("chorus", [])[:4]
            # Pad if needed
            while len(chord_progression["chorus"]) < 4:
                chord_progression["chorus"].append("F")
        
        return {
            "chords": chord_progression,
            "description": description,
            "inspirations": inspirations,
            "source": "chord_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_chord_progression: {str(e)}")
        return {
            "error": str(e),
            "source": "chord_generator_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_lyrics(description: str, inspirations: List[str], chords: Dict[str, List[str]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate lyrics for verse and chorus based on description and inspirations"""
    try:
        # Prepare system message for lyrics generation
        system_message = """You are a lyricist specializing in songwriting. 
        You'll create lyrics for a verse and chorus based on a song description and musical inspirations.
        Focus on creating ONE verse and ONE chorus that fit with the given chord progressions in 4/4 time.
        Your lyrics should match the mood and theme suggested by both the description and chord progressions.
        Your response should be in JSON format with 'verse' and 'chorus' keys, each containing the lyrics as a string."""
        
        # Prepare messages for the LLM
        inspirations_str = ", ".join(inspirations)
        chords_str = json.dumps(chords)
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Create lyrics for a song with this description: {description}\n\n"
                                        f"Musical inspirations: {inspirations_str}\n\n"
                                        f"Chord progressions: {chords_str}"}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Generate lyrics
        lyrics_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.8  # Higher temperature for more creative lyrics
        )
        
        # Extract JSON from the response
        import re
        json_match = re.search(r'({.*?})', lyrics_response.replace('\n', ' '), re.DOTALL)
        
        if json_match:
            lyrics_json = json_match.group(1)
            lyrics = json.loads(lyrics_json)
        else:
            # Fallback to parsing manually if JSON format is not perfect
            logger.warning("Couldn't parse JSON directly, attempting manual extraction")
            
            verse_match = re.search(r'verse"?\s*:\s*"(.*?)"', lyrics_response, re.DOTALL)
            chorus_match = re.search(r'chorus"?\s*:\s*"(.*?)"', lyrics_response, re.DOTALL)
            
            verse_lyrics = ""
            chorus_lyrics = ""
            
            if verse_match:
                verse_lyrics = verse_match.group(1).strip()
            else:
                # Look for verse content not in JSON format
                verse_section = re.search(r'Verse:?\s*(.*?)(?=Chorus:|$)', lyrics_response, re.DOTALL)
                if verse_section:
                    verse_lyrics = verse_section.group(1).strip()
            
            if chorus_match:
                chorus_lyrics = chorus_match.group(1).strip()
            else:
                # Look for chorus content not in JSON format
                chorus_section = re.search(r'Chorus:?\s*(.*?)(?=Verse:|$)', lyrics_response, re.DOTALL)
                if chorus_section:
                    chorus_lyrics = chorus_section.group(1).strip()
            
            lyrics = {
                "verse": verse_lyrics if verse_lyrics else "Default verse lyrics for the song.",
                "chorus": chorus_lyrics if chorus_lyrics else "Default chorus lyrics for the song."
            }
        
        return {
            "lyrics": lyrics,
            "description": description,
            "inspirations": inspirations,
            "chords": chords,
            "source": "lyrics_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_lyrics: {str(e)}")
        return {
            "error": str(e),
            "source": "lyrics_generator_error",
            "timestamp": datetime.now().isoformat()
        }

def generate_melody(description: str, inspirations: List[str], chords: Dict[str, List[str]], lyrics: Dict[str, str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate melody based on lyrics and chords"""
    try:
        # Prepare system message for melody generation
        system_message = """You are a melody composer specializing in songwriting. 
        You'll create a melody for verse and chorus lyrics based on chord progressions.
        Focus on assigning notes and durations to each syllable of the lyrics in 4/4 time.
        For each syllable, specify a pitch (e.g., C4, D4, E4) and a duration (in quarter notes).
        Your response should be in JSON format with 'verse' and 'chorus' keys, each containing an array of note objects.
        Each note object should have 'pitch', 'duration', and 'syllable' keys."""
        
        # Prepare messages for the LLM
        inspirations_str = ", ".join(inspirations)
        chords_str = json.dumps(chords)
        lyrics_str = json.dumps(lyrics)
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Create a melody for a song with this description: {description}\n\n"
                                        f"Musical inspirations: {inspirations_str}\n\n"
                                        f"Chord progressions: {chords_str}\n\n"
                                        f"Lyrics: {lyrics_str}\n\n"
                                        f"For each syllable in the lyrics, specify a note (pitch like C4, D4, etc.) and duration (in quarter notes, e.g., 0.5 for eighth note, 1.0 for quarter note, etc.)."}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context)
            messages.append({"role": "user", "content": f"Additional context: {context_str}"})
        
        # Generate melody
        melody_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        # Extract JSON from the response
        import re
        json_match = re.search(r'({.*})', melody_response.replace('\n', ' '), re.DOTALL)
        
        melody = {
            "verse": [],
            "chorus": []
        }
        
        if json_match:
            try:
                melody_json = json_match.group(1)
                melody_data = json.loads(melody_json)
                melody = melody_data
            except json.JSONDecodeError:
                logger.warning("JSON decode error, using manual extraction")
                # Continue to manual extraction
        
        # If JSON parsing failed or didn't get expected structure, try manual extraction
        if not melody.get("verse") and not melody.get("chorus"):
            logger.warning("Using manual extraction for melody")
            
            # Look for verse notes
            verse_section = re.search(r'verse"?\s*:\s*\[(.*?)\]', melody_response, re.DOTALL)
            if verse_section:
                verse_notes_str = verse_section.group(1)
                
                # Extract individual note objects
                note_pattern = r'{(.*?)}'
                note_matches = re.finditer(note_pattern, verse_notes_str)
                
                for note_match in note_matches:
                    note_str = note_match.group(1)
                    
                    # Extract pitch, duration, and syllable
                    pitch_match = re.search(r'pitch"?\s*:\s*"?([A-G][#b]?[0-9])"?', note_str)
                    duration_match = re.search(r'duration"?\s*:\s*([0-9.]+)', note_str)
                    syllable_match = re.search(r'syllable"?\s*:\s*"([^"]*)"', note_str)
                    
                    if pitch_match and duration_match:
                        pitch = pitch_match.group(1)
                        duration = float(duration_match.group(1))
                        syllable = syllable_match.group(1) if syllable_match else ""
                        
                        melody["verse"].append({
                            "pitch": pitch,
                            "duration": duration,
                            "syllable": syllable
                        })
            
            # Look for chorus notes
            chorus_section = re.search(r'chorus"?\s*:\s*\[(.*?)\]', melody_response, re.DOTALL)
            if chorus_section:
                chorus_notes_str = chorus_section.group(1)
                
                # Extract individual note objects
                note_pattern = r'{(.*?)}'
                note_matches = re.finditer(note_pattern, chorus_notes_str)
                
                for note_match in note_matches:
                    note_str = note_match.group(1)
                    
                    # Extract pitch, duration, and syllable
                    pitch_match = re.search(r'pitch"?\s*:\s*"?([A-G][#b]?[0-9])"?', note_str)
                    duration_match = re.search(r'duration"?\s*:\s*([0-9.]+)', note_str)
                    syllable_match = re.search(r'syllable"?\s*:\s*"([^"]*)"', note_str)
                    
                    if pitch_match and duration_match:
                        pitch = pitch_match.group(1)
                        duration = float(duration_match.group(1))
                        syllable = syllable_match.group(1) if syllable_match else ""
                        
                        melody["chorus"].append({
                            "pitch": pitch,
                            "duration": duration,
                            "syllable": syllable
                        })
        
        # If still empty, create a simple default melody
        if not melody.get("verse"):
            # Create a simple default melody
            verse_syllables = syllabify(lyrics.get("verse", "Default verse lyrics"))
            melody["verse"] = generate_default_melody(verse_syllables, chords.get("verse", ["C", "G", "Am", "F"]))
        
        if not melody.get("chorus"):
            # Create a simple default melody
            chorus_syllables = syllabify(lyrics.get("chorus", "Default chorus lyrics"))
            melody["chorus"] = generate_default_melody(chorus_syllables, chords.get("chorus", ["F", "C", "G", "Am"]))
        
        return {
            "melody": melody,
            "description": description,
            "inspirations": inspirations,
            "chords": chords,
            "lyrics": lyrics,
            "source": "melody_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_melody: {str(e)}")
        return {
            "error": str(e),
            "source": "melody_generator_error",
            "timestamp": datetime.now().isoformat()
        }

def syllabify(text):
    """Simple syllable counter - splits text into approximate syllables"""
    if not text:
        return []
        
    # Remove punctuation except apostrophes
    import re
    text = re.sub(r'[^\w\s\']', '', text)
    
    # Split into words
    words = text.split()
    
    syllables = []
    for word in words:
        # Count vowel sequences as syllables
        vowels = "aeiouy"
        count = 0
        in_vowel_group = False
        
        for char in word.lower():
            if char in vowels:
                if not in_vowel_group:
                    count += 1
                    in_vowel_group = True
            else:
                in_vowel_group = False
        
        # Ensure at least one syllable per word
        if count == 0:
            count = 1
            
        # Add each syllable to the list
        for i in range(count):
            syllables.append(word if count == 1 else f"{word}_{i+1}")
    
    return syllables

def generate_default_melody(syllables, chords):
    """Generate a simple default melody based on syllables and chords"""
    if not syllables or not chords:
        return []
    
    # Basic pitches for each chord
    chord_pitches = {
        "C": ["C4", "E4", "G4"],
        "G": ["G4", "B4", "D4"],
        "Am": ["A4", "C4", "E4"],
        "F": ["F4", "A4", "C4"],
        "Dm": ["D4", "F4", "A4"],
        "Em": ["E4", "G4", "B4"],
        # Add more chords as needed
    }
    
    # Default to C major scale if chord not recognized
    default_pitches = ["C4", "D4", "E4", "F4", "G4", "A4", "B4"]
    
    melody = []
    chord_idx = 0
    beats_per_chord = 4  # 4 beats per chord in 4/4 time
    current_beat = 0
    
    for syllable in syllables:
        # Determine which chord we're currently on
        current_chord = chords[chord_idx % len(chords)]
        
        # Get available pitches for this chord
        available_pitches = chord_pitches.get(current_chord, default_pitches)
        
        # Choose a pitch based on position in the sequence
        pitch_idx = len(melody) % len(available_pitches)
        pitch = available_pitches[pitch_idx]
        
        # Default to quarter notes, with occasional eighth notes
        duration = 0.5 if len(melody) % 3 == 0 else 1.0
        
        # Add the note to the melody
        melody.append({
            "pitch": pitch,
            "duration": duration,
            "syllable": syllable
        })
        
        # Update beat counter
        current_beat += duration
        
        # Move to next chord if we've filled this one
        if current_beat >= beats_per_chord:
            chord_idx += 1
            current_beat = 0
    
    return melody

# Define AutoGen tool functions with proper format
def register_autogen_functions():
    """Register functions as tools for AutoGen agents"""
    function_map = {
        "generate_chords": {
            "name": "generate_chords",
            "description": "Generate chord progressions for verse and chorus",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the song's theme and mood"
                    },
                    "inspirations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of musical artists that inspire this song"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for chord generation"
                    }
                },
                "required": ["description", "inspirations"]
            },
            "function": generate_chord_progression
        },
        "generate_lyrics": {
            "name": "generate_lyrics",
            "description": "Generate lyrics for verse and chorus",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the song's theme and mood"
                    },
                    "inspirations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of musical artists that inspire this song"
                    },
                    "chords": {
                        "type": "object",
                        "description": "Chord progressions for verse and chorus"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for lyrics generation"
                    }
                },
                "required": ["description", "inspirations", "chords"]
            },
            "function": generate_lyrics
        },
        "generate_melody": {
            "name": "generate_melody",
            "description": "Generate melody based on lyrics and chords",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the song's theme and mood"
                    },
                    "inspirations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of musical artists that inspire this song"
                    },
                    "chords": {
                        "type": "object",
                        "description": "Chord progressions for verse and chorus"
                    },
                    "lyrics": {
                        "type": "object",
                        "description": "Lyrics for verse and chorus"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context for melody generation"
                    }
                },
                "required": ["description", "inspirations", "chords", "lyrics"]
            },
            "function": generate_melody
        }
    }
    
    return function_map

# AutoGen Agent System
class SongwritingAgentSystem:
    def __init__(self):
        """Initialize the AutoGen-based songwriting agent system"""
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
            "temperature": 0.7  # Higher temperature for creative agents
        }
        
        # Register tool functions
        self.function_map = register_autogen_functions()
        
        # Create the router agent (LLM-based)
        self.router_agent = AssistantAgent(
            name="RouterAgent",
            system_message="""You are a songwriting assistant router. Your job is to determine which specialist to route 
            user queries to based on the content. You have three specialists available:
            1. ChordProgressionAgent - For generating chord progressions
            2. LyricsAgent - For generating lyrics
            3. MelodyAgent - For creating melodies
            
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
                                    "enum": ["ChordProgressionAgent", "LyricsAgent", "MelodyAgent"]
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
        self.chord_progression_agent = AssistantAgent(
            name="ChordProgressionAgent",
            system_message="You are a music theory expert specializing in chord progressions. You can generate chord progressions for verse and chorus based on song descriptions and musical inspirations.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_chords"]
                ]
            }
        )
        
        self.lyrics_agent = AssistantAgent(
            name="LyricsAgent",
            system_message="You are a lyricist specializing in songwriting. You can create lyrics for verse and chorus based on song descriptions, musical inspirations, and chord progressions.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_lyrics"]
                ]
            }
        )
        
        self.melody_agent = AssistantAgent(
            name="MelodyAgent",
            system_message="You are a melody composer specializing in songwriting. You can create melodies for lyrics based on chord progressions and lyrics.",
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_melody"]
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
            "ChordProgressionAgent": self.function_map["generate_chords"]["function"],
            "LyricsAgent": self.function_map["generate_lyrics"]["function"],
            "MelodyAgent": self.function_map["generate_melody"]["function"]
        }
    
    async def create_song(self, description: str, inspirations: List[str], title: Optional[str] = None, tempo: int = 120) -> Response:
        """Create a complete song using the agent system"""
        try:
            # Step 1: Generate chord progressions
            logger.info("Generating chord progressions...")
            chord_result = generate_chord_progression(description, inspirations)
            
            if "error" in chord_result:
                return Response(
                    result=f"Error generating chord progressions: {chord_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            chords = chord_result["chords"]
            logger.info(f"Generated chords: {chords}")
            
            # Step 2: Generate lyrics
            logger.info("Generating lyrics...")
            lyrics_result = generate_lyrics(description, inspirations, chords)
            
            if "error" in lyrics_result:
                return Response(
                    result=f"Error generating lyrics: {lyrics_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            lyrics = lyrics_result["lyrics"]
            logger.info(f"Generated lyrics for verse and chorus")
            
            # Step 3: Generate melody
            logger.info("Generating melody...")
            melody_result = generate_melody(description, inspirations, chords, lyrics)
            
            if "error" in melody_result:
                return Response(
                    result=f"Error generating melody: {melody_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            melody = melody_result["melody"]
            logger.info(f"Generated melody for verse and chorus")
            
            # Step 4: Generate MIDI file
            if not title:
                title = f"Song about {description[:20]}"
            
            logger.info(f"Generating MIDI file with title: {title}, tempo: {tempo}...")
            midi_path = MusicProcessor.generate_midi_file(chords, melody, title, tempo)
            
            # Prepare result
            result = {
                "title": title,
                "description": description,
                "inspirations": inspirations,
                "tempo": tempo,
                "chords": chords,
                "lyrics": lyrics,
                "melody_summary": {
                    "verse_notes": len(melody["verse"]),
                    "chorus_notes": len(melody["chorus"])
                },
                "midi_file": midi_path
            }
            
            return Response(
                result=result,
                source="songwriting_system",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in create_song: {str(e)}")
            return Response(
                result=f"Error creating song: {str(e)}",
                source="agent_error",
                timestamp=datetime.now().isoformat()
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

@app.get("/api/download/{song_title}")
async def download_midi(song_title: str):
    """Download the generated MIDI file"""
    try:
        # Find the MIDI file in the songs directory
        songs_dir = os.path.join(os.getcwd(), "songs")
        safe_title = "".join([c for c in song_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        if not safe_title:
            safe_title = "song"
            
        # Path to the song's directory and MIDI file
        song_dir = os.path.join(songs_dir, safe_title.replace(' ', '_'))
        midi_path = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
        
        if not os.path.exists(midi_path):
            raise HTTPException(status_code=404, detail=f"MIDI file for '{song_title}' not found")
        
        return FileResponse(
            path=midi_path,
            filename=f"{safe_title}.mid",
            media_type="audio/midi"
        )
    except Exception as e:
        logger.error(f"Error downloading MIDI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading MIDI: {str(e)}")

# API endpoints for song management
@app.get("/api/songs")
def list_songs():
    """List all generated songs"""
    try:
        songs_dir = os.path.join(os.getcwd(), "songs")
        if not os.path.exists(songs_dir):
            return {"songs": []}
        
        songs = []
        for song_folder in os.listdir(songs_dir):
            folder_path = os.path.join(songs_dir, song_folder)
            if os.path.isdir(folder_path):
                # Try to read song_info.json if it exists
                info_path = os.path.join(folder_path, "song_info.json")
                if os.path.exists(info_path):
                    try:
                        with open(info_path, 'r') as f:
                            song_info = json.load(f)
                            songs.append({
                                "title": song_info.get("title", song_folder.replace('_', ' ')),
                                "creation_date": song_info.get("creation_date", ""),
                                "folder": song_folder
                            })
                    except:
                        # If JSON can't be read, just use the folder name
                        songs.append({
                            "title": song_folder.replace('_', ' '),
                            "folder": song_folder
                        })
                else:
                    # No song_info.json, just use the folder name
                    songs.append({
                        "title": song_folder.replace('_', ' '),
                        "folder": song_folder
                    })
        
        return {"songs": songs}
    except Exception as e:
        logger.error(f"Error listing songs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing songs: {str(e)}")

@app.get("/api/songs/{song_title}")
def get_song_details(song_title: str):
    """Get details of a specific song"""
    try:
        songs_dir = os.path.join(os.getcwd(), "songs")
        safe_title = "".join([c for c in song_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        if not safe_title:
            safe_title = "song"
            
        song_dir = os.path.join(songs_dir, safe_title.replace(' ', '_'))
        
        if not os.path.exists(song_dir):
            raise HTTPException(status_code=404, detail=f"Song '{song_title}' not found")
            
        # Read song_info.json if it exists
        info_path = os.path.join(song_dir, "song_info.json")
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                song_info = json.load(f)
                # Add the path to the MIDI file
                song_info["midi_file"] = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
                return song_info
        else:
            # Basic info if no JSON file
            return {
                "title": song_title,
                "midi_file": os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting song details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting song details: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)