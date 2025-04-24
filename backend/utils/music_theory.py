"""
Music theory helper functions
"""

def syllabify(text):
    """Simple syllable counter - splits text into approximate syllables"""
    if not text:
        return []
        
    # Remove punctuation except apostrophes
    import re
    text = re.sub(r'[^\w\s\']', '', text)
    
    # Split into words
    words = text.split()
    
    syllables = []
    for word in words:
        # Count vowel sequences as syllables
        vowels = "aeiouy"
        count = 0
        in_vowel_group = False
        
        for char in word.lower():
            if char in vowels:
                if not in_vowel_group:
                    count += 1
                    in_vowel_group = True
            else:
                in_vowel_group = False
        
        # Ensure at least one syllable per word
        if count == 0:
            count = 1
            
        # Add each syllable to the list
        for i in range(count):
            syllables.append(word if count == 1 else f"{word}_{i+1}")
    
    return syllables

def generate_default_melody(syllables, chords):
    """Generate a simple default melody based on syllables and chords"""
    if not syllables or not chords:
        return []
    
    # Basic pitches for each chord
    chord_pitches = {
        "C": ["C4", "E4", "G4"],
        "G": ["G4", "B4", "D4"],
        "Am": ["A4", "C4", "E4"],
        "F": ["F4", "A4", "C4"],
        "Dm": ["D4", "F4", "A4"],
        "Em": ["E4", "G4", "B4"],
        # Add more chords as needed
    }
    
    # Default to C major scale if chord not recognized
    default_pitches = ["C4", "D4", "E4", "F4", "G4", "A4", "B4"]
    
    melody = []
    chord_idx = 0
    beats_per_chord = 4  # 4 beats per chord in 4/4 time
    current_beat = 0
    
    for syllable in syllables:
        # Determine which chord we're currently on
        current_chord = chords[chord_idx % len(chords)]
        
        # Get available pitches for this chord
        available_pitches = chord_pitches.get(current_chord, default_pitches)
        
        # Choose a pitch based on position in the sequence
        pitch_idx = len(melody) % len(available_pitches)
        pitch = available_pitches[pitch_idx]
        
        # Default to quarter notes, with occasional eighth notes
        duration = 0.5 if len(melody) % 3 == 0 else 1.0
        
        # Add the note to the melody
        melody.append({
            "pitch": pitch,
            "duration": duration,
            "syllable": syllable
        })
        
        # Update beat counter
        current_beat += duration
        
        # Move to next chord if we've filled this one
        if current_beat >= beats_per_chord:
            chord_idx += 1
            current_beat = 0
    
    return melody