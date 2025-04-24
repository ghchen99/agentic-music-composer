# AI Songwriting Assistant Frontend

A modern web interface for creating and managing AI-generated songs, built with Next.js, Tailwind CSS, and ShadCN UI components.

## 🎵 Overview

The Songwriting Assistant Frontend provides an intuitive user interface for interacting with the AI songwriting backend. Users can create new songs by providing descriptions and inspirations, and then explore and play their generated musical compositions.

## ✨ Features

- 🎨 **Modern UI**: Clean, responsive design using Tailwind CSS and ShadCN UI components
- 🌓 **Dark/Light Mode**: Automatic theme switching with system preference support
- 📱 **Responsive Layout**: Works seamlessly on mobile, tablet, and desktop devices
- 🎵 **MIDI Visualisation**: Interactive player to visualise and play generated songs
- 🔍 **Song Details**: View lyrics, chord progressions, and melody information
- 🎚️ **Customisation Options**: Adjust tempo, drum style, and other song parameters
- 📂 **Song Library**: Browse and manage all generated songs

## 🖼️ Screenshots

<img src="./assets/songform.png" alt="Song request interface" width={500} height={300} />

## 🚀 Getting Started

### Prerequisites

- Node.js 18.17.0 or later
- npm or yarn package manager
- Backend server running (see backend README)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd songwriting-assistant/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Configure environment variables:
   Create a `.env.local` file in the root directory:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

4. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. Open your browser and navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js 15 app router pages
│   │   ├── page.tsx         # Home page
│   │   ├── songs/           # Song library and detail pages
│   │   └── layout.tsx       # Root layout with theme provider
│   ├── components/          # React components
│   │   ├── MidiVisualizer.tsx
│   │   ├── SongDetails.tsx
│   │   ├── SongForm.tsx
│   │   ├── theme-provider.tsx
│   │   └── ui/              # ShadCN UI components
│   ├── services/            # API service layer
│   │   └── api.ts           # Backend API communication
│   └── types/               # TypeScript type definitions
│       └── song.ts
├── public/                  # Static assets
└── package.json
```

## 🧩 Key Components

### SongForm

The main form for creating new songs with the following inputs:
- Song title
- Description
- Artist inspirations
- Tempo adjustment
- Drum style selection

### SongDetails

Displays comprehensive information about a generated song:
- Song metadata (title, description, tempo)
- Chord progressions for verse and chorus
- Lyrics display with verse/chorus sections
- Melody information
- MIDI visualisation and playback

### MidiVisualizer

An interactive component that provides:
- Visual representation of the MIDI tracks
- Play/pause controls
- Timeline visualisation
- Track-by-track breakdown

## 🔄 State Management

The application uses React's built-in state management with:
- `useState` for component-level state
- `useEffect` for side effects like API calls
- `useRouter` for navigation between pages

## 🌐 API Integration

The frontend communicates with the backend through the `ApiService` which provides methods for:
- Creating new songs
- Listing all songs
- Fetching song details
- Downloading MIDI files

## 📱 Responsive Design

The UI is fully responsive with:
- Mobile-first approach
- Breakpoint-based layout adjustments
- Flexible card and grid components
- Touch-friendly controls


## 🛠️ Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run ESLint
npm run lint
```

## 🔧 Configuration

- **Next.js Config**: `next.config.js` for Next.js configuration
- **Tailwind Config**: `tailwind.config.js` for styling customisation
- **TypeScript Config**: `tsconfig.json` for TypeScript settings
- **ESLint Config**: `eslint.config.mjs` for code quality

## 📦 Dependencies

- **Next.js**: React framework
- **React**: UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible UI primitives
- **ShadCN UI**: Component library based on Radix
- **Lucide React**: Icon library
- **next-themes**: Theme management

## 🤝 Working with the Backend

The frontend expects the backend to be running and accessible at the URL specified in `NEXT_PUBLIC_API_URL`. Make sure the backend is running before starting the frontend application.

## 📄 License

[MIT License](LICENSE)
