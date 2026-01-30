# Media Mind AI - Frontend

React frontend application for the Media Mind AI system.

## Features

- 📤 **File Upload Sidebar**: Upload and manage PDFs, audio, and video files
- 💬 **Chat Interface**: Ask questions about uploaded content using RAG
- 📋 **Summary Section**: View summaries, transcriptions, and timestamps
- 🎯 **Timestamp Navigation**: Extract and navigate to specific timestamps in audio/video

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set your API URL:
```
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal).

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx          # File upload and management
│   │   ├── ChatArea.jsx         # Q&A chat interface
│   │   └── SummarySection.jsx   # Summaries and timestamps
│   ├── services/
│   │   └── api.js               # Backend API client
│   ├── App.jsx                  # Main app component
│   └── main.jsx                 # Entry point
├── .env.example
└── package.json
```

## Usage

1. **Upload Files**: Click "Upload" in the sidebar to add PDFs, audio, or video files
2. **Select File**: Click on a file in the sidebar to select it
3. **Ask Questions**: Type questions in the chat area to get answers based on your files
4. **View Summaries**: Check the summary section for file summaries and transcriptions
5. **Extract Timestamps**: Search for text in the timestamps tab to find specific moments

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## License

MIT
