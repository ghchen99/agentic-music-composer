// src/types/song.ts
export interface SongRequest {
  title: string;
  description: string;
  inspirations: string[];
  tempo?: number;
  drum_style?: string;
}

export interface ChordProgressionRequest {
  description: string;
  inspirations: string[];
  context?: string;
}

export interface LyricsRequest {
  description: string;
  inspirations: string[];
  chords: any; // Define more specific type if needed
  context?: string;
}

export interface MelodyRequest {
  description: string;
  inspirations: string[];
  chords: any; // Define more specific type if needed
  lyrics: any; // Define more specific type if needed
  context?: string;
}

export interface DrumPatternRequest {
  tempo: number;
  style: string;
  bars: number;
  context?: string;
}

export interface Response {
  result: any;
  source: string;
  timestamp: string;
}

export interface SongDetails {
  title: string;
  description: string;
  inspirations: string[];
  tempo: number;
  drum_style?: string;
  chords?: {
    verse: string[];
    chorus: string[];
  };
  lyrics?: {
    verse: string;
    chorus: string;
  };
  melody?: any;
  melody_summary?: {
    verse_notes: number;
    chorus_notes: number;
  };
  drums?: any;
  created_at: string;
  midi_url?: string;
  midi_file?: string;
}

export interface Song {
  title: string;
  description: string;
  created_at: string;
}