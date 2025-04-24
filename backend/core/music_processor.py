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
        """Parse a note info dict into a music21 note object"""
        try:
            # Expected format: {'pitch': 'C4', 'duration': 1.0, 'syllable': 'ly'}
            pitch = note_info.get('pitch', 'C4')
            duration = note_info.get('duration', 1.0)
            
            note = music21.note.Note(pitch)
            note.duration = music21.duration.Duration(duration)
            return note
        except Exception as e:
            logger.error(f"Error parsing note {note_info}: {str(e)}")
            # Fallback to a quarter note C
            return music21.note.Note('C4', type='quarter')
    
    @staticmethod
    def generate_midi_file(chords, melody, title="Song", tempo=DEFAULT_TEMPO):
        """Generate a MIDI file with piano, drums, strings, and lyrics annotation"""
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
            for section, chord_list in chords.items():
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
                    # Convert to music21 note
                    m21_note = MusicProcessor.parse_melody_note(note_info)
                    
                    # Get the syllable for this note
                    syllable = note_info.get('syllable', '')
                    
                    # Convert to MIDI note number
                    midi_note = m21_note.pitch.midi
                    
                    # Calculate duration in ticks (assuming 480 ticks per quarter note)
                    duration_ticks = int(TICKS_PER_BEAT * m21_note.duration.quarterLength)
                    
                    # Add note_on
                    melody_track.append(Message('note_on', note=midi_note, velocity=80, time=time))
                    time = 0
                    
                    # Add lyrics if there's a syllable
                    if syllable:
                        melody_track.append(mido.MetaMessage('lyrics', text=syllable, time=0))
                    
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
            for section, chord_list in chords.items():
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
            
            # Add drums track using the add_drums helper method
            drum_track = MusicProcessor.create_drum_track(tempo, 8)  # Create 8 bars of drums
            mid.tracks.append(drum_track)
            
            # Create a song directory structure
            if not os.path.exists(SONGS_DIR):
                os.makedirs(SONGS_DIR)
            
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
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
                "title": title,
                "tempo": tempo,
                "creation_date": datetime.now().isoformat(),
                "chords": chords,
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

    @staticmethod
    def create_drum_track(tempo=DEFAULT_TEMPO, bars=8):
        """Create a drum track with the specified number of bars"""
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