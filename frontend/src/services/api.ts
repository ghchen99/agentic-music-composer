// src/services/api.ts
import { SongRequest, Response, SongDetails, Song } from '@/types/song';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const ApiService = {
  async createSong(songRequest: SongRequest): Promise<Response> {
    const response = await fetch(`${API_BASE_URL}/create-song`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(songRequest),
    });

    if (!response.ok) {
      throw new Error(`Error creating song: ${response.statusText}`);
    }

    return response.json();
  },

  async listSongs(): Promise<Song[]> {
    const response = await fetch(`${API_BASE_URL}/songs`);

    if (!response.ok) {
      throw new Error(`Error fetching songs: ${response.statusText}`);
    }

    const data = await response.json();
    return data.songs;
  },

  async getSongDetails(title: string): Promise<SongDetails> {
    const response = await fetch(`${API_BASE_URL}/songs/${encodeURIComponent(title)}`);

    if (!response.ok) {
      throw new Error(`Error fetching song details: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Handle response data based on its structure
    if (data.result) {
      // For API responses from create-song that have a result object containing song data
      const result = data.result;
      return {
        title: result.title,
        description: result.description,
        inspirations: result.inspirations || [],
        tempo: result.tempo || 120,
        drum_style: result.drum_style || 'basic',
        chords: result.chords || null,
        lyrics: result.lyrics || null,
        melody_summary: result.melody_summary || null,
        melody: result.melody || null,
        drums: result.drums || null,
        created_at: data.timestamp || new Date().toISOString(),
        midi_url: result.midi_file || `${API_BASE_URL}/download/${encodeURIComponent(title)}`
      };
    }
    
    // For directly structured responses
    return {
      title: data.title || title,
      description: data.description || '',
      inspirations: data.inspirations || [],
      tempo: data.tempo || 120,
      drum_style: data.drum_style || 'basic',
      chords: data.chords || null,
      lyrics: data.lyrics || null,
      melody_summary: data.melody_summary || null,
      melody: data.melody || null,
      drums: data.drums || null,
      created_at: data.created_at || new Date().toISOString(),
      midi_url: data.midi_file || data.midi_url || `${API_BASE_URL}/download/${encodeURIComponent(title)}`
    };
  },

  getMidiUrl(title: string): string {
    return `${API_BASE_URL}/download/${encodeURIComponent(title)}`;
  }
};