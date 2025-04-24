"""
Lyrics generation agent
"""

import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.azure_client import AzureOpenAIClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

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