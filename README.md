# 🌍 African Video Engine v2.0

> Transform any YouTube video into powerful African-voiced content using AI.

## Pipeline

```
YouTube → AssemblyAI ✅ → GPT-4o-mini ✅ → ElevenLabs ✅ → FFmpeg ✅
```

## Features

- 🎙 **AssemblyAI** transcription (no local Whisper needed)
- 🧙 **GURU rewrite** — African proverbs, warmth, communal energy
- 🔊 **ElevenLabs** deep African voice (Antoni)
- 🎬 **4 modes**: GURU · Documentary · Story · News
- 📊 Real-time progress bar with SSE streaming
- ⬇️ Download finished `.mp4` directly from the browser

## Quick Start (Local)

### 1. Clone & enter

```bash
git clone https://github.com/emmanuelbulus1/african-video-engine-.git
cd african-video-engine-
```

### 2. Add your API keys

```bash
cp .env.example .env
# edit .env with your 3 keys
```

### 3. Run

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Open **http://localhost:8000**

---

## Deploy on Railway

1. Push this repo to GitHub
2. Go to **railway.app → New Project → Deploy from GitHub**
3. Select `african-video-engine-`
4. Add **Variables**:

| Variable | Where to get it |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com |
| `ELEVENLABS_API_KEY` | elevenlabs.io |
| `ASSEMBLYAI_API_KEY` | assemblyai.com |

5. Railway builds & deploys automatically
6. Visit `your-app.up.railway.app/health` — all 3 should say **"connected"**

---

## Health Check

```
GET /health
```

```json
{
  "status": "healthy",
  "apis": {
    "openai":     "connected",
    "elevenlabs": "connected",
    "assemblyai": "connected"
  }
}
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Check API key status |
| `/api/transform` | POST | Start a transform job |
| `/api/job/{id}` | GET | Poll job progress |
| `/api/stream/{id}` | GET | SSE live progress stream |
| `/api/download/{id}` | GET | Download finished video |

### Transform Request

```json
{
  "youtube_url": "https://youtube.com/watch?v=...",
  "mode": "guru"
}
```

Modes: `guru` · `documentary` · `story` · `news`

---

## Project Structure

```
african-video-engine/
├── main.py          ← FastAPI app + endpoints
├── pipeline.py      ← Full AI pipeline (5 steps)
├── config.py        ← API keys + settings
├── requirements.txt ← Python dependencies
├── quickstart.sh    ← One-command local setup
├── Procfile         ← Railway / Heroku start command
└── frontend/
    ├── src/
    │   ├── App.tsx      ← Main React UI
    │   ├── main.tsx
    │   └── index.css    ← African-themed styles
    ├── index.html
    ├── vite.config.ts   ← Vite (no extra plugins)
    └── package.json
```

---

## Requirements

- Python 3.11+
- Node.js 18+ (for frontend build)
- FFmpeg (pre-installed on Railway)
- 3 API keys (OpenAI · ElevenLabs · AssemblyAI)

---

*Built with ❤️ for Africa 🌍*
