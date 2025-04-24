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
        You'll create lyrics for a 16-bar cycle song with verse and chorus based on a song description and musical inspirations.
        
        IMPORTANT STRUCTURE:
        - Verse: The chord progression repeats twice (8 bars total)
        - Chorus: The chord progression repeats twice (8 bars total)
        - Each line of lyrics should span TWO CHORDS (2 bars of music)
        - This means 4 lines of lyrics for verse and 4 lines for chorus
        
        Your lyrics should match the mood and theme suggested by both the description and chord progressions.
        Ensure verse lyrics have a narrative flow that leads naturally into the chorus.
        The chorus should be more emotionally direct and memorable than the verse.
        
        IMPORTANT: Return ONLY raw JSON with no markdown formatting, code blocks, or explanation.
        Your response must be a valid JSON object with 'verse' and 'chorus' keys, each containing the lyrics as a string.
        Example format: {"verse": "Line 1\\nLine 2\\nLine 3\\nLine 4", "chorus": "Chorus line 1\\nChorus line 2\\nChorus line 3\\nChorus line 4"}"""
        
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
        
        # Final reminder to return only structured JSON
        messages.append({"role": "user", "content": "Remember to respond with ONLY the JSON object containing verse and chorus lyrics. No explanation text, no code blocks, just the raw JSON object."})
        
        # Generate lyrics
        lyrics_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.8,  # Higher temperature for more creative lyrics
            structured_output=True  # Signal to the client that we want structured JSON
        )
        
        # Parse the response using multiple strategies
        lyrics = parse_lyrics_response(lyrics_response)
        
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

def parse_lyrics_response(response: str) -> Dict[str, str]:
    """Parse the LLM response to extract lyrics JSON using multiple strategies
    
    Args:
        response: The raw response from the LLM
        
    Returns:
        Dict with verse and chorus lyrics
    """
    # Default fallback lyrics
    default_lyrics = {
        "verse": "Default verse lyrics line 1\nDefault verse lyrics line 2\nDefault verse lyrics line 3\nDefault verse lyrics line 4",
        "chorus": "Default chorus lyrics line 1\nDefault chorus lyrics line 2\nDefault chorus lyrics line 3\nDefault chorus lyrics line 4"
    }
    
    # Strategy 1: Try direct JSON parsing
    try:
        lyrics = json.loads(response)
        # Validate the structure
        if isinstance(lyrics, dict) and "verse" in lyrics and "chorus" in lyrics:
            logger.info("Successfully parsed lyrics JSON directly")
            return lyrics
        else:
            logger.warning("JSON parsed but missing required keys")
    except json.JSONDecodeError:
        logger.warning("Direct JSON parsing failed, trying alternative methods")
    
    # Strategy 2: Try to extract JSON from code blocks
    if "```" in response:
        try:
            # Extract content between code blocks, regardless of language specifier
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if match:
                clean_response = match.group(1)
                lyrics = json.loads(clean_response)
                if isinstance(lyrics, dict) and "verse" in lyrics and "chorus" in lyrics:
                    logger.info("Successfully extracted and parsed JSON from code block")
                    return lyrics
        except (json.JSONDecodeError, AttributeError):
            logger.warning("JSON extraction from code block failed")
    
    # Strategy 3: Manual extraction of verse and chorus using regex
    try:
        verse_match = re.search(r'verse"?\s*:\s*"(.*?)"', response, re.DOTALL)
        chorus_match = re.search(r'chorus"?\s*:\s*"(.*?)"', response, re.DOTALL)
        
        verse_lyrics = ""
        chorus_lyrics = ""
        
        if verse_match:
            verse_lyrics = verse_match.group(1).strip()
            # Replace escaped newlines with actual newlines
            verse_lyrics = verse_lyrics.replace("\\n", "\n")
        else:
            # Look for verse content not in JSON format
            verse_section = re.search(r'Verse:?\s*(.*?)(?=Chorus:|$)', response, re.DOTALL)
            if verse_section:
                verse_lyrics = verse_section.group(1).strip()
        
        if chorus_match:
            chorus_lyrics = chorus_match.group(1).strip()
            # Replace escaped newlines with actual newlines
            chorus_lyrics = chorus_lyrics.replace("\\n", "\n")
        else:
            # Look for chorus content not in JSON format
            chorus_section = re.search(r'Chorus:?\s*(.*?)(?=Verse:|$)', response, re.DOTALL)
            if chorus_section:
                chorus_lyrics = chorus_section.group(1).strip()
        
        if verse_lyrics and chorus_lyrics:
            logger.info("Successfully extracted lyrics using regex")
            return {
                "verse": verse_lyrics,
                "chorus": chorus_lyrics
            }
    except Exception as e:
        logger.warning(f"Regex extraction failed: {str(e)}")
    
    # If all parsing attempts fail, return default lyrics
    logger.warning("All parsing attempts failed, using default lyrics")
    return default_lyrics