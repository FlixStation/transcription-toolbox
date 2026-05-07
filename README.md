# Transcription Toolbox 🎙️

A **modular, fault-tolerant transcription pipeline** for podcasts and long-form audio. Downloads, transcribes, and polishes content from YouTube and Spotify — even on free API tiers — using a triple-layer fallback system.

---

## ✨ Features

- **5-Step Modular Pipeline**: Each stage is a standalone tool that can be run independently or as part of the full pipeline.
- **Chunk Persistence**: Every chunk is saved immediately. If the process crashes or hits a rate limit, it resumes exactly where it left off.
- **Triple-Layer Transcription Fallback**: Automatically switches providers if a quota is exhausted.
- **Quality-First Polishing**: Uses large LLMs (Llama 3.3 70B) to fix transcription errors, named entities, and formatting.
- **Automatic Cleanup**: Deletes all intermediate audio files after a successful run, keeping only the final transcript.

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
│  5. Cleaner     │  Deletes temp audio, keeps final .md
└────────┬────────┘
         │
         ▼
  artifacts/cleaned_transcript.md
```

---

## 🚀 Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
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

The final polished transcript will be saved to `artifacts/cleaned_transcript.md`.

---

## 🔧 Running Individual Steps

Each tool in `src/` can be run independently:

```bash
# Step 1: Download only
python3 src/downloader.py "https://youtu.be/..."

# Step 2: Split audio into chunks
python3 src/processor.py artifacts/my_audio.mp3

# Step 3: Transcribe a directory of chunks
python3 src/transcriber.py artifacts/chunks_my_audio/ --lang es

# Step 4: Polish a raw transcript
python3 src/polisher.py artifacts/raw_transcript.txt --topic "Roman history"

# Step 5: Clean up intermediate artifacts
python3 src/cleaner.py
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
