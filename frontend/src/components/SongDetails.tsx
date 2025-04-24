// src/components/SongDetails.tsx
"use client";

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ApiService } from '@/services/api';
import { SongDetails as SongDetailsType } from '@/types/song';
import { MidiVisualizer } from '@/components/MidiVisualizer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface SongDetailsProps {
  songTitle: string;
}

export function SongDetails({ songTitle }: SongDetailsProps) {
  const router = useRouter();
  const [songDetails, setSongDetails] = useState<SongDetailsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSongDetails() {
      try {
        setIsLoading(true);
        const details = await ApiService.getSongDetails(songTitle);
        setSongDetails(details);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load song details');
      } finally {
        setIsLoading(false);
      }
    }

    fetchSongDetails();
  }, [songTitle]);

  const handleDownload = () => {
    if (!songDetails) return;
    
    // Get the appropriate URL - either direct midi_url if available or from the API
    const midiUrl = songDetails.midi_url || ApiService.getMidiUrl(songDetails.title);
    
    // Create link and trigger download
    const link = document.createElement('a');
    link.href = midiUrl;
    link.download = `${songDetails.title}.mid`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const goBack = () => {
    router.push('/songs');
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-10 w-10 animate-spin text-muted-foreground">
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
      </div>
    );
  }

  if (error || !songDetails) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[50vh] space-y-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Error Loading Song</h2>
          <p className="text-muted-foreground">{error || 'Song details not found'}</p>
        </div>
        <Button onClick={goBack} variant="outline" className="mt-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4">
            <path d="M15 18l-6-6 6-6" />
          </svg> Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 w-full max-w-4xl">
      <div className="flex items-center justify-between">
        <Button onClick={goBack} variant="outline" size="sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4">
            <path d="M15 18l-6-6 6-6" />
          </svg> Back to Songs
        </Button>
        <Button onClick={handleDownload} variant="outline" size="sm">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg> Download MIDI
        </Button>
      </div>

      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-3xl">{songDetails.title}</CardTitle>
          <CardDescription className="text-lg">
            {songDetails.description}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <p className="text-sm font-medium mb-1">Tempo</p>
              <p>{songDetails?.tempo || 120} BPM</p>
            </div>
            <div>
              <p className="text-sm font-medium mb-1">Drum Style</p>
              <p className="capitalize">{songDetails?.drum_style || 'Standard'}</p>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-sm font-medium mb-2">Inspirations</p>
            <div className="flex flex-wrap gap-2">
              {songDetails.inspirations && songDetails.inspirations.length > 0 ? (
                songDetails.inspirations.map((inspiration, index) => (
                  <span
                    key={index}
                    className="bg-secondary text-secondary-foreground px-3 py-1 rounded-full text-sm"
                  >
                    {inspiration}
                  </span>
                ))
              ) : (
                <span className="text-muted-foreground">No inspirations provided</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <MidiVisualizer 
        midiUrl={songDetails.midi_url || ApiService.getMidiUrl(songDetails.title)} 
        songTitle={songDetails.title} 
      />

      <Tabs defaultValue="lyrics" className="w-full">
        <TabsList className="grid grid-cols-3 mb-4">
          <TabsTrigger value="lyrics">Lyrics</TabsTrigger>
          <TabsTrigger value="chords">Chord Progression</TabsTrigger>
          <TabsTrigger value="melody">Melody</TabsTrigger>
        </TabsList>
        
        <TabsContent value="lyrics" className="p-4 bg-muted/50 rounded-md">
          <h3 className="font-bold mb-4">Lyrics</h3>
          {songDetails.lyrics ? (
            <div className="space-y-6">
              {songDetails.lyrics.verse && (
                <div>
                  <h4 className="font-semibold mb-2">Verse</h4>
                  <pre className="whitespace-pre-wrap font-sans">{songDetails.lyrics.verse}</pre>
                </div>
              )}
              
              {songDetails.lyrics.chorus && (
                <div>
                  <h4 className="font-semibold mb-2">Chorus</h4>
                  <pre className="whitespace-pre-wrap font-sans">{songDetails.lyrics.chorus}</pre>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">No lyrics available</p>
          )}
        </TabsContent>
        
        <TabsContent value="chords" className="p-4 bg-muted/50 rounded-md">
          <h3 className="font-bold mb-4">Chord Progression</h3>
          {songDetails.chords ? (
            <div className="space-y-6">
              {songDetails.chords.verse && (
                <div>
                  <h4 className="font-semibold mb-2">Verse</h4>
                  <p className="font-mono text-lg">{songDetails.chords.verse.join(' | ')}</p>
                </div>
              )}
              
              {songDetails.chords.chorus && (
                <div>
                  <h4 className="font-semibold mb-2">Chorus</h4>
                  <p className="font-mono text-lg">{songDetails.chords.chorus.join(' | ')}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">No chord progression available</p>
          )}
        </TabsContent>
        
        <TabsContent value="melody" className="p-4 bg-muted/50 rounded-md">
          <h3 className="font-bold mb-4">Melody</h3>
          {(songDetails.melody_summary || songDetails.melody) ? (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Melody information is represented in the MIDI visualization above.
              </p>
              
              {/* Melody details from melody_summary */}
              {songDetails.melody_summary && (
                <div className="grid grid-cols-2 gap-4 bg-card p-4 rounded-md">
                  <div>
                    <h4 className="font-semibold mb-1">Verse</h4>
                    <p>{songDetails.melody_summary.verse_notes} notes</p>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">Chorus</h4>
                    <p>{songDetails.melody_summary.chorus_notes} notes</p>
                  </div>
                </div>
              )}
              
              {/* General melody information if available */}
              {typeof songDetails.melody === 'object' && songDetails.melody?.notes && (
                <p>
                  The melody contains {songDetails.melody.notes.length} notes across 
                  {' '}{songDetails.melody.measures || 'several'} measures.
                </p>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground">No melody information available</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}