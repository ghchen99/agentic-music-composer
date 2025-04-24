"""
Melody generation agent
"""

import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.azure_client import AzureOpenAIClient
from utils.music_theory import syllabify, generate_default_melody

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

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