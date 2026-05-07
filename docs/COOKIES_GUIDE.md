# 🍪 YouTube Cookie Authentication Guide

This guide explains **why** cookies are needed and how to **safely export your own** so the toolbox can download authenticated YouTube content.

---

## Why are cookies needed?

YouTube increasingly challenges automated downloaders with "Sign in to confirm you're not a bot" errors. By providing your own session cookies, `yt-dlp` can authenticate as you and bypass these checks.

> [!CAUTION]
> **Your `youtube_cookies.txt` is as sensitive as your password.** It contains your login session.
> - ❌ Never commit it to Git
> - ❌ Never share it publicly
> - ✅ The `.gitignore` in this project already blocks it

---

## Option A — Browser Extension (Recommended)

This is the easiest method. A small browser extension exports your cookies directly from your active YouTube session.

### Step 1: Install the extension
- **Chrome/Edge**: Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- **Firefox**: Install [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

### Step 2: Log in to YouTube
Make sure you are logged into your Google account at [youtube.com](https://www.youtube.com).

### Step 3: Export the cookies
1. Navigate to `https://www.youtube.com`
2. Click the extension icon in your browser toolbar
3. Select **"Export"** — choose **Netscape format** if given a choice
4. Save the file as `youtube_cookies.txt`

### Step 4: Place the file in the project root
```
transcription-toolbox/
├── src/
├── youtube_cookies.txt   ← place it here
└── ...
```

---

## Option B — Using `yt-dlp` directly (No extension needed)

If you prefer not to install a browser extension, `yt-dlp` can extract cookies directly from your installed browser.

```bash
# Export cookies from Chrome
yt-dlp --cookies-from-browser chrome --skip-download "https://www.youtube.com" --cookies youtube_cookies.txt

# Export cookies from Firefox
yt-dlp --cookies-from-browser firefox --skip-download "https://www.youtube.com" --cookies youtube_cookies.txt

# Export cookies from Safari (macOS only)
yt-dlp --cookies-from-browser safari --skip-download "https://www.youtube.com" --cookies youtube_cookies.txt
```

> [!NOTE]
> On macOS, `yt-dlp` may prompt the system keychain for permission. This is expected and safe — it only reads the cookies, not your password.

---

## Cookie Expiry

Session cookies expire periodically (usually every few weeks to months). If you start seeing authentication errors, simply re-export your cookies following the steps above and replace the existing `youtube_cookies.txt`.

---

## Verifying it works

Run the downloader directly against a YouTube URL to confirm authentication is working:

```bash
python3 src/downloader.py "https://www.youtube.com/watch?v=SOME_VIDEO_ID"
```

If successful, you should see the download start without any bot-check warnings.
