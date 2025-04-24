"""
Drum pattern generation agent with support for multiple musical styles
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from core.azure_client import AzureOpenAIClient
from utils.midi_utils import create_drum_pattern
from config.settings import TICKS_PER_BEAT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

# Define available drum styles
AVAILABLE_STYLES = [
    "basic",          # Standard rock/pop pattern
    "four_on_floor",  # Classic disco/house with kick on every beat
    "trap",           # Modern trap beats with rolling hi-hats
    "latin",          # Latin percussion patterns
    "pop",            # Contemporary pop patterns
    "rock",           # Rock drumming patterns
    "jazz",           # Jazz swing patterns
    "electronic",     # Electronic/EDM patterns
    "hip_hop",        # Hip-hop beats
    "r_and_b"         # R&B groove patterns
]

def generate_drum_pattern(tempo: int = 120, style: str = "basic", bars: int = 8, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a drum pattern with the specified style and number of bars
    
    Args:
        tempo: The tempo in BPM
        style: The style of the drum pattern (e.g., "basic", "four_on_floor", "latin")
        bars: Number of bars to generate
        context: Additional context (e.g., song description, inspirations)
    
    Returns:
        Dictionary containing the generated drum pattern and metadata
    """
    try:
        # Normalize style input
        normalized_style = style.lower().replace(" ", "_").replace("-", "_") if style else "basic"
        
        # If style is not recognized, use AI to determine the most appropriate style
        if normalized_style not in AVAILABLE_STYLES:
            determined_style = _determine_style_with_ai(tempo, context)
            logger.info(f"Style '{style}' not recognized, using AI-determined style: {determined_style}")
            normalized_style = determined_style
        
        # Generate the drum pattern using the appropriate style
        drum_track = create_drum_pattern(tempo, bars, normalized_style)
        
        return {
            "drum_track": drum_track,
            "tempo": tempo,
            "style": normalized_style,
            "bars": bars,
            "source": "drum_generator",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in generate_drum_pattern: {str(e)}")
        return {
            "error": str(e),
            "source": "drum_generator_error",
            "timestamp": datetime.now().isoformat()
        }

def _determine_style_with_ai(tempo: int, context: Optional[Dict[str, Any]]) -> str:
    """Use the AI to determine the most appropriate drum style based on context
    
    Args:
        tempo: The tempo in BPM
        context: Additional context about the song
        
    Returns:
        The determined drum style string
    """
    try:
        # Extract useful information from context
        description = context.get("description", "") if context else ""
        inspirations = context.get("inspirations", []) if context else []
        
        # Prepare system message for style determination
        system_message = """You are a music production expert specializing in drum programming.
        Based on the provided song information (tempo, description, inspirations), 
        determine the most appropriate drum style from the following options:
        - basic: Standard rock/pop pattern
        - four_on_floor: Classic disco/house with kick on every beat
        - trap: Modern trap beats with rolling hi-hats
        - latin: Latin percussion patterns
        - pop: Contemporary pop patterns
        - rock: Rock drumming patterns
        - jazz: Jazz swing patterns
        - electronic: Electronic/EDM patterns
        - hip_hop: Hip-hop beats
        - r_and_b: R&B groove patterns
        
        Respond with ONLY the style name, nothing else."""
        
        # Prepare messages for the LLM
        inspirations_str = ", ".join(inspirations) if inspirations else ""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Determine the most appropriate drum style for a song with:\n"
                                        f"Tempo: {tempo} BPM\n"
                                        f"Description: {description}\n"
                                        f"Inspirations: {inspirations_str}"}
        ]
        
        # Get AI recommendation
        style_response = ai_client.generate_chat_completion(
            messages=messages,
            max_tokens=50,
            temperature=0.3  # Lower temperature for more deterministic results
        )
        
        # Clean and normalize the response
        style = style_response.strip().lower()
        
        # Extract just the style name if there's additional text
        for available_style in AVAILABLE_STYLES:
            if available_style in style:
                return available_style
        
        # Default to basic if no match found
        logger.warning(f"Could not determine style from AI response: '{style}', defaulting to 'basic'")
        return "basic"
        
    except Exception as e:
        logger.error(f"Error determining style with AI: {str(e)}")
        return "basic"  # Default to basic on error