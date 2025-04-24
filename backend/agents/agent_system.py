"""
Songwriting Agent System using AutoGen
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from autogen import AssistantAgent, UserProxyAgent

from agents.chord_agent import generate_chord_progression
from agents.lyrics_agent import generate_lyrics
from agents.melody_agent import generate_melody
from agents.drum_agent import generate_drum_pattern
from core.music_processor import MusicProcessor
from models.schemas import Response
from config.settings import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, API_VERSION, MODEL_NAME

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SongwritingAgentSystem:
    def __init__(self):
        """Initialize the AutoGen-based songwriting agent system"""
        # Configure AutoGen for Azure OpenAI
        llm_config = {
            "config_list": [
                {
                    "model": MODEL_NAME,
                    "api_type": "azure",
                    "api_key": AZURE_OPENAI_API_KEY,
                    "base_url": AZURE_OPENAI_ENDPOINT,
                    "api_version": API_VERSION,
                }
            ],
            "temperature": 0.7  # Higher temperature for creative agents
        }
        
        # Register tool functions
        self.function_map = self._register_autogen_functions()
        
        # Create the router agent (LLM-based)
        self.router_agent = AssistantAgent(
            name="RouterAgent",
            system_message="""You are a songwriting assistant router. Your job is to determine which specialist to route 
            user queries to based on the content. You have four specialists available:
            1. ChordProgressionAgent - For generating chord progressions
            2. LyricsAgent - For generating lyrics
            3. MelodyAgent - For creating melodies
            4. DrumAgent - For creating drum patterns
            
            Determine which specialist should handle the query and route it appropriately.
            When responding, provide ONLY the name of the specialist in a JSON format: {"specialist": "SpecialistName"}
            """,
            llm_config={
                **llm_config,
                "functions": [
                    {
                        "name": "route_to_specialist",
                        "description": "Route the request to the appropriate specialist",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "specialist": {
                                    "type": "string",
                                    "description": "The specialist to route to",
                                    "enum": ["ChordProgressionAgent", "LyricsAgent", "MelodyAgent", "DrumAgent"]
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Reason for selecting this specialist"
                                }
                            },
                            "required": ["specialist"]
                        }
                    }
                ]
            }
        )
        
        # Create specialist agents with their tools
        self.chord_progression_agent = AssistantAgent(
            name="ChordProgressionAgent",
            system_message="""You are a music theory expert specializing in chord progressions. 
            You can generate chord progressions for verse and chorus based on song descriptions and musical inspirations.
            
            When responding, provide your output in structured JSON format:
            {"verse": ["C", "G", "Am", "F"], "chorus": ["F", "C", "G", "Am"]}
            """,
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_chords"]
                ]
            }
        )
        
        self.lyrics_agent = AssistantAgent(
            name="LyricsAgent",
            system_message="""You are a lyricist specializing in songwriting. 
            You can create lyrics for verse and chorus based on song descriptions, musical inspirations, and chord progressions.
            
            When responding, provide your output in structured JSON format:
            {"verse": "Verse lyrics line 1\\nVerse lyrics line 2\\nVerse lyrics line 3\\nVerse lyrics line 4", 
             "chorus": "Chorus lyrics line 1\\nChorus lyrics line 2\\nChorus lyrics line 3\\nChorus lyrics line 4"}
            """,
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_lyrics"]
                ]
            }
        )
        
        self.melody_agent = AssistantAgent(
            name="MelodyAgent",
            system_message="""You are a melody composer specializing in songwriting. 
            You can create melodies for lyrics based on chord progressions and lyrics.
            
            When responding, provide your output in structured JSON format with detailed note information.
            """,
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_melody"]
                ]
            }
        )

        self.drum_agent = AssistantAgent(
            name="DrumAgent",
            system_message="""You are a drum programming expert. 
            You can create drum patterns in various styles for songs.
            
            When responding, provide your output in a single-word format specifying just the drum style.
            """,
            llm_config={
                **llm_config,
                "functions": [
                    self.function_map["generate_drums"]
                ]
            }
        )
        
        # Create a human proxy agent to act as the interface
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",  # No actual human input needed
            code_execution_config=False  # Disable code execution
        )
        
        # Map specialists to their respective functions for direct execution
        self.specialist_function_map = {
            "ChordProgressionAgent": self.function_map["generate_chords"]["function"],
            "LyricsAgent": self.function_map["generate_lyrics"]["function"],
            "MelodyAgent": self.function_map["generate_melody"]["function"],
            "DrumAgent": self.function_map["generate_drums"]["function"]
        }

    def _register_autogen_functions(self):
        """Register functions as tools for AutoGen agents"""
        function_map = {
            "generate_chords": {
                "name": "generate_chords",
                "description": "Generate chord progressions for verse and chorus",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the song's theme and mood"
                        },
                        "inspirations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of musical artists that inspire this song"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for chord generation"
                        }
                    },
                    "required": ["description", "inspirations"]
                },
                "function": generate_chord_progression
            },
            "generate_lyrics": {
                "name": "generate_lyrics",
                "description": "Generate lyrics for verse and chorus",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the song's theme and mood"
                        },
                        "inspirations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of musical artists that inspire this song"
                        },
                        "chords": {
                            "type": "object",
                            "description": "Chord progressions for verse and chorus"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for lyrics generation"
                        }
                    },
                    "required": ["description", "inspirations", "chords"]
                },
                "function": generate_lyrics
            },
            "generate_melody": {
                "name": "generate_melody",
                "description": "Generate melody based on lyrics and chords",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the song's theme and mood"
                        },
                        "inspirations": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of musical artists that inspire this song"
                        },
                        "chords": {
                            "type": "object",
                            "description": "Chord progressions for verse and chorus"
                        },
                        "lyrics": {
                            "type": "object",
                            "description": "Lyrics for verse and chorus"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for melody generation"
                        }
                    },
                    "required": ["description", "inspirations", "chords", "lyrics"]
                },
                "function": generate_melody
            },
            "generate_drums": {
                "name": "generate_drums",
                "description": "Generate drum patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tempo": {
                            "type": "integer",
                            "description": "Tempo in BPM"
                        },
                        "style": {
                            "type": "string",
                            "description": "Drum style (e.g., 'basic', 'rock', 'jazz')"
                        },
                        "bars": {
                            "type": "integer",
                            "description": "Number of bars for the drum pattern"
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context for drum generation"
                        }
                    },
                    "required": ["tempo"]
                },
                "function": generate_drum_pattern
            }
        }
        
        return function_map

    async def create_song(self, description: str, inspirations: List[str], title: Optional[str] = None, 
                        tempo: int = 120, drum_style: Optional[str] = None) -> Response:
        """Create a complete song using the agent system
        
        Args:
            description: Description of the song's theme and mood
            inspirations: List of musical artists that inspire this song
            title: Optional title for the song (generated from description if not provided)
            tempo: Tempo in BPM
            drum_style: Optional drum style to use (e.g., "basic", "four_on_floor", "trap", "latin", "pop")
        
        Returns:
            Response object containing the generated song details or error information
        """
        try:
            # Step 1: Generate chord progressions
            logger.info("Generating chord progressions...")
            chord_result = generate_chord_progression(description, inspirations)
            
            if "error" in chord_result:
                return Response(
                    result=f"Error generating chord progressions: {chord_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            chords = chord_result["chords"]
            logger.info(f"Generated chords: {chords}")
            
            # Step 2: Generate lyrics
            logger.info("Generating lyrics...")
            lyrics_result = generate_lyrics(description, inspirations, chords)
            
            if "error" in lyrics_result:
                return Response(
                    result=f"Error generating lyrics: {lyrics_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            lyrics = lyrics_result["lyrics"]
            logger.info(f"Generated lyrics for verse and chorus")
            
            # Step 3: Generate melody
            logger.info("Generating melody...")
            melody_result = generate_melody(description, inspirations, chords, lyrics)
            
            if "error" in melody_result:
                return Response(
                    result=f"Error generating melody: {melody_result['error']}",
                    source="agent_error",
                    timestamp=datetime.now().isoformat()
                )
            
            melody = melody_result["melody"]
            logger.info(f"Generated melody for verse and chorus")
            
            # Step 4: Generate drum pattern
            logger.info(f"Generating drum pattern with style: {drum_style or 'auto-determined'}...")
            
            # If no drum style specified, determine it based on description and inspirations
            if not drum_style:
                # Use the context to help the drum agent determine the style
                context = {
                    "description": description,
                    "inspirations": inspirations
                }
            else:
                context = None
                
            drum_result = generate_drum_pattern(
                tempo=tempo, 
                style=drum_style, 
                bars=16,  # 16 bars for the full verse+chorus pattern
                context=context
            )
            
            if "error" in drum_result:
                logger.warning(f"Error generating drum pattern: {drum_result['error']}, continuing with basic pattern")
                drum_style = "basic"
            else:
                logger.info(f"Generated drum pattern with style: {drum_result.get('style', 'basic')}")
                drum_style = drum_result.get('style', 'basic')
            
            # Step 5: Generate MIDI file
            if not title:
                title = f"Song about {description[:20]}"
            
            logger.info(f"Generating MIDI file with title: {title}, tempo: {tempo}...")
            midi_path = MusicProcessor.generate_midi_file(chords, melody, title, tempo, drum_style)
            
            # Prepare result
            result = {
                "title": title,
                "description": description,
                "inspirations": inspirations,
                "tempo": tempo,
                "chords": chords,
                "lyrics": lyrics,
                "melody_summary": {
                    "verse_notes": len(melody["verse"]),
                    "chorus_notes": len(melody["chorus"])
                },
                "drum_style": drum_style,
                "midi_file": midi_path
            }
            
            return Response(
                result=result,
                source="songwriting_system",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in create_song: {str(e)}")
            return Response(
                result=f"Error creating song: {str(e)}",
                source="agent_error",
                timestamp=datetime.now().isoformat()
            )