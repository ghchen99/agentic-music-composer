# Music Composition System

An AI-powered music composition backend that uses agent-based architecture to create musical pieces based on user parameters.

## Overview

This system provides an API for generating music compositions with specialized agents handling different aspects of music creation. The backend leverages language models to create chord progressions, melodies, and drum patterns, then assembles them into complete compositions that can be exported as MIDI files and sheet music.

## Features

- **AI-Driven Composition**: Generate complete musical compositions based on style, key, tempo, and other parameters
- **Specialized Music Agents**:
  - **Chord Specialist**: Generates appropriate chord progressions for the requested style and key
  - **Melody Specialist**: Creates melodies that complement the chord progression
  - **Drum Specialist**: Programs rhythm patterns fitting the style and time signature
  - **Composition Assembler**: Combines all musical elements into a cohesive piece
- **Multiple Output Formats**:
  - MIDI files for playback in any DAW or sequencer
  - MusicXML for sheet music and notation
- **Music Theory Knowledge Base**: Access information about chord progressions, scales, and style characteristics
- **User Preferences**: Store and retrieve user composition history and preferences

## Technical Stack

- **Framework**: FastAPI
- **AI**: Azure OpenAI for language model capabilities
- **Agent Framework**: AutoGen for the intelligent agent system
- **Music Libraries**:
  - `mido` for MIDI file creation and manipulation
  - `music21` for music theory and sheet music generation
- **Environment**: Python 3.8+

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/music-composition-system.git
   cd music-composition-system
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Azure OpenAI credentials:
   ```
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   API_VERSION=your_api_version
   MODEL_NAME=your_model_name
   ```

## Usage

1. Start the server:
   ```
   uvicorn main:app --reload
   ```

2. The API will be available at `http://localhost:8000`

3. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Composition

- `POST /api/compose`: Generate a new music composition
  ```json
  {
    "parameters": {
      "style": "jazz",
      "key": "C minor",
      "tempo": 120,
      "length": 16,
      "time_signature": "4/4",
      "additional_notes": "Include a ii-V-I progression"
    }
  }
  ```

### Music Theory

- `POST /api/theory`: Query music theory information
  ```json
  {
    "query": "What are common chord progressions in jazz?",
    "style": "jazz",
    "key": "C major"
  }
  ```

### User Data

- `POST /api/user-data`: Retrieve user preferences and history
  ```json
  {
    "user_id": "user123",
    "query_type": "history"
  }
  ```

### Composition Files

- `GET /api/composition/{composition_id}/midi`: Download the MIDI file for a composition
- `GET /api/composition/{composition_id}/sheet`: Download the sheet music for a composition

## Example Workflow

1. Request a new composition with specific parameters
2. The system generates chord progressions appropriate for the style
3. Melodies are created to fit the chord progression
4. Drum patterns are generated to match the style and time signature
5. All components are assembled into a complete composition
6. MIDI and sheet music files are created and made available for download

## Extending The System

### Adding New Musical Styles

To add support for a new musical style:

1. Update the `MusicLibrary` class with style characteristics, chord progressions, and patterns
2. Add style-specific generation logic to the agent functions

### Adding New Output Formats

To support additional output formats:

1. Add new methods to the `MusicProcessor` class
2. Create new endpoint(s) for the format

## Troubleshooting

- **MIDI File Issues**: Check that the composition data structure conforms to the expected format
- **API Connection Errors**: Verify Azure OpenAI credentials and network connectivity
- **Agent Errors**: Review logs for specific error messages from the composition agents

## License

[MIT License](LICENSE)

## Acknowledgements

- [AutoGen](https://github.com/microsoft/autogen) for the agent framework
- [Music21](https://web.mit.edu/music21/) for music theory and notation capabilities
- [Mido](https://mido.readthedocs.io/) for MIDI file manipulation
