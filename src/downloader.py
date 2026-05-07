import os
import subprocess
import argparse
from pathlib import Path

def download_youtube(url, output_dir):
    """Downloads audio from YouTube using yt-dlp with cookie support."""
    print(f"--- Step 1: Downloading from YouTube ---")
    
    # Get title for a clean filename
    title_cmd = ["yt-dlp", "--get-title", "--no-playlist", url]
    title = subprocess.run(title_cmd, capture_output=True, text=True).stdout.strip()
    if not title: title = "youtube_audio"
    
    # Sanitize title
    sanitized_title = "".join([c for c in title if c.isalnum() or c in (" ", "_", "-")]).strip().replace(" ", "_")
    final_path = os.path.join(output_dir, f"{sanitized_title}.mp3")

    if os.path.exists(final_path):
        print(f"File already exists: {final_path}. Skipping.")
        return final_path

    # Check for cookies in the parent directory (root)
    cookie_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "youtube_cookies.txt"))
    
    command = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "0",
        "--extractor-args", "youtube:player-client=android_vr,web_creator",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "--output", os.path.join(output_dir, f"{sanitized_title}.%(ext)s"),
    ]
    
    if os.path.exists(cookie_file):
        print(f"Using cookies from: {cookie_file}")
        command.extend(["--cookies", cookie_file])
    
    command.append(url)
    
    # Handle JS runtime
    node_path = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
    if node_path:
        command.extend(["--js-runtimes", f"node:{node_path}", "--remote-components", "ejs:github"])

    print(f"Running download for: {title}")
    result = subprocess.run(command)
    
    if result.returncode == 0 and os.path.exists(final_path):
        return final_path
    return None

def download_spotify(url, output_dir):
    """Downloads audio from Spotify using spotdl."""
    print(f"--- Step 1: Downloading from Spotify ---")
    # Spotdl usually downloads to current dir, we'll move it later or use its template
    # For now, we'll assume spotdl is in the environment
    command = ["spotdl", "download", url, "--output", output_dir]
    result = subprocess.run(command)
    
    if result.returncode == 0:
        # spotdl doesn't make it easy to know the exact filename without parsing
        # For simplicity, we search the output_dir for new mp3s
        import glob
        files = sorted(glob.glob(os.path.join(output_dir, "*.mp3")), key=os.path.getmtime, reverse=True)
        return files[0] if files else None
    return None

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 1: Downloader")
    parser.add_argument("url", help="URL to download (YouTube or Spotify)")
    parser.add_argument("--output-dir", default="artifacts", help="Where to save the download")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    
    if "spotify.com" in args.url:
        path = download_spotify(args.url, args.output_dir)
    elif "youtube.com" in args.url or "youtu.be" in args.url:
        path = download_youtube(args.url, args.output_dir)
    else:
        print("Unsupported URL type.")
        return

    if path:
        print(f"SUCCESS: Downloaded to {path}")
    else:
        print("FAILED: Download failed.")

if __name__ == "__main__":
    main()
