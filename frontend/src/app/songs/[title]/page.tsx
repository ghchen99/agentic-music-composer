// src/app/songs/[title]/page.tsx
"use client";

import { SongDetails } from "@/components/SongDetails";
import { useParams } from "next/navigation";

export default function SongPage() {
  // Use next/navigation's useParams hook instead of accessing params directly
  const params = useParams();
  const title = Array.isArray(params.title) ? params.title[0] : params.title;
  const decodedTitle = decodeURIComponent(title as string);

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <SongDetails songTitle={decodedTitle} />
      </div>
    </div>
  );
}