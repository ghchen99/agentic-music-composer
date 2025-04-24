"""
MIDI utility functions for music processing with enhanced drum pattern capabilities
"""

import logging
import mido
from mido import Message, MidiTrack, MidiFile
import random
from typing import Dict, List, Tuple

from config.settings import TICKS_PER_BEAT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define drum note values (General MIDI drum map)
DRUM_NOTES = {
    "kick": 36,            # Bass Drum 1
    "kick_alt": 35,        # Bass Drum 2
    "snare": 38,           # Acoustic Snare
    "snare_rim": 40,       # Electric Snare
    "clap": 39,            # Clap
    "closed_hihat": 42,    # Closed Hi-Hat
    "open_hihat": 46,      # Open Hi-Hat
    "pedal_hihat": 44,     # Pedal Hi-Hat
    "crash": 49,           # Crash Cymbal 1
    "ride": 51,            # Ride Cymbal 1
    "ride_bell": 53,       # Ride Bell
    "tom_high": 50,        # High Tom
    "tom_mid": 47,         # Mid Tom
    "tom_low": 45,         # Low Tom
    "percussion_high": 63, # High Conga/Bongo
    "percussion_mid": 62,  # Mid Conga/Bongo
    "percussion_low": 60,  # Low Conga/Bongo
    "tambourine": 54,      # Tambourine
    "cowbell": 56,         # Cowbell
    "clave": 75,           # Claves
    "shaker": 70,          # Maracas/Shaker
}

# Define common velocity values for dynamic feel
VELOCITIES = {
    "soft": 70,
    "normal": 90,
    "accent": 110,
    "ghost": 40,
}

def create_drum_pattern(tempo: int = 120, bars: int = 8, style: str = "basic") -> MidiTrack:
    """Create a drum track with the specified style and number of bars
    
    Parameters:
        tempo (int): The tempo in BPM
        bars (int): The number of bars to generate
        style (str): The style of drum pattern to generate
        
    Returns:
        MidiTrack: A MIDI track containing the drum pattern
    """
    drum_track = MidiTrack()
    drum_track.append(mido.MetaMessage('track_name', name=f'Drums ({style})', time=0))
    drum_track.append(Message('program_change', program=0, channel=9, time=0))  # Drums channel (9)
    
    # Calculate total ticks per bar to ensure consistent bar length
    ticks_per_bar = TICKS_PER_BEAT * 4  # 4 beats per bar in 4/4 time
    
    # Generate pattern based on style
    pattern_function = {
        "basic": _create_basic_pattern,
        "four_on_floor": _create_four_on_floor_pattern,
        "trap": _create_trap_pattern,
        "latin": _create_latin_pattern,
        "pop": _create_pop_pattern,
        "rock": _create_rock_pattern,
        "jazz": _create_jazz_pattern,
        "electronic": _create_electronic_pattern,
        "hip_hop": _create_hip_hop_pattern,
        "r_and_b": _create_rnb_pattern,
    }.get(style, _create_basic_pattern)  # Default to basic if style not found
    
    # Get the pattern for a single bar
    single_bar_events = pattern_function(ticks_per_bar)
    
    # Create the drum track for the specified number of bars
    for bar in range(bars):
        # Add a crash cymbal on the first beat of the first bar
        if bar == 0:
            drum_track.append(Message('note_on', note=DRUM_NOTES["crash"], velocity=VELOCITIES["accent"], channel=9, time=0))
            drum_track.append(Message('note_off', note=DRUM_NOTES["crash"], velocity=0, channel=9, time=50))
            
            # Adjust the first note's timing to account for the crash
            if single_bar_events and single_bar_events[0][0] == 0:
                # Skip the time offset for the first note since we just played the crash
                _, note, vel, duration = single_bar_events[0]
                drum_track.append(Message('note_on', note=note, velocity=vel, channel=9, time=0))
                drum_track.append(Message('note_off', note=note, velocity=0, channel=9, time=duration))
                events_to_process = single_bar_events[1:]
            else:
                events_to_process = single_bar_events
        else:
            events_to_process = single_bar_events
            
        # Add the rest of the pattern for this bar
        last_tick = 0
        for tick, note, velocity, duration in events_to_process:
            # Calculate the time parameter (difference from last event)
            time_param = tick - last_tick if tick > last_tick else 0
            last_tick = tick
            
            # Add the note
            drum_track.append(Message('note_on', note=note, velocity=velocity, channel=9, time=time_param))
            drum_track.append(Message('note_off', note=note, velocity=0, channel=9, time=duration))
            last_tick += duration
        
        # Make sure we end exactly at the bar boundary
        if bar < bars - 1:  # Don't add extra time after the last bar
            remaining_time = ticks_per_bar - last_tick
            if remaining_time > 0:
                # Add a silent note (or use mido.sleep) to complete the bar
                drum_track.append(Message('note_on', note=DRUM_NOTES["kick"], velocity=0, channel=9, time=remaining_time))
                drum_track.append(Message('note_off', note=DRUM_NOTES["kick"], velocity=0, channel=9, time=0))
    
    return drum_track

def _create_basic_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a basic rock/pop drum pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    # Pattern: kick, hihat, snare, hihat, hihat, kick, snare, hihat
    pattern = [
        # tick, note, velocity, duration
        (0, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration),
        (eighth, DRUM_NOTES["closed_hihat"], VELOCITIES["normal"], note_duration),
        (quarter, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration),
        (quarter + eighth, DRUM_NOTES["closed_hihat"], VELOCITIES["normal"], note_duration),
        (quarter * 2, DRUM_NOTES["closed_hihat"], VELOCITIES["normal"], note_duration),
        (quarter * 2 + eighth, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration),
        (quarter * 3, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration),
        (quarter * 3 + eighth, DRUM_NOTES["closed_hihat"], VELOCITIES["normal"], note_duration),
    ]
    
    # Add hihat for every eighth note (underneath the existing pattern)
    hihat_pattern = []
    for i in range(0, ticks_per_bar, eighth):
        hihat_pattern.append((i, DRUM_NOTES["closed_hihat"], VELOCITIES["soft"], note_duration))
    
    # Merge hihat pattern with main pattern, avoiding duplicates
    main_ticks = [item[0] for item in pattern]
    full_pattern = pattern + [item for item in hihat_pattern if item[0] not in main_ticks]
    
    # Sort by tick position
    return sorted(full_pattern, key=lambda x: x[0])

def _create_four_on_floor_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a four-on-the-floor pattern (disco, house)
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    # Basic pattern: kick on every beat, snare on 2 and 4, open hihat on offbeats
    pattern = []
    
    # Kick on every beat (1, 2, 3, 4)
    for beat in range(4):
        pattern.append((beat * quarter, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Snare on beats 2 and 4
    pattern.append((quarter, DRUM_NOTES["snare"], VELOCITIES["normal"], note_duration))
    pattern.append((3 * quarter, DRUM_NOTES["snare"], VELOCITIES["normal"], note_duration))
    
    # Open hi-hat on offbeats
    for i in range(4):
        pattern.append((i * quarter + eighth, DRUM_NOTES["open_hihat"], VELOCITIES["soft"], note_duration))
    
    # Closed hi-hat on every sixteenth
    for i in range(16):
        pattern.append((i * sixteenth, DRUM_NOTES["closed_hihat"], 
                        VELOCITIES["soft"] if i % 4 != 0 else VELOCITIES["normal"], 
                        note_duration))
    
    # Sort by tick position and remove duplicates based on tick+note
    unique_dict = {}
    for item in pattern:
        key = (item[0], item[1])  # tick, note
        if key not in unique_dict or unique_dict[key][2] < item[2]:  # prefer higher velocity
            unique_dict[key] = item
    
    return sorted(unique_dict.values(), key=lambda x: x[0])

def _create_trap_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a trap-style drum pattern with rolling hi-hats
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    thirtysecond = sixteenth // 2
    note_duration = 30  # Shorter duration for faster patterns
    
    pattern = []
    
    # Kick pattern (sparser, often syncopated)
    kick_positions = [0, quarter + eighth, quarter * 2, quarter * 3 + eighth]
    for pos in kick_positions:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Snare typically on beats 3 or 3+
    snare_positions = [quarter * 2]
    if random.random() > 0.5:  # Randomly add variation
        snare_positions.append(quarter * 3 + eighth)
    for pos in snare_positions:
        pattern.append((pos, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    
    # Rolling hi-hats (quintuplet feel)
    # This creates the characteristic trap hi-hat pattern
    total_hihats = 24  # Subdivide the bar into 24 hi-hat hits
    base_velocity = VELOCITIES["normal"] - 25
    
    for i in range(total_hihats):
        tick = (ticks_per_bar * i) // total_hihats
        # Vary velocity to create rhythm
        velocity_boost = 0
        if i % 6 == 0:  # Accent every 6th hit
            velocity_boost = 30
        elif i % 3 == 0:  # Slight accent every 3rd hit
            velocity_boost = 15
            
        velocity = min(base_velocity + velocity_boost, 127)
        
        # Alternate between closed and open hi-hat
        hat_type = DRUM_NOTES["closed_hihat"]
        if i % 12 == 6:  # Open hi-hat for variation
            hat_type = DRUM_NOTES["open_hihat"]
            
        pattern.append((tick, hat_type, velocity, note_duration))
    
    # Occasionally add clap layered with snare
    for pos in snare_positions:
        if random.random() > 0.7:  # 30% chance
            pattern.append((pos, DRUM_NOTES["clap"], VELOCITIES["normal"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_latin_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a Latin percussion pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # Clave pattern (3-2 clave)
    clave_positions = [0, quarter, quarter * 2, quarter * 2 + eighth, quarter * 3 + eighth]
    for pos in clave_positions:
        pattern.append((pos, DRUM_NOTES["clave"], VELOCITIES["accent"], note_duration))
    
    # Congas
    conga_positions = [
        (0, DRUM_NOTES["percussion_low"], VELOCITIES["accent"]),
        (eighth, DRUM_NOTES["percussion_high"], VELOCITIES["normal"]),
        (quarter, DRUM_NOTES["percussion_mid"], VELOCITIES["normal"]),
        (quarter + eighth, DRUM_NOTES["percussion_high"], VELOCITIES["soft"]),
        (quarter * 2, DRUM_NOTES["percussion_low"], VELOCITIES["accent"]),
        (quarter * 2 + eighth, DRUM_NOTES["percussion_high"], VELOCITIES["normal"]),
        (quarter * 3, DRUM_NOTES["percussion_mid"], VELOCITIES["normal"]),
        (quarter * 3 + eighth, DRUM_NOTES["percussion_high"], VELOCITIES["soft"]),
    ]
    for pos, note, vel in conga_positions:
        pattern.append((pos, note, vel, note_duration))
    
    # Shaker/Maracas on every eighth note
    for i in range(8):
        velocity = VELOCITIES["normal"] if i % 2 == 0 else VELOCITIES["soft"]
        pattern.append((i * eighth, DRUM_NOTES["shaker"], velocity, note_duration))
    
    # Cowbell accents
    cowbell_positions = [quarter, quarter * 3]
    for pos in cowbell_positions:
        pattern.append((pos, DRUM_NOTES["cowbell"], VELOCITIES["normal"], note_duration))
    
    # Basic kick and snare for foundation
    kick_positions = [0, quarter * 2 + eighth]
    snare_positions = [quarter, quarter * 3]
    
    for pos in kick_positions:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["normal"], note_duration))
    
    for pos in snare_positions:
        pattern.append((pos, DRUM_NOTES["snare"], VELOCITIES["normal"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_pop_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a contemporary pop drum pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # Standard kick pattern for pop
    kick_positions = [0, quarter + eighth, quarter * 2 + eighth, quarter * 3 + (eighth if random.random() > 0.5 else 0)]
    for pos in kick_positions:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Snare on beats 2 and 4
    pattern.append((quarter, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    
    # Clap layered with snare (common in pop)
    pattern.append((quarter, DRUM_NOTES["clap"], VELOCITIES["normal"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["clap"], VELOCITIES["normal"], note_duration))
    
    # Hi-hat pattern (usually eighth notes with occasional sixteenth notes)
    for i in range(8):
        velocity = VELOCITIES["normal"] if i % 2 == 0 else VELOCITIES["soft"]
        pattern.append((i * eighth, DRUM_NOTES["closed_hihat"], velocity, note_duration))
    
    # Add some sixteenth note hi-hat variations in the second half
    if random.random() > 0.5:  # 50% chance for variation
        for i in range(8, 16):
            if random.random() > 0.7:  # 30% chance per position
                pattern.append((i * sixteenth, DRUM_NOTES["closed_hihat"], VELOCITIES["soft"], note_duration))
    
    # Tambourine on offbeats (common in pop)
    for i in range(4):
        pattern.append((i * quarter + eighth, DRUM_NOTES["tambourine"], VELOCITIES["soft"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_rock_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a rock drum pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # Standard rock kick pattern
    kick_positions = [0, quarter * 2, quarter * 2 + eighth + sixteenth, quarter * 3 + eighth]
    for pos in kick_positions:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Snare on beats 2 and 4
    pattern.append((quarter, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    
    # Ride cymbal or hi-hat pattern (usually eighth notes)
    cymbal = DRUM_NOTES["closed_hihat"] if random.random() > 0.5 else DRUM_NOTES["ride"]
    for i in range(8):
        # Accent on the beats
        velocity = VELOCITIES["accent"] if i % 2 == 0 else VELOCITIES["normal"]
        pattern.append((i * eighth, cymbal, velocity, note_duration))
    
    # Add occasional crash cymbal
    if random.random() > 0.7:  # 30% chance
        crash_pos = quarter * 2 if random.random() > 0.5 else 0
        pattern.append((crash_pos, DRUM_NOTES["crash"], VELOCITIES["accent"], note_duration))
    
    # Add tom fills at the end of the bar
    if random.random() > 0.7:  # 30% chance for a fill
        toms = [DRUM_NOTES["tom_high"], DRUM_NOTES["tom_mid"], DRUM_NOTES["tom_low"]]
        start_pos = quarter * 3 + eighth
        for i in range(3):
            tom = toms[i % len(toms)]
            pos = start_pos + (i * sixteenth)
            pattern.append((pos, tom, VELOCITIES["accent"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_jazz_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a jazz swing pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    triplet = quarter // 3  # Triplet feel is characteristic of swing
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # Ride cymbal pattern with swing feel
    for beat in range(4):
        # Beat
        pattern.append((beat * quarter, DRUM_NOTES["ride"], VELOCITIES["accent"], note_duration))
        # And (swung)
        pattern.append((beat * quarter + triplet * 2, DRUM_NOTES["ride"], VELOCITIES["normal"], note_duration))
    
    # Add occasional ride bell
    if random.random() > 0.7:
        bell_positions = [quarter, quarter * 3]
        for pos in bell_positions:
            if random.random() > 0.5:
                pattern.append((pos, DRUM_NOTES["ride_bell"], VELOCITIES["accent"], note_duration))
    
    # Hi-hat with foot on beats 2 and 4 (characteristic of jazz)
    pattern.append((quarter, DRUM_NOTES["pedal_hihat"], VELOCITIES["normal"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["pedal_hihat"], VELOCITIES["normal"], note_duration))
    
    # Kick drum sparse and often syncopated in jazz
    kick_positions = []
    if random.random() > 0.5:
        kick_positions.append(0)  # Sometimes on beat 1
    if random.random() > 0.7:
        kick_positions.append(quarter * 2 + triplet)  # Sometimes on a syncopated beat
    
    for pos in kick_positions:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["normal"], note_duration))
    
    # Snare comping - varied and improvisational
    # In real jazz, this would be more varied, but we'll use some common patterns
    snare_options = [
        [quarter + triplet, quarter * 3 + triplet],
        [quarter * 2, quarter * 3 + triplet * 2],
        [quarter + triplet * 2, quarter * 2 + triplet, quarter * 3 + triplet * 2]
    ]
    
    snare_pattern = random.choice(snare_options)
    for pos in snare_pattern:
        # Vary the velocity for more natural comping
        vel = random.choice([VELOCITIES["ghost"], VELOCITIES["normal"], VELOCITIES["accent"]])
        pattern.append((pos, DRUM_NOTES["snare"], vel, note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_electronic_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create an electronic/EDM pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 30  # Shorter for electronic music
    
    pattern = []
    
    # Four-on-the-floor kick pattern (standard in EDM)
    for beat in range(4):
        pattern.append((beat * quarter, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Clap or snare on beats 2 and 4
    percussion = DRUM_NOTES["clap"] if random.random() > 0.5 else DRUM_NOTES["snare"]
    pattern.append((quarter, percussion, VELOCITIES["normal"], note_duration))
    pattern.append((quarter * 3, percussion, VELOCITIES["normal"], note_duration))
    
    # Hi-hat pattern - either steady sixteenths or eighth notes
    if random.random() > 0.5:
        # Sixteenth notes
        for i in range(16):
            velocity = VELOCITIES["accent"] if i % 4 == 0 else VELOCITIES["soft"]
            pattern.append((i * sixteenth, DRUM_NOTES["closed_hihat"], velocity, note_duration))
    else:
        # Eighth notes, alternating closed and open
        for i in range(8):
            hat_type = DRUM_NOTES["closed_hihat"] if i % 2 == 0 else DRUM_NOTES["open_hihat"]
            pattern.append((i * eighth, hat_type, VELOCITIES["normal"], note_duration))
    
    # Add occasional electronic effects (using tom sounds as substitutes)
    if random.random() > 0.5:
        effect_positions = [
            (quarter + eighth + sixteenth, DRUM_NOTES["tom_high"]),
            (quarter * 3 + eighth, DRUM_NOTES["tom_mid"])
        ]
        for pos, note in effect_positions:
            if random.random() > 0.5:
                pattern.append((pos, note, VELOCITIES["soft"], note_duration))
    
    # Rhythmic variation in the last beat
    if random.random() > 0.7:
        for i in range(3):
            pos = quarter * 3 + (i + 1) * sixteenth
            pattern.append((pos, DRUM_NOTES["kick_alt"], VELOCITIES["normal"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_hip_hop_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create a hip-hop beat pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # Hip-hop often uses syncopated kick patterns
    kick_options = [
        [0, quarter + eighth, quarter * 2, quarter * 3 + eighth],  # Classic boom-bap
        [0, quarter * 2, quarter * 2 + eighth + sixteenth, quarter * 3 + eighth],  # Syncopated
        [0, quarter + eighth, quarter * 2 + eighth, quarter * 3 + eighth]  # All offbeats except first
    ]
    kick_pattern = random.choice(kick_options)
    
    for pos in kick_pattern:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["accent"], note_duration))
    
    # Snare on beats 2 and 4 (classic hip-hop)
    pattern.append((quarter, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["snare"], VELOCITIES["accent"], note_duration))
    
    # Layered clap is common
    pattern.append((quarter, DRUM_NOTES["clap"], VELOCITIES["normal"], note_duration))
    pattern.append((quarter * 3, DRUM_NOTES["clap"], VELOCITIES["normal"], note_duration))
    
    # Hi-hat pattern - often eighth notes with some variations
    hat_positions = [i * eighth for i in range(8)]
    for pos in hat_positions:
        # Vary the velocities to create a groove
        vel = VELOCITIES["normal"] if pos % quarter == 0 else VELOCITIES["soft"]
        pattern.append((pos, DRUM_NOTES["closed_hihat"], vel, note_duration))
    
    # Add some ghost notes for realism
    ghost_positions = [quarter + sixteenth, quarter * 3 + sixteenth]
    for pos in ghost_positions:
        if random.random() > 0.7:  # 30% chance
            pattern.append((pos, DRUM_NOTES["snare"], VELOCITIES["ghost"], note_duration))
    
    # Occasionally add percussive elements
    perc_options = [DRUM_NOTES["tambourine"], DRUM_NOTES["cowbell"], DRUM_NOTES["clave"]]
    perc_element = random.choice(perc_options)
    perc_positions = [quarter + eighth, quarter * 3 + eighth]
    
    for pos in perc_positions:
        if random.random() > 0.6:  # 40% chance
            pattern.append((pos, perc_element, VELOCITIES["soft"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])

def _create_rnb_pattern(ticks_per_bar: int) -> List[Tuple[int, int, int, int]]:
    """Create an R&B groove pattern
    
    Returns a list of (tick, note, velocity, duration) tuples
    """
    # Define time values (in ticks)
    quarter = TICKS_PER_BEAT
    eighth = quarter // 2
    sixteenth = quarter // 4
    note_duration = 40  # Short duration for percussion sounds
    
    pattern = []
    
    # R&B kick patterns - often with more subtle syncopation
    kick_pattern = [0, quarter * 2]
    # Add some variations
    if random.random() > 0.5:
        kick_pattern.append(quarter + eighth)
    if random.random() > 0.5:
        kick_pattern.append(quarter * 3 + eighth)
    
    for pos in kick_pattern:
        pattern.append((pos, DRUM_NOTES["kick"], VELOCITIES["normal"], note_duration))
    
    # Snare on beats 2 and 4 with rimshots for variation
    if random.random() > 0.5:
        pattern.append((quarter, DRUM_NOTES["snare"], VELOCITIES["normal"], note_duration))
    else:
        pattern.append((quarter, DRUM_NOTES["snare_rim"], VELOCITIES["normal"], note_duration))
        
    if random.random() > 0.5:
        pattern.append((quarter * 3, DRUM_NOTES["snare"], VELOCITIES["normal"], note_duration))
    else:
        pattern.append((quarter * 3, DRUM_NOTES["snare_rim"], VELOCITIES["normal"], note_duration))
    
    # R&B often uses sixteenth note hi-hat patterns
    for i in range(16):
        # Create a groove by accenting certain positions
        velocity = VELOCITIES["normal"]
        if i % 4 == 0:  # Accent on the beat
            velocity = VELOCITIES["accent"]
        elif i % 2 == 0:  # Medium accent on the eighths
            velocity = VELOCITIES["normal"]
        else:  # Soft on the offbeats
            velocity = VELOCITIES["soft"]
            
        hat_type = DRUM_NOTES["closed_hihat"]
        # Occasionally open hi-hat for variation
        if (i == 7 or i == 15) and random.random() > 0.5:
            hat_type = DRUM_NOTES["open_hihat"]
            
        pattern.append((i * sixteenth, hat_type, velocity, note_duration))
    
    # Add ghost notes for snare (common in R&B)
    ghost_positions = [sixteenth, quarter + sixteenth, quarter * 2 + sixteenth, quarter * 3 + sixteenth]
    for pos in ghost_positions:
        if random.random() > 0.6:  # 40% chance
            pattern.append((pos, DRUM_NOTES["snare"], VELOCITIES["ghost"], note_duration))
    
    # Add rim clicks or percussion elements
    if random.random() > 0.5:
        for i in range(2):
            pos = (i * 2 + 1) * quarter + eighth  # Offbeats of 2 and 4
            pattern.append((pos, DRUM_NOTES["snare_rim"], VELOCITIES["soft"], note_duration))
    
    # Sort by tick position
    return sorted(pattern, key=lambda x: x[0])