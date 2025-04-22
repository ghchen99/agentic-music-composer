# Music Composition Agentic System

## Overview

The Music Composition Agentic System is a specialized backend that leverages AI agents to create original musical compositions. Each agent specializes in a different aspect of music creation, working together in a coordinated environment to produce complete compositions that can be exported as both MIDI files and sheet music.

## Architecture

### Agent Environment

The system's environment is built on two primary music processing libraries:

1. **music21**: A Python toolkit for computer-aided musicology that provides an object-oriented representation of musical elements like notes, chords, measures, and time signatures.

2. **mido**: A library for working with MIDI messages and files, allowing for the creation and manipulation of MIDI data.

These libraries define the "world" in which the agents operate, providing them with the tools to create and manipulate musical elements programmatically.

### Agent Specializations

The system employs specialized agents that focus on specific aspects of music composition:

1. **ChordSpecialist Agent**:
   - Generates chord progressions based on style, key, and length parameters
   - Works with harmony principles specific to different musical styles
   - Creates progressions as sequences of chords with MIDI note numbers and durations

2. **MelodySpecialist Agent**:
   - Creates melodies that fit over chord progressions
   - Ensures melodies are appropriate for the selected style and key
   - Outputs sequences of notes with pitch, duration, and velocity information

3. **DrumSpecialist Agent**:
   - Generates rhythm patterns based on style and time signature
   - Creates appropriate drum patterns for various musical genres
   - Outputs drum hits with instrument ID, velocity, and position information

4. **CompositionAssembler Agent**:
   - Integrates the outputs from all specialist agents
   - Ensures musical coherence between components
   - Prepares the final composition data for export

### How Agents Work Together

1. The process begins with a composition request specifying style, key, tempo, and other parameters.
2. Each specialist agent is invoked in sequence:
   - ChordSpecialist generates the harmonic foundation
   - MelodySpecialist creates a melody that aligns with the chord progression
   - DrumSpecialist adds rhythmic elements appropriate for the style
3. The CompositionAssembler combines these elements into a coherent composition
4. The music is exported as both MIDI and MusicXML formats using the environment libraries

The agents utilize an Azure OpenAI language model to generate musical content based on their specialized knowledge, then format this content into structured musical data that can be processed by the music21 and mido libraries.

## Technical Implementation

### Built With

- **FastAPI**: Web framework for the API endpoints
- **AutoGen**: Framework for building and orchestrating LLM-powered agents
- **Azure OpenAI**: Language models for the agents' decision-making
- **music21**: Music notation and theory processing
- **mido**: MIDI file creation and manipulation
- **Python 3.8+**: Core programming language

### Core Components

- **Music Processor**: Handles the conversion between composition data and actual music files
- **Agent System**: Manages the specialist agents and their interactions
- **API Layer**: Exposes endpoints for composition requests and file retrieval

## API Usage

### Composition Request

**Endpoint**: `POST /api/compose`

**Input Format**:
```json
{
  "parameters": {
    "style": "jazz",         // Musical style
    "key": "C minor",        // Musical key
    "tempo": 110,            // BPM
    "length": 16,            // Number of measures
    "time_signature": "4/4", // Time signature
    "additional_notes": "Create a cool jazz progression with extended chords"
  }
}
```

**Output Format**:
```json
{
  "result": {
    "composition_id": "comp_20250422123456",
    "title": "Jazz Composition in C minor",
    "style": "jazz",
    "key": "C minor",
    "tempo": 110,
    "time_signature": "4/4",
    "length": 16,
    "midi_file": "compositions/comp_20250422123456.mid",
    "sheet_music_file": "compositions/comp_20250422123456.musicxml",
    "composition_data": {
      // Detailed composition structure
    }
  },
  "source": "music_composition_system",
  "timestamp": "2025-04-22T12:34:56.789012"
}
```

### Retrieving Files

**MIDI File**: `GET /api/composition/{composition_id}/midi`
**Sheet Music**: `GET /api/composition/{composition_id}/sheet`

## Installation and Setup

1. Clone the repository
```bash
git clone https://github.com/your-org/music-composition-agents.git
cd music-composition-agents
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file:
```
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
MODEL_NAME=your_model_name
API_VERSION=your_api_version
```

4. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Example Usage

### Python Example
```python
import requests
import json

url = "http://localhost:8000/api/compose"
headers = {"Content-Type": "application/json"}

payload = {
  "parameters": {
    "style": "classical",
    "key": "F major",
    "tempo": 170,
    "length": 32,
    "time_signature": "3/4",
    "additional_notes": "Viennese waltz style with light, elegant feel"
  }
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json())

# Get the composition ID from the response
composition_id = response.json()["result"]["composition_id"]

# Download MIDI file
midi_response = requests.get(f"http://localhost:8000/api/composition/{composition_id}/midi")
with open(f"{composition_id}.mid", "wb") as f:
    f.write(midi_response.content)

# Download Sheet Music
sheet_response = requests.get(f"http://localhost:8000/api/composition/{composition_id}/sheet")
with open(f"{composition_id}.musicxml", "wb") as f:
    f.write(sheet_response.content)
```

## Limitations and Future Work

- The current system focuses on basic musical elements; future versions could add additional specialists for basslines, countermelodies, and arrangements
- Style-specific knowledge could be expanded for more authentic genre representations
- Integration with audio synthesis for direct playback could enhance the user experience

## License

This project is licensed under the MIT License - see the LICENSE file for details.
