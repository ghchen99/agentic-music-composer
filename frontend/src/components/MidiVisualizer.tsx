// src/components/MidiVisualizer.tsx
"use client";

import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MidiVisualizerProps {
  midiUrl: string;
  songTitle: string;
}

export function MidiVisualizer({ midiUrl, songTitle }: MidiVisualizerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [midiData, setMidiData] = useState<any>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioContext = useRef<AudioContext | null>(null);
  const midiPlayer = useRef<any>(null);

  // Load the MIDI file
  useEffect(() => {
    let isMounted = true;
    
    const loadMidi = async () => {
      try {
        setIsLoading(true);
        
        // In a real implementation, we would load the actual MIDI file
        // For now, we'll simulate loading
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        if (isMounted) {
          // Simulate MIDI data
          setMidiData({
            tracks: 4,
            duration: 180, // 3 minutes in seconds
            // Other MIDI data would be here in a real implementation
          });
          setDuration(180);
          setIsLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to load MIDI file');
          setIsLoading(false);
        }
      }
    };

    loadMidi();
    
    return () => {
      isMounted = false;
      if (audioContext.current) {
        // Clean up audio context
        if (audioContext.current.state !== 'closed') {
          audioContext.current.close();
        }
      }
      // Clear any interval
      if (midiPlayer.current) {
        clearInterval(midiPlayer.current);
      }
    };
  }, [midiUrl]);

  // Play/pause functionality
  const togglePlay = () => {
    if (!audioContext.current) {
      audioContext.current = new AudioContext();
    }

    if (isPlaying) {
      // Pause logic
      setIsPlaying(false);
      // In a real implementation, you'd pause the MIDI playback
      if (midiPlayer.current) {
        clearInterval(midiPlayer.current);
      }
    } else {
      // Play logic
      setIsPlaying(true);
      // In a real implementation, you'd start the MIDI playback
      
      // Simulate time updates
      midiPlayer.current = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= duration) {
            clearInterval(midiPlayer.current);
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  // Stop and reset
  const handleReset = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (midiPlayer.current) {
      clearInterval(midiPlayer.current);
    }
    // In a real implementation, you'd stop and reset the MIDI playback
  };

  // Format time as mm:ss
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Generate MIDI visualization
  const renderMidiVisualization = () => {
    if (!midiData) return null;

    // This is a simplified visualization
    // In a real implementation, you would analyze the MIDI data
    const tracks = ['Piano', 'Bass', 'Drums', 'Melody'];
    const instrumentColors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444'];

    return (
      <div className="w-full">
        {/* Timeline */}
        <div className="w-full bg-muted rounded-md h-2 mb-6 relative">
          <div 
            className="absolute h-full bg-primary rounded-md"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
          <div 
            className="absolute top-1/2 -translate-y-1/2 h-4 w-4 bg-primary rounded-full"
            style={{ left: `${(currentTime / duration) * 100}%` }}
          />
        </div>

        {/* Time display */}
        <div className="flex justify-between text-sm text-muted-foreground mb-6">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>

        {/* MIDI tracks visualization */}
        <div className="space-y-4">
          {tracks.map((track, trackIndex) => (
            <div key={trackIndex} className="w-full">
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium">{track}</span>
              </div>
              <div className="h-8 bg-muted/50 rounded-md w-full relative overflow-hidden">
                {/* Simulate notes for visualization */}
                {Array.from({ length: 20 }).map((_, i) => {
                  // Random position and length for visualization
                  const left = (i * 5) % 100;
                  const width = 3 + Math.random() * 7;
                  return (
                    <div
                      key={i}
                      className="absolute h-4 rounded-sm top-2"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: instrumentColors[trackIndex],
                        opacity: left < (currentTime / duration) * 100 ? 0.4 : 0.8
                      }}
                    />
                  );
                })}
                
                {/* Playhead */}
                <div 
                  className="absolute top-0 h-full w-px bg-primary opacity-70" 
                  style={{ left: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="pb-4">
        <CardTitle className="flex justify-between items-center">
          <span>MIDI Visualization: {songTitle}</span>
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="icon" 
              onClick={togglePlay} 
              disabled={isLoading || !!error}
            >
              {isPlaying ? (
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
              )}
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={handleReset} 
              disabled={isLoading || !!error || currentTime === 0}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <path d="M3 2v6h6"></path>
                <path d="M21 12A9 9 0 0 0 6 5.3L3 8"></path>
                <path d="M21 22v-6h-6"></path>
                <path d="M3 12a9 9 0 0 0 15 6.7l3-2.7"></path>
              </svg>
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => window.open(midiUrl, '_blank')}
              disabled={isLoading || !!error}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-10 w-10 animate-spin text-muted-foreground">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center h-64 text-center">
            <div>
              <p className="text-red-500 mb-2">Failed to load MIDI visualization</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        ) : (
          renderMidiVisualization()
        )}
      </CardContent>
    </Card>
  );
}