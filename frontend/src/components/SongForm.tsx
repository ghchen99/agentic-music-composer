// src/components/SongForm.tsx
"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ApiService } from '@/services/api';
import { SongRequest } from '@/types/song';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

export function SongForm() {
  const router = useRouter();
  const [songData, setSongData] = useState<SongRequest>({
    title: '',
    description: '',
    inspirations: [],
    tempo: 120,
    drum_style: 'rock',
  });
  const [inspirationInput, setInspirationInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setSongData((prev) => ({ ...prev, [name]: value }));
  };

  const handleTempoChange = (value: number[]) => {
    setSongData((prev) => ({ ...prev, tempo: value[0] }));
  };

  const handleAddInspiration = () => {
    if (inspirationInput.trim()) {
      setSongData((prev) => ({
        ...prev,
        inspirations: [...prev.inspirations, inspirationInput.trim()],
      }));
      setInspirationInput('');
    }
  };

  const handleRemoveInspiration = (index: number) => {
    setSongData((prev) => ({
      ...prev,
      inspirations: prev.inspirations.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Send the song creation request and wait for the response
      const response = await ApiService.createSong(songData);
      
      // After successful song creation, redirect to the song details page
      if (response && response.result && response.result.title) {
        // Use the title from the response if available
        router.push(`/songs/${encodeURIComponent(response.result.title)}`);
      } else {
        // Fallback to using the title from the form
        router.push(`/songs/${encodeURIComponent(songData.title)}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred creating your song');
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-3xl">
      <CardHeader>
        <CardTitle>Create a New Song</CardTitle>
        <CardDescription>
          Fill out the form to generate a unique song with lyrics, melody, and rhythm.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title">Song Title</Label>
            <Input
              id="title"
              name="title"
              required
              value={songData.title}
              onChange={handleChange}
              placeholder="Enter a title for your song"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Song Description</Label>
            <Textarea
              id="description"
              name="description"
              required
              value={songData.description}
              onChange={handleChange}
              placeholder="Describe the theme, mood, and style of your song"
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label>Artist Inspirations</Label>
            <div className="flex space-x-2">
              <Input
                value={inspirationInput}
                onChange={(e) => setInspirationInput(e.target.value)}
                placeholder="Add an artist or band as inspiration"
              />
              <Button type="button" onClick={handleAddInspiration} variant="secondary">
                Add
              </Button>
            </div>
            {songData.inspirations.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {songData.inspirations.map((inspiration, index) => (
                  <div
                    key={index}
                    className="bg-secondary text-secondary-foreground px-3 py-1 rounded-full flex items-center gap-2"
                  >
                    <span>{inspiration}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveInspiration(index)}
                      className="text-secondary-foreground/70 hover:text-secondary-foreground"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="tempo">Tempo: {songData.tempo} BPM</Label>
            <Slider
              id="tempo"
              min={60}
              max={180}
              step={1}
              value={[songData.tempo || 120]}
              onValueChange={handleTempoChange}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="drum_style">Drum Style</Label>
            <select
              id="drum_style"
              name="drum_style"
              value={songData.drum_style}
              onChange={handleChange}
              className="w-full p-2 rounded-md border border-input bg-background"
            >
              <option value="rock">Rock</option>
              <option value="pop">Pop</option>
              <option value="jazz">Jazz</option>
              <option value="hiphop">Hip Hop</option>
              <option value="electronic">Electronic</option>
              <option value="folk">Folk</option>
            </select>
          </div>

          {error && <div className="text-red-500 text-sm">{error}</div>}
        </form>
      </CardContent>
      <CardFooter>
        <Button
          type="submit"
          onClick={handleSubmit}
          disabled={isLoading || !songData.title || !songData.description}
          className="w-full"
        >
          {isLoading ? (
            <>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                className="mr-2 h-4 w-4 animate-spin"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg> Creating Song...
            </>
          ) : (
            'Create Song'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}