// src/app/songs/page.tsx
"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiService } from '@/services/api';
import { Song } from '@/types/song';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDate, truncateText } from '@/lib/utils';

export default function SongsPage() {
  const router = useRouter();
  const [songs, setSongs] = useState<Song[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSongs() {
      try {
        setIsLoading(true);
        const songsData = await ApiService.listSongs();
        setSongs(songsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load songs');
      } finally {
        setIsLoading(false);
      }
    }

    fetchSongs();
  }, []);

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Song Library</h1>
          <Button onClick={() => router.push('/')} variant="outline">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4">
              <path d="M15 18l-6-6 6-6" />
            </svg> Back to Home
          </Button>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center min-h-[200px]">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-10 w-10 animate-spin text-muted-foreground">
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-500 mb-4">{error}</p>
            <Button onClick={() => router.push('/')} variant="outline">
              Return to Home
            </Button>
          </div>
        ) : songs.length === 0 ? (
          <div className="text-center py-12 bg-muted/30 rounded-lg">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="40" 
              height="40" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="text-muted-foreground mx-auto mb-4"
            >
              <path d="M9 18V5l12-2v13"/>
              <circle cx="6" cy="18" r="3"/>
              <circle cx="18" cy="16" r="3"/>
            </svg>
            <h2 className="text-xl font-semibold mb-2">No Songs Yet</h2>
            <p className="text-muted-foreground mb-6">
              You haven't created any songs yet. Let's make your first masterpiece!
            </p>
            <Button onClick={() => router.push('/')}>Create Your First Song</Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {songs.map((song) => (
              <Link href={`/songs/${encodeURIComponent(song.title)}`} key={song.title} passHref>
                <Card className="h-full hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader className="pb-2">
                    <CardTitle className="line-clamp-1">{song.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {truncateText(song.description, 120)}
                    </p>
                  </CardContent>
                  <CardFooter className="text-xs text-muted-foreground">
                    Created: {formatDate(song.created_at)}
                  </CardFooter>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}