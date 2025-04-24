// src/app/page.tsx
import Link from 'next/link';
import { SongForm } from '@/components/SongForm';
import { Button } from '@/components/ui/button';
// Replacing imported icon with custom SVG
// import { MusicIcon } from '@radix-ui/react-icons';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto space-y-12">
        <section className="text-center space-y-4">
          <div className="inline-block p-4 bg-primary/10 rounded-full mb-4">
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
              className="text-primary"
            >
              <path d="M9 18V5l12-2v13"/>
              <circle cx="6" cy="18" r="3"/>
              <circle cx="18" cy="16" r="3"/>
            </svg>
          </div>
          <h1 className="text-4xl font-bold tracking-tight">AI Songwriting Assistant</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Create original songs with AI-generated chord progressions, lyrics, melody, and rhythm. 
            Just describe your song and get a complete musical piece.
          </p>
        </section>

        <div className="flex justify-center">
          <SongForm />
        </div>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold text-center">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-card border rounded-lg p-6 space-y-2 text-center">
              <div className="bg-primary/10 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-primary">1</span>
              </div>
              <h3 className="font-bold">Describe Your Song</h3>
              <p className="text-muted-foreground">Tell us about the theme, mood, and style you want for your song</p>
            </div>
            
            <div className="bg-card border rounded-lg p-6 space-y-2 text-center">
              <div className="bg-primary/10 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-primary">2</span>
              </div>
              <h3 className="font-bold">AI Generates Music</h3>
              <p className="text-muted-foreground">Our AI creates chord progressions, lyrics, melody, and drum patterns</p>
            </div>
            
            <div className="bg-card border rounded-lg p-6 space-y-2 text-center">
              <div className="bg-primary/10 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="font-bold text-primary">3</span>
              </div>
              <h3 className="font-bold">Play &amp; Download</h3>
              <p className="text-muted-foreground">Visualize and play your song, then download the MIDI file</p>
            </div>
          </div>
        </section>

        <section className="bg-card border rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Already Created a Song?</h2>
          <p className="text-muted-foreground mb-6">
            Check out your previous creations or listen to songs created by others.
          </p>
          <Link href="/songs" passHref>
            <Button>Browse Songs</Button>
          </Link>
        </section>
      </div>
    </div>
  );
}