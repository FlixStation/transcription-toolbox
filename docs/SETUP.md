# Setup Guide

This guide covers the installation of all system-level dependencies required by the Transcription Toolbox.

---

## 1. Python

Python **3.10 or higher** is required.

```bash
# Check your version
python3 --version

# macOS (via Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11
```

---

## 2. ffmpeg (Required)

`ffmpeg` is used to extract audio from video files and split audio into chunks.

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg

# Verify installation
ffmpeg -version
```

---

## 3. yt-dlp (Required for YouTube)

```bash
# Install with uv (recommended)
uv pip install yt-dlp

# Or install the standalone binary on macOS
brew install yt-dlp
```

---

## 4. Python Virtual Environment & Dependencies

Create and activate a virtual environment using uv:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix or macOS
# or
.venv\Scripts\activate     # On Windows
```

Install dependencies using uv (either from requirements.txt or pyproject.toml):

```bash
# Option 1: Install from requirements.txt
uv pip install -r requirements.txt

# Option 2: Install from pyproject.toml (recommended)
uv pip install -e .
```

---

## 5. API Keys

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Then edit `.env` with your actual API keys:

| Key | Where to get it | Required? |
|-----|----------------|-----------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | ✅ Yes |
| `MISTRAL_API_KEY` | [console.mistral.ai](https://console.mistral.ai) | Optional (enables Mistral fallback) |
| `SPOTIPY_CLIENT_ID` | [developer.spotify.com](https://developer.spotify.com/dashboard) | Optional (for Spotify URLs) |
| `SPOTIPY_CLIENT_SECRET` | Same Spotify Dashboard app | Optional |

---

## 6. YouTube Authentication (Optional but Recommended)

See the [Cookie Authentication Guide](./COOKIES_GUIDE.md) to set up `youtube_cookies.txt` for downloading age-restricted content or avoiding bot detection.
