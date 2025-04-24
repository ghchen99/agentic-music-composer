"""
Drum pattern generation agent
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import mido
from mido import Message, MidiTrack

from core.azure_client import AzureOpenAIClient
from config.settings import TICKS_PER_BEAT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
ai_client = AzureOpenAIClient()

def generate_drum_pattern(tempo: int = 120, style: str = "basic", bars: int = 8, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a drum pattern with the specified style and number of bars"""
    try:
        if style == "basic" or not style:
            # For basic style, use the predefined pattern
            drum_track = create_basic_drum_pattern(tempo, bars)
            
            return {
                "drum_track": drum_track,
                "tempo": tempo,
                "style": style,
                "bars": bars,
                "source": "drum_generator",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # For custom styles, could use AI to generate different patterns
            # This is a placeholder for future development
            system_message = """You are a drum programming expert. 
            Create a drum pattern in the specified style, describing the kick, snare, and hi-hat patterns
            for the requested number of bars."""
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create a {style} drum pattern for {bars} bars at {tempo} BPM."}
            ]
            
            # Add context if provided
            if context:
                context_str = json.dumps(context)
                messages.append({"role": "user", "content": f"Additional context: {context_str}"})
            
            # This would be expanded in a full implementation to actually use the AI response
            # to create a custom drum pattern
            _ = ai_client.generate_chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            # For now, just return the basic pattern
            drum_track = create_basic_drum_pattern(tempo, bars)
            
            return {
                "drum_track": drum_track,
                "tempo": tempo,
                "style": style,
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

def create_basic_drum_pattern(tempo: int = 120, bars: int = 8) -> MidiTrack:
    """Create a basic drum track with the specified number of bars"""
    # Create a drum track
    drum_track = MidiTrack()
    drum_track.append(mido.MetaMessage('track_name', name='Drums', time=0))
    drum_track.append(Message('program_change', program=0, channel=9, time=0))  # Drums channel

    # Define drum notes (General MIDI drum map)
    kick_drum = 36      # Bass Drum 1
    snare_drum = 38     # Acoustic Snare
    closed_hihat = 42   # Closed Hi-Hat

    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds

    # Define velocities for dynamic feel
    kick_velocity = 110
    snare_velocity = 100
    hihat_velocity = 90

    # Pattern for measures in the song structure
    def add_measure(track):
        """Add one measure of the drum pattern: kick, hihat, snare, hihat, hihat, kick, snare, hihat"""
        
        # 1: Kick
        track.append(Message('note_on', note=kick_drum, velocity=kick_velocity, channel=9, time=0))
        track.append(Message('note_off', note=kick_drum, velocity=0, channel=9, time=note_duration))
        
        # 2: Hi-hat
        track.append(Message('note_on', note=closed_hihat, velocity=hihat_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=note_duration))
        
        # 3: Snare
        track.append(Message('note_on', note=snare_drum, velocity=snare_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=snare_drum, velocity=0, channel=9, time=note_duration))
        
        # 4: Hi-hat
        track.append(Message('note_on', note=closed_hihat, velocity=hihat_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=note_duration))
        
        # 5: Hi-hat
        track.append(Message('note_on', note=closed_hihat, velocity=hihat_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=note_duration))
        
        # 6: Kick
        track.append(Message('note_on', note=kick_drum, velocity=kick_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=kick_drum, velocity=0, channel=9, time=note_duration))
        
        # 7: Snare
        track.append(Message('note_on', note=snare_drum, velocity=snare_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=snare_drum, velocity=0, channel=9, time=note_duration))
        
        # 8: Hi-hat
        track.append(Message('note_on', note=closed_hihat, velocity=hihat_velocity, channel=9, time=eighth-note_duration))
        track.append(Message('note_off', note=closed_hihat, velocity=0, channel=9, time=note_duration))

    # Add the requested number of measures
    for _ in range(bars):
        add_measure(drum_track)

    # Set tempo for the drum track
    tempo_microseconds = mido.bpm2tempo(tempo)
    drum_track.append(mido.MetaMessage('set_tempo', tempo=tempo_microseconds, time=0))
    
    return drum_track