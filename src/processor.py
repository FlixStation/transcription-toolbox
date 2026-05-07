import os
import subprocess
import argparse
import glob
import math

def split_audio(audio_path, max_size_mb=24):
    """Splits audio into chunks smaller than max_size_mb."""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        print(f"File is {file_size_mb:.2f}MB, no splitting needed.")
        return [audio_path]

    print(f"--- Step 2: Splitting {file_size_mb:.2f}MB into chunks ---")
    
    base_dir = os.path.dirname(audio_path)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    # Sanitize base_name for directory
    clean_name = "".join([c for c in base_name if c.isalnum() or c == "_"])
    chunk_dir = os.path.join(base_dir, f"chunks_{clean_name}")
    os.makedirs(chunk_dir, exist_ok=True)
    
    # 10 minutes (600s) is safe for MP3s to stay under 25MB
    output_pattern = os.path.join(chunk_dir, "chunk_%03d.mp3")
    split_cmd = [
        "ffmpeg", "-i", audio_path,
        "-f", "segment",
        "-segment_time", "600",
        "-c", "copy",
        output_pattern
    ]
    
    try:
        subprocess.run(split_cmd, check=True, capture_output=True)
        chunks = sorted(glob.glob(os.path.join(chunk_dir, "chunk_*.mp3")))
        print(f"SUCCESS: Split into {len(chunks)} chunks in {chunk_dir}")
        return chunks
    except Exception as e:
        print(f"ERROR: Splitting failed: {e}")
        return [audio_path]

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 2: Audio Processor")
    parser.add_argument("input", help="Path to the audio or video file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File not found: {args.input}")
        return

    # Check if it's a video file that needs conversion (basic check)
    ext = os.path.splitext(args.input)[1].lower()
    if ext in [".webm", ".mp4", ".mkv"]:
        print(f"Detected video file {ext}. Extracting audio...")
        audio_path = args.input.replace(ext, ".mp3")
        subprocess.run(["ffmpeg", "-i", args.input, "-vn", "-ab", "128k", "-ar", "44100", "-y", audio_path])
        input_file = audio_path
    else:
        input_file = args.input

    split_audio(input_file)

if __name__ == "__main__":
    main()
