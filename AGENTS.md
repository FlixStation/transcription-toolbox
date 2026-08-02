# AGENTS.md

## Critical Commands

- Run full pipeline:
  ```bash
  python3 src/main.py "https://youtu.be/VIDEO_ID" --topic "Your topic" --lang es
  ```

- Run individual steps:
  ```bash
  python3 src/downloader.py "URL" --output-dir artifacts
  python3 src/processor.py artifacts/downloaded_audio.mp3
  python3 src/transcriber.py artifacts/chunks_audio/ --lang es
  python3 src/polisher.py artifacts/raw_transcript.txt --topic "Topic" --lang es
  python3 src/cleaner.py
  ```

## Architecture Quirks

- **5-step modular pipeline**: Each step runs independently but orchestrator (`src/main.py`) runs them in sequence using subprocess isolation.

- **Artifacts directory**: All intermediate files stored in `artifacts/`; final output is `artifacts/cleaned_transcript.md`.

- **Chunk persistence**: Every audio chunk and transcript chunk is saved immediately; process resumes where it left off on restart.

## Rate Limit System

- **Triple-layer transcription fallback**: Groq whisper-large-v3 → whisper-large-v3-turbo → Mistral voxtral-mini-latest.

- **Polishing fallback**: Llama 3.3 70B → groq/compound.

- **Safety delays**: 2s between transcription chunks, 10s between polishing chunks to respect rate limits.

## Dependencies & Setup

- **System deps**: ffmpeg, yt-dlp, spotdl, node (for JS runtime).

- **Python**: 3.12+ (pyproject.toml constraint). Prefer using uv for dependency management.

- **API keys**: GROQ_API_KEY required; MISTRAL_API_KEY optional (enables Mistral fallback).

- **Cookie auth**: `youtube_cookies.txt` in project root enables authenticated YouTube downloads; treat as sensitive.

## Chunking Strategy

- **Audio**: Split into 10-minute chunks via ffmpeg segment to stay under 25MB.

- **Transcript**: Raw transcript split into 4,000-word chunks for polishing to maintain context quality.

## Cleanup Behavior

- **Automatic**: Intermediate audio files and chunks deleted after successful run; only `cleaned_transcript.md` and `raw_transcript.txt` preserved.

- **Manual override**: Use `--keep-final false` with cleaner.py to preserve all artifacts.
