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