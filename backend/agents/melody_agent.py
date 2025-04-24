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
        
        YOUR RESPONSE MUST BE VALID JSON in this exact format:
        {
          "verse": [
            {"pitch": "C4", "duration": 1.0, "syllable": "first"},
            {"pitch": "D4", "duration": 0.5, "syllable": "sec"},
            {"pitch": "E4", "duration": 0.5, "syllable": "ond"}
          ],
          "chorus": [
            {"pitch": "G4", "duration": 1.0, "syllable": "cho"},
            {"pitch": "F4", "duration": 1.0, "syllable": "rus"}
          ]
        }
        
        For each syllable, specify a pitch (e.g., C4, D4, E4) and a duration (in quarter notes).
        DO NOT include any explanation or additional text in your response, ONLY the JSON."""
        
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
            max_tokens=4000,
            temperature=0.7
        )
        
        # Try to load the JSON directly
        try:
            melody = json.loads(melody_response)
            logger.info("Successfully parsed melody JSON")
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the response
            logger.warning("Direct JSON parse failed, trying to extract JSON object")
            json_match = re.search(r'({.*})', melody_response.replace('\n', ' '), re.DOTALL)
            
            if json_match:
                try:
                    melody_json = json_match.group(1)
                    melody = json.loads(melody_json)
                    logger.info("Successfully extracted and parsed melody JSON")
                except json.JSONDecodeError:
                    logger.warning("JSON extraction failed, using default melody")
                    melody = None
            else:
                logger.warning("No JSON found in response, using default melody")
                melody = None
        
        # If still empty, create a default melody
        if not melody or not isinstance(melody, dict) or "verse" not in melody or "chorus" not in melody:
            logger.warning("Using default melody generation")
            # Create a simple default melody
            verse_syllables = syllabify(lyrics.get("verse", "Default verse lyrics"))
            chorus_syllables = syllabify(lyrics.get("chorus", "Default chorus lyrics"))
            
            melody = {
                "verse": generate_default_melody(verse_syllables, chords.get("verse", ["C", "G", "Am", "F"])),
                "chorus": generate_default_melody(chorus_syllables, chords.get("chorus", ["F", "C", "G", "Am"]))
            }
        
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