# Transcription Toolbox 🎙️

A **modular, fault-tolerant transcription pipeline** for podcasts and long-form audio — even on free API tiers — using a triple-layer fallback system.

- **Full pipeline** (`main.py`): downloads, transcribes, and polishes content from **YouTube or Spotify URLs** only.
- **Individual steps**: each stage (`processor.py`, `transcriber.py`, `polisher.py`, `cleaner.py`) can be run directly on **any local audio or video file** — no YouTube/Spotify required. See [Running Individual Steps](#-running-individual-steps).

---

## ✨ Features

- **5-Step Modular Pipeline**: Each stage is a standalone tool that can be run independently or as part of the full pipeline.
- **Chunk Persistence**: Every chunk is saved immediately. If the process crashes or hits a rate limit, it resumes exactly where it left off.
- **Triple-Layer Transcription Fallback**: Automatically switches providers if a quota is exhausted.
- **Quality-First Polishing**: Uses large LLMs (Llama 3.3 70B) to fix transcription errors, named entities, and formatting.
- **Optional Cleanup**: Intermediate files are kept by default so you can inspect or resume; pass `--keep-files False` to delete *this run's* audio and chunks after a successful run. Cleanup is scoped to the current run only — other videos' files in `artifacts/` are never touched.

---

## 🏗️ Architecture

```
URL (YouTube / Spotify)
        │
        ▼
┌─────────────────┐
│  1. Downloader  │  yt-dlp / spotdl with cookie auth
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Processor   │  ffmpeg: extract audio, split into 10-min chunks
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  3. Transcriber — Triple Fallback        │
│                                          │
│  Layer 1: Groq whisper-large-v3          │
│  Layer 2: Groq whisper-large-v3-turbo    │  ← if Layer 1 quota exhausted
│  Layer 3: Mistral voxtral-mini-latest    │  ← if Layer 2 quota exhausted
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. Polisher — Quality-First LLM    │
│                                     │
│  Primary:  Llama 3.3 70B Versatile  │
│  Fallback: groq/compound            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  5. Cleaner     │  --keep-files (default: True); set to False to delete temp audio
└────────┬────────┘
         │
         ▼
  artifacts/cleaned_transcript.md
```

---

## 🚀 Quickstart

### 1. Set up virtual environment and install dependencies

```bash
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Unix or macOS
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -e .
uv pip install -r requirements.txt
```

> See [docs/SETUP.md](docs/SETUP.md) for system-level dependencies (ffmpeg, yt-dlp).

### 2. Configure your API keys

```bash
cp .env.example .env
# Edit .env and add your Groq (required) and Mistral (optional) keys
```

### 3. Set up YouTube authentication (recommended)

```bash
# Place your exported cookies in the project root
# See docs/COOKIES_GUIDE.md for step-by-step instructions
```

### 4. Run the full pipeline

```bash
python3 src/main.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" \
    --topic "Your podcast topic" \
    --lang "es"
```

#### Optional Flags

- `--keep-files`: Keep intermediate files after successful run. Pass `True` or `False` (default: `True`)

The final polished transcript will be saved to `artifacts/cleaned_transcript.md`.

---

## 🔧 Running Individual Steps

Each tool in `src/` can be run independently. **Step 1 (Downloader) only supports YouTube/Spotify URLs** — but Steps 2–5 work on any local audio or video file, so you can skip the downloader entirely if you already have a file (a local recording, a podcast RSS download, audio from another source, etc.):

```bash
# Step 1: Download only (YouTube/Spotify URL required)
python3 src/downloader.py "https://youtu.be/..."

# --- OR, if you already have a local file, start here instead ---

# Step 2: Split audio into chunks (accepts any local .mp3/.wav or video file;
# .webm/.mp4/.mkv are auto-converted to audio first)
python3 src/processor.py artifacts/my_audio.mp3

# Step 3: Transcribe a directory of chunks (or a single audio file)
python3 src/transcriber.py -i artifacts/chunks_my_audio/ --lang es

# Step 4: Polish a raw transcript
python3 src/polisher.py artifacts/raw_transcript.txt --topic "Roman history"

# Step 5: Clean up this run's intermediate artifacts only (final .md/.txt are never touched)
python3 src/cleaner.py --keep-files False \
    --base-name my_audio \
    --audio-file artifacts/my_audio.mp3 \
    --chunks-dir artifacts/chunks_my_audio
```

---

## 📋 Rate Limits & The Fallback System

The toolbox is designed to work within **free API tiers**:

| Model | Provider | Limit | Role |
|-------|----------|-------|------|
| `whisper-large-v3` | Groq | 7,200 sec/hour | Primary transcription |
| `whisper-large-v3-turbo` | Groq | shared quota | Secondary |
| `voxtral-mini-latest` | Mistral | 50K tokens/min | Safety net |
| `llama-3.3-70b-versatile` | Groq | 1K req/day | Primary polishing |
| `groq/compound` | Groq | 250 req/day | Polishing fallback |

When a model's quota is exhausted, the toolbox **automatically switches to the next layer** without any manual intervention.

---

## 📁 Project Structure

```
transcription-toolbox/
├── src/
│   ├── main.py          # Orchestrator
│   ├── downloader.py    # Step 1: YouTube / Spotify
│   ├── processor.py     # Step 2: Extract & split audio
│   ├── transcriber.py   # Step 3: Triple-fallback transcription
│   ├── polisher.py      # Step 4: LLM quality polishing
│   └── cleaner.py       # Step 5: Artifact cleanup
├── docs/
│   ├── COOKIES_GUIDE.md # YouTube authentication setup
│   └── SETUP.md         # Full installation guide
├── .env.example         # API key template
├── requirements.txt
└── LICENSE
```

---

## 📚 Documentation

- [Full Setup Guide](docs/SETUP.md)
- [YouTube Cookie Authentication](docs/COOKIES_GUIDE.md)

---

## 📄 License

[MIT](LICENSE)
