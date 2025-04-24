# AI Music Composition Assistant 🎵

A powerful backend system for generating original music using AI agents. This system uses Azure OpenAI and AutoGen to create chord progressions, lyrics, melodies, and drum patterns, combining them into complete MIDI songs.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of songwriting
- **Complete Song Generation**: Creates chord progressions, lyrics, melodies and drum patterns
- **Multiple Drum Styles**: Support for various musical styles (basic, four_on_floor, trap, latin, pop, etc.)
- **MIDI File Output**: Generates professional-quality MIDI files with multiple instrument tracks
- **RESTful API**: Easy integration with front-end applications

## 📋 System Components

```
backend/
├── agents/               # Specialized AI agents
│   ├── agent_system.py   # Main agent orchestration
│   ├── chord_agent.py    # Chord progression generation
│   ├── drum_agent.py     # Drum pattern generation
│   ├── lyrics_agent.py   # Song lyrics generation
│   └── melody_agent.py   # Melody creation
├── config/               # Configuration settings
├── core/                 # Core functionality
│   ├── azure_client.py   # Azure OpenAI integration
│   └── music_processor.py # MIDI and music generation
├── models/               # Data models
├── services/             # Business logic services
├── utils/                # Utility functions
│   ├── midi_utils.py     # MIDI manipulation utilities
│   └── music_theory.py   # Music theory helpers
├── main.py               # FastAPI application
└── requirements.txt      # Dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Azure OpenAI API key and endpoint
- Dependencies from requirements.txt

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-songwriting-assistant.git
   cd ai-songwriting-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following:
   ```
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   API_VERSION=your_api_version
   MODEL_NAME=your_model_name
   ```

### Running the API

Start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```

The API will be available at http://localhost:8000

## 🎹 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/create-song` | POST | Create a complete song |
| `/api/generate-chords` | POST | Generate chord progressions |
| `/api/generate-lyrics` | POST | Generate song lyrics |
| `/api/generate-melody` | POST | Generate melody based on lyrics and chords |
| `/api/generate-drums` | POST | Generate drum patterns |
| `/api/songs` | GET | List all generated songs |
| `/api/songs/{song_title}` | GET | Get song details |
| `/api/download/{song_title}` | GET | Download MIDI file |
| `/health` | GET | API health check |

## 📝 Example Usage

### Create a complete song

```python
import requests
import json

url = "http://localhost:8000/api/create-song"
payload = {
    "description": "An uplifting pop song about perseverance and growth",
    "inspirations": ["Coldplay", "OneRepublic", "Imagine Dragons"],
    "title": "Rising Higher",
    "tempo": 120
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

## 🥁 Available Drum Styles

- `basic`: Standard rock/pop pattern
- `four_on_floor`: Classic disco/house with kick on every beat
- `trap`: Modern trap beats with rolling hi-hats
- `latin`: Latin percussion patterns
- `pop`: Contemporary pop patterns
- `rock`: Rock drumming patterns
- `jazz`: Jazz swing patterns
- `electronic`: Electronic/EDM patterns
- `hip_hop`: Hip-hop beats
- `r_and_b`: R&B groove patterns

## 🧩 Architecture

This system uses a multi-agent approach where specialized agents handle different aspects of the songwriting process:

1. **RouterAgent**: Determines which specialist should handle user queries
2. **ChordProgressionAgent**: Generates chord progressions for verse and chorus
3. **LyricsAgent**: Creates lyrics based on song theme and chord progressions
4. **MelodyAgent**: Composes melodies that fit the lyrics and chords
5. **DrumAgent**: Creates appropriate drum patterns for the song

The agents collaborate to create a complete song, which is then processed into a MIDI file with multiple tracks:
- Piano (chords)
- Melody (with lyrics annotations)
- Strings (pad)
- Drums

## 📥 Output Format

The system generates:

1. A MIDI file with multiple tracks
2. A JSON file with song metadata

Example output directory structure:
```
songs/
└── Rising_Higher/
    ├── Rising_Higher.mid
    └── song_info.json
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Azure OpenAI for the language model capabilities
- AutoGen for the agent framework
- music21 and mido for music theory and MIDI processing
