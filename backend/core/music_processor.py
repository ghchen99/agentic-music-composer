"""
Music processor for MIDI generation and music theory operations
"""

import os
import json
import logging
from datetime import datetime
from fastapi import HTTPException

import music21
import mido
from mido import Message, MidiFile, MidiTrack

from config.settings import SONGS_DIR, TICKS_PER_BEAT, DEFAULT_TEMPO
from utils.midi_utils import create_drum_pattern  # Import the shared implementation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MusicProcessor:
    @staticmethod
    def parse_chord(chord_name):
        """Parse a chord name into a music21 chord object"""
        try:
            return music21.harmony.ChordSymbol(chord_name)
        except Exception as e:
            logger.error(f"Error parsing chord {chord_name}: {str(e)}")
            # Fallback to a simple C major chord
            return music21.chord.Chord(['C4', 'E4', 'G4'])
    
    @staticmethod
    def parse_melody_note(note_info):
        """Parse a note info dict into a music21 note or rest object"""
        try:
            # Expected format: {'pitch': 'C4', 'duration': 1.0, 'syllable': 'ly'}
            pitch = note_info.get('pitch', 'C4')
            duration = note_info.get('duration', 1.0)
            
            # Check if it's a rest
            if pitch.lower() == 'rest':
                # Create a rest with the specified duration
                note = music21.note.Rest()
                note.duration = music21.duration.Duration(duration)
                return note
            else:
                # Create a regular note
                note = music21.note.Note(pitch)
                note.duration = music21.duration.Duration(duration)
                return note
        except Exception as e:
            logger.error(f"Error parsing note {note_info}: {str(e)}")
            # Fallback to a quarter note C
            return music21.note.Note('C4', type='quarter')

    @staticmethod
    def generate_midi_file(chords, melody, title="Song", tempo=DEFAULT_TEMPO, drum_style="basic"):
        """Generate a MIDI file with piano, drums, strings, and lyrics annotation
        
        Args:
            chords: Dictionary with verse and chorus chord progressions
            melody: Dictionary with verse and chorus melodies
            title: Title of the song
            tempo: Tempo in BPM
            drum_style: Style of drum pattern to use
            
        Returns:
            Path to the generated MIDI file
        """
        try:
            # Create a MIDI file with tracks: tempo/time sig, piano (chords), melody, strings, drums
            mid = MidiFile(type=1)
            
            # Track 0: Tempo and time signature
            track0 = MidiTrack()
            mid.tracks.append(track0)
            
            # Add tempo
            tempo_microseconds = mido.bpm2tempo(tempo)
            track0.append(mido.MetaMessage('set_tempo', tempo=tempo_microseconds, time=0))
            
            # Add time signature (4/4)
            track0.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
            
            # Track 1: Piano (chords)
            piano_track = MidiTrack()
            mid.tracks.append(piano_track)
            piano_track.append(mido.MetaMessage('track_name', name='Piano', time=0))
            piano_track.append(Message('program_change', program=0, time=0))  # Piano
            
            # Add chords - one chord per bar (1920 ticks)
            ticks_per_bar = TICKS_PER_BEAT * 4  # 4 beats per bar in 4/4 time
            
            time = 0
            # Create a 16-bar pattern with verse and chorus sections
            for section, chord_list in chords.items():
                # Play each section twice (8 bars total for each section)
                for repetition in range(2):
                    for chord_name in chord_list:
                        # Convert chord to music21 object
                        chord = MusicProcessor.parse_chord(chord_name)
                        
                        # Add each note in the chord
                        for note in chord.pitches:
                            # Convert to MIDI note number
                            midi_note = note.midi
                            piano_track.append(Message('note_on', note=midi_note, velocity=64, time=time))
                            time = 0  # Reset time for subsequent notes in chord
                        
                        # Set time for note_off - full bar
                        time = ticks_per_bar
                        
                        # Add note_off messages
                        for note in chord.pitches:
                            midi_note = note.midi
                            piano_track.append(Message('note_off', note=midi_note, velocity=64, time=time))
                            time = 0  # Reset time for subsequent notes
            
            # Track 2: Melody with lyrics
            melody_track = MidiTrack()
            mid.tracks.append(melody_track)
            melody_track.append(mido.MetaMessage('track_name', name='Melody', time=0))
            melody_track.append(Message('program_change', program=73, time=0))  # Flute
            
            # Add melody notes with lyrics annotation
            time = 0
            for section, notes in melody.items():
                for note_info in notes:
                    # Convert to music21 note or rest
                    m21_note = MusicProcessor.parse_melody_note(note_info)
                    
                    # Get the syllable for this note
                    syllable = note_info.get('syllable', '')
                    
                    # Calculate duration in ticks (assuming 480 ticks per quarter note)
                    duration_ticks = int(TICKS_PER_BEAT * m21_note.duration.quarterLength)
                    
                    # Handle rest versus note differently
                    if isinstance(m21_note, music21.note.Rest):
                        # For a rest, we just advance the time
                        time += duration_ticks
                    else:
                        # For a note, add note_on and note_off events
                        # Convert to MIDI note number
                        midi_note = m21_note.pitch.midi
                        
                        # Add note_on
                        melody_track.append(Message('note_on', note=midi_note, velocity=80, time=time))
                        time = 0
                        
                        # Add lyrics if there's a syllable - make sure it's ASCII-compatible
                        if syllable:
                            # Convert non-ASCII characters to ASCII approximations or remove them
                            ascii_syllable = syllable.encode('ascii', 'replace').decode('ascii')
                            melody_track.append(mido.MetaMessage('lyrics', text=ascii_syllable, time=0))
                        
                        # Add note_off
                        melody_track.append(Message('note_off', note=midi_note, velocity=0, time=duration_ticks))
                        time = 0
            
            # Track 3: Strings (pad)
            strings_track = MidiTrack()
            mid.tracks.append(strings_track)
            strings_track.append(mido.MetaMessage('track_name', name='Strings', time=0))
            strings_track.append(Message('program_change', program=48, time=0))  # String Ensemble
            
            # Add basic string pad following the chord progression
            time = 0
            # Update strings track to use the same 16-bar pattern
            for section, chord_list in chords.items():
                # Play each section twice (8 bars total for each section)
                for repetition in range(2):
                    for chord_name in chord_list:
                        # Convert chord to music21 object
                        chord = MusicProcessor.parse_chord(chord_name)
                        
                        # Add root and fifth for a pad sound
                        notes_to_play = [chord.root().midi, chord.getChordStep(5).midi]
                        
                        # Add note_on messages
                        for midi_note in notes_to_play:
                            strings_track.append(Message('note_on', note=midi_note, velocity=50, time=time))
                            time = 0
                        
                        # Set time for note_off - full bar
                        time = ticks_per_bar
                        
                        # Add note_off messages
                        for midi_note in notes_to_play:
                            strings_track.append(Message('note_off', note=midi_note, velocity=0, time=time))
                            time = 0
            
            # Create drum track with the specified style - now 16 bars to match the complete pattern
            from utils.midi_utils import create_drum_pattern
            drum_track = create_drum_pattern(tempo, 16, drum_style)  # Create 16 bars of drums with the specified style
            mid.tracks.append(drum_track)
            
            # Create a song directory structure
            if not os.path.exists(SONGS_DIR):
                os.makedirs(SONGS_DIR)
            
            # Normalize title to ensure it's compatible with Latin-1 encoding (used by MIDI)
            normalized_title = title.encode('ascii', 'ignore').decode('ascii')
            safe_title = "".join([c for c in normalized_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            if not safe_title:
                safe_title = "song"
                
            song_dir = os.path.join(SONGS_DIR, safe_title.replace(' ', '_'))
            if not os.path.exists(song_dir):
                os.makedirs(song_dir)
            
            midi_path = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
            
            # Save the MIDI file
            mid.save(midi_path)
            
            # Also save a song info JSON file with metadata
            song_info = {
                "title": title,  # Keep the original title with special characters in JSON
                "tempo": tempo,
                "creation_date": datetime.now().isoformat(),
                "chords": chords,
                "drum_style": drum_style,
                "structure": "16-bar cycle (8-bar verse, 8-bar chorus)",
                "melody_info": {
                    "verse_notes": len(melody.get("verse", [])),
                    "chorus_notes": len(melody.get("chorus", []))
                }
            }
            
            with open(os.path.join(song_dir, "song_info.json"), "w") as f:
                json.dump(song_info, f, indent=2)
            
            return midi_path
        
        except Exception as e:
            logger.error(f"Error generating MIDI file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"MIDI generation error: {str(e)}")