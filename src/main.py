import os
import sys
import re
import glob
import argparse
import subprocess


def sanitize(name):
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def run_step(command):
    """Runs a pipeline step and exits on failure."""
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"\nERROR: Step failed. Command: {' '.join(str(c) for c in command)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Podcast Transcription Orchestrator")
    parser.add_argument("url", help="YouTube or Spotify URL")
    parser.add_argument("--topic", required=True, help="Topic/context for the polishing step")
    parser.add_argument("--lang", default="pt", help="Language code (e.g. pt, es, en)")
    parser.add_argument("--artifacts-dir", default="artifacts",
                        help="Directory for all intermediate and final artifacts")
    parser.add_argument("--video-date", default=None,
                        help="Upload date of the video (YYYY-MM-DD). Used for output naming.")
    parser.add_argument("--video-title", default=None,
                        help="Title of the video. Used for output naming.")
    args = parser.parse_args()

    os.makedirs(args.artifacts_dir, exist_ok=True)

    print("\n" + "=" * 55)
    print("  PODCAST TRANSCRIPTION PIPELINE")
    print("=" * 55 + "\n")

    # ── Step 1: Download ──────────────────────────────────────
    run_step([sys.executable, "src/downloader.py", args.url,
              "--output-dir", args.artifacts_dir])

    # Identify the downloaded audio file
    audio_files = sorted(
        glob.glob(os.path.join(args.artifacts_dir, "*.mp3")),
        key=os.path.getmtime, reverse=True
    )
    if not audio_files:
        print("Error: No audio file found after download.")
        sys.exit(1)

    current_audio = audio_files[0]

    # Determine base name for all output files
    if args.video_date and args.video_title:
        base_name = f"{args.video_date}_{sanitize(args.video_title)}"
    else:
        base_name = os.path.splitext(os.path.basename(current_audio))[0]

    print(f"\n  Base name  : {base_name}")
    print(f"  Audio file : {current_audio}")
    print(f"  Artifacts  : {args.artifacts_dir}\n")

    # ── Step 2: Process (split into chunks) ──────────────────
    run_step([sys.executable, "src/processor.py", current_audio])

    chunk_dirs = glob.glob(os.path.join(args.artifacts_dir, "chunks_*"))
    transcribe_input = chunk_dirs[0] if chunk_dirs else current_audio

    # ── Step 3: Transcribe ────────────────────────────────────
    run_step([
        sys.executable, "src/transcriber.py",
        "-i", transcribe_input,
        "--lang", args.lang,
        "--output-name", base_name,
        "--artifacts-dir", args.artifacts_dir,
    ])

    # ── Step 4: Polish ────────────────────────────────────────
    raw_text = os.path.join(args.artifacts_dir, f"{base_name}.txt")
    run_step([
        sys.executable, "src/polisher.py",
        raw_text,
        "--topic", args.topic,
        "--lang", args.lang,
        "--output-name", base_name,
    ])

    # ── Step 5: Clean up ─────────────────────────────────────
    run_step([
        sys.executable, "src/cleaner.py",
        "--artifacts-dir", args.artifacts_dir,
        "--base-name", base_name,
    ])

    polished = os.path.join(args.artifacts_dir, f"{base_name}.md")
    raw = os.path.join(args.artifacts_dir, f"{base_name}.txt")

    print("\n" + "=" * 55)
    print("  PIPELINE SUCCESSFUL")
    print(f"  Polished transcript : {polished}")
    print(f"  Raw transcript      : {raw}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
