"""
Configuration settings for the Songwriting Agentic Backend
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("API_VERSION")
MODEL_NAME = os.getenv("MODEL_NAME")

# Application settings
SONGS_DIR = os.path.join(os.getcwd(), "songs")

# MIDI settings
DEFAULT_TEMPO = 120
TICKS_PER_BEAT = 480