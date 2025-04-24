"""
Song creation and management service
"""

import os
import json
import logging
from typing import List, Dict, Optional
from fastapi import HTTPException

from models.schemas import SongDetails
from config.settings import SONGS_DIR

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SongService:
    @staticmethod
    def list_songs() -> List[Dict]:
        """List all generated songs"""
        try:
            if not os.path.exists(SONGS_DIR):
                return []
            
            songs = []
            for song_folder in os.listdir(SONGS_DIR):
                folder_path = os.path.join(SONGS_DIR, song_folder)
                if os.path.isdir(folder_path):
                    # Try to read song_info.json if it exists
                    info_path = os.path.join(folder_path, "song_info.json")
                    if os.path.exists(info_path):
                        try:
                            with open(info_path, 'r') as f:
                                song_info = json.load(f)
                                songs.append({
                                    "title": song_info.get("title", song_folder.replace('_', ' ')),
                                    "creation_date": song_info.get("creation_date", ""),
                                    "folder": song_folder
                                })
                        except:
                            # If JSON can't be read, just use the folder name
                            songs.append({
                                "title": song_folder.replace('_', ' '),
                                "folder": song_folder
                            })
                    else:
                        # No song_info.json, just use the folder name
                        songs.append({
                            "title": song_folder.replace('_', ' '),
                            "folder": song_folder
                        })
            
            return songs
        except Exception as e:
            logger.error(f"Error listing songs: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing songs: {str(e)}")

    @staticmethod
    def get_song_details(song_title: str) -> SongDetails:
        """Get details of a specific song"""
        try:
            safe_title = "".join([c for c in song_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            if not safe_title:
                safe_title = "song"
                
            song_dir = os.path.join(SONGS_DIR, safe_title.replace(' ', '_'))
            
            if not os.path.exists(song_dir):
                raise HTTPException(status_code=404, detail=f"Song '{song_title}' not found")
                
            # Read song_info.json if it exists
            info_path = os.path.join(song_dir, "song_info.json")
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    song_info = json.load(f)
                    # Add the path to the MIDI file
                    midi_file = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
                    return SongDetails(
                        title=song_info.get("title", song_title),
                        description=song_info.get("description", None),
                        inspirations=song_info.get("inspirations", None),
                        tempo=song_info.get("tempo", None),
                        chords=song_info.get("chords", None),
                        lyrics=song_info.get("lyrics", None),
                        melody_summary=song_info.get("melody_info", None),
                        midi_file=midi_file,
                        creation_date=song_info.get("creation_date", None)
                    )
            else:
                # Basic info if no JSON file
                midi_file = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
                return SongDetails(
                    title=song_title,
                    midi_file=midi_file
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting song details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting song details: {str(e)}")

    @staticmethod
    def get_midi_path(song_title: str) -> str:
        """Get the path to a song's MIDI file"""
        try:
            safe_title = "".join([c for c in song_title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            if not safe_title:
                safe_title = "song"
                
            # Path to the song's directory and MIDI file
            song_dir = os.path.join(SONGS_DIR, safe_title.replace(' ', '_'))
            midi_path = os.path.join(song_dir, f"{safe_title.replace(' ', '_')}.mid")
            
            if not os.path.exists(midi_path):
                raise HTTPException(status_code=404, detail=f"MIDI file for '{song_title}' not found")
            
            return midi_path
        except Exception as e:
            logger.error(f"Error getting MIDI path: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting MIDI path: {str(e)}")