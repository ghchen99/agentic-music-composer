"""
Chord progression generation agent
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

def generate_chord_progression(description: str, inspirations: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate chord progressions for verse and chorus"""
    try:
        # Prepare system message for chord progression generation
        system_message = """You are a music theory expert specializing in songwriting. 
        You'll create chord progressions for a verse and chorus based on a song description and musical inspirations.
        Focus on creating ONE 4-chord progression for the verse and ONE 4-chord progression for the chorus in 4/4 time.
        Use standard chord notation (e.g., C, G, Am, F).
        
        IMPORTANT: Return ONLY raw JSON with no markdown formatting, code blocks, or explanation.
        Your response must be a valid JSON object with 'verse' and 'chorus' keys, each with an array of 4 chords.
        Example format: {"verse": ["C", "G", "Am", "F"], "chorus": ["F", "C", "G", "Am"]}"""
        
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
        
        # Final reminder to return only structured JSON
        messages.append({"role": "user", "content": "Remember to respond with ONLY the JSON object containing verse and chorus chord progressions. No explanation text, no code blocks, just the raw JSON object."})
        
        # Generate chord progression
        chord_progression_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=500,
            temperature=0.7,  # Higher temperature for creative variations
            structured_output=True  # Signal to the client that we want structured JSON
        )
        
        # Parse the response using multiple strategies
        chord_progression = parse_chord_progression_response(chord_progression_response)
        
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

def parse_chord_progression_response(response: str) -> Dict[str, List[str]]:
    """Parse the LLM response to extract chord progression JSON using multiple strategies
    
    Args:
        response: The raw response from the LLM
        
    Returns:
        Dict with verse and chorus chord progressions
    """
    # Default fallback chord progressions
    default_progression = {
        "verse": ["C", "G", "Am", "F"],
        "chorus": ["F", "C", "G", "Am"]
    }
    
    # Strategy 1: Try direct JSON parsing
    try:
        chord_progression = json.loads(response)
        # Validate the structure
        if isinstance(chord_progression, dict) and "verse" in chord_progression and "chorus" in chord_progression:
            logger.info("Successfully parsed chord progression JSON directly")
            return chord_progression
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
                chord_progression = json.loads(clean_response)
                if isinstance(chord_progression, dict) and "verse" in chord_progression and "chorus" in chord_progression:
                    logger.info("Successfully extracted and parsed JSON from code block")
                    return chord_progression
        except (json.JSONDecodeError, AttributeError):
            logger.warning("JSON extraction from code block failed")
    
    # Strategy 3: Manual extraction of arrays using regex
    try:
        verse_match = re.search(r'verse"?\s*:\s*\[(.*?)\]', response, re.DOTALL)
        chorus_match = re.search(r'chorus"?\s*:\s*\[(.*?)\]', response, re.DOTALL)
        
        verse_chords = []
        chorus_chords = []
        
        if verse_match:
            verse_str = verse_match.group(1).strip()
            verse_chords = [chord.strip().strip('"\'') for chord in verse_str.split(',')]
            verse_chords = [c for c in verse_chords if c]  # Remove empty strings
        
        if chorus_match:
            chorus_str = chorus_match.group(1).strip()
            chorus_chords = [chord.strip().strip('"\'') for chord in chorus_str.split(',')]
            chorus_chords = [c for c in chorus_chords if c]  # Remove empty strings
        
        if verse_chords and chorus_chords:
            logger.info("Successfully extracted chord arrays using regex")
            return {
                "verse": verse_chords,
                "chorus": chorus_chords
            }
    except Exception as e:
        logger.warning(f"Regex extraction failed: {str(e)}")
    
    # If all parsing attempts fail, return default progression
    logger.warning("All parsing attempts failed, using default chord progressions")
    return default_progression