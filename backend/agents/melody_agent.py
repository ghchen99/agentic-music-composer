"""
Melody generation agent
"""

import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.azure_client import AzureOpenAIClient
from utils.music_theory import syllabify

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

def generate_melody(description: str, inspirations: List[str], chords: Dict[str, List[str]], lyrics: Dict[str, str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate melody based on lyrics and chords"""
    try:
        # Prepare system message for melody generation
        system_message = """You are a melody composer for a 16-bar song (verse and chorus).
        STRUCTURE:
        - Verse: (4 chords repeats twice, 8 bars total)
        - Chorus: (4 chords repeats twice, 8 bars total)
        - Each lyric line spans EXACTLY 2 bars (duration sum = 2.0)

        RHYTHMIC REQUIREMENTS:
        - Use varied durations: 0.25, 0.5, 0.75, 1.0, 1.5, 2.0
        - For rests, use pitch: "rest" (exactly this string, lowercase)
        - Create repeating 4-bar motifs with variations
        - Ensure syncopation and rhythmic interest

        MELODY GUIDELINES:
        - Verse: Stepwise motion, narrow range, conversational feel
        - Chorus: Consonant interval jumps (3rds, 4ths, 5ths), memorable hook
        - Land on chord tones on strong beats
        - Non-chord tones must resolve smoothly

        IMPORTANT: Return ONLY raw JSON with this exact structure:
        {
        "verse": [
            {"pitch": "C4", "duration": 0.5, "syllable": "first"},
            {"pitch": "rest", "duration": 0.5, "syllable": ""},
            {"pitch": "D4", "duration": 0.5, "syllable": "syl"},
            {"pitch": "E4", "duration": 0.5, "syllable": "la-ble"}
        ],
        "chorus": [
            {"pitch": "G4", "duration": 1.0, "syllable": "cho"},
            {"pitch": "F4", "duration": 0.5, "syllable": "rus"},
            {"pitch": "rest", "duration": 0.5, "syllable": ""}
        ]
        }

        CRITICAL RULES:
        - Each 2-bar phrase must sum to exactly 2.0 in duration
        - For rests, always use the string "rest" (lowercase) as the pitch value
        - Empty syllables for rests should have an empty string
        - Include EVERY syllable from the provided lyrics
        - Double-check that your output is valid JSON before submitting
        - Respond with NOTHING except the JSON object"""
        
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
        
        # Final reminder to return only structured JSON
        messages.append({"role": "user", "content": "Remember to respond with ONLY the JSON object containing verse and chorus melodies. No explanation text, no code blocks, just the raw JSON object."})
        
        # Generate melody
        melody_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=8000,
            temperature=0.7,
            structured_output=True  # Signal to the client that we want structured JSON
        )
        
        # Parse the response
        melody = parse_melody_response(melody_response, lyrics, chords)
        
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

def parse_melody_response(response: str, lyrics: Dict[str, str], chords: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Parse the LLM response to extract melody JSON using multiple strategies
    
    Args:
        response: The raw response from the LLM
        lyrics: Lyrics dict with verse and chorus
        chords: Chords dict with verse and chorus progressions
        
    Returns:
        Dict with verse and chorus melodies
    """
    # Try to load the JSON directly
    try:
        melody = json.loads(response)
        if isinstance(melody, dict) and "verse" in melody and "chorus" in melody:
            # Validate the structure - each item should have pitch, duration, syllable
            valid_structure = all(
                isinstance(note, dict) and "pitch" in note and "duration" in note and "syllable" in note
                for section in ["verse", "chorus"]
                for note in melody[section]
            )
            
            if valid_structure:
                logger.info("Successfully parsed melody JSON directly")
                return melody
            else:
                logger.warning("JSON parsed but has invalid structure")
    except json.JSONDecodeError:
        logger.warning("Direct JSON parsing failed, trying alternative methods")
    
    # Try to extract JSON from the response
    if "```" in response:
        try:
            # Extract content between code blocks, regardless of language specifier
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if match:
                clean_response = match.group(1)
                melody = json.loads(clean_response)
                if isinstance(melody, dict) and "verse" in melody and "chorus" in melody:
                    logger.info("Successfully extracted and parsed melody JSON from code block")
                    return melody
        except (json.JSONDecodeError, AttributeError):
            logger.warning("JSON extraction from code block failed")
    
    return melody