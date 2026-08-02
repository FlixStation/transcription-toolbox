import os
import sys
import re
import argparse
import subprocess


def sanitize(name):
    """Sanitize a string for use as a filename."""
    name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def str2bool(value):
    """Parses 'True'/'False' (case-insensitive) into a bool for argparse."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Expected True or False, got: {value!r}")


def run_step(command):
    """Runs a pipeline step and exits on failure."""
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"\nERROR: Step failed. Command: {' '.join(str(c) for c in command)}")
        sys.exit(1)


def run_step_capture(command):
    """Runs a pipeline step, streaming its output live while also capturing it. Exits on failure."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []
    for line in process.stdout:
        print(line, end="")
        lines.append(line)
    process.wait()
    if process.returncode != 0:
        print(f"\nERROR: Step failed. Command: {' '.join(str(c) for c in command)}")
        sys.exit(1)
    return "".join(lines)


def chunk_dir_for(audio_path):
    """Mirrors processor.py's chunk directory naming convention."""
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    clean_name = "".join([c for c in base_name if c.isalnum() or c == "_"])
    return os.path.join(os.path.dirname(audio_path), f"chunks_{clean_name}")


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
    parser.add_argument("--keep-files", type=str2bool, default=True,
                        help="Keep intermediate chunks and transcription files after the run. "
                             "Pass True or False (default: True).")
    args = parser.parse_args()

    os.makedirs(args.artifacts_dir, exist_ok=True)

    print("\n" + "=" * 55)
    print("  PODCAST TRANSCRIPTION PIPELINE")
    print("=" * 55 + "\n")

    # ── Step 1: Download ──────────────────────────────────────
    download_output = run_step_capture([sys.executable, "src/downloader.py", args.url,
                                         "--output-dir", args.artifacts_dir])

    # Identify the exact file this run downloaded (never guess from directory contents:
    # other runs may have left newer-mtime .mp3 files from unrelated videos in artifacts-dir)
    current_audio = None
    for line in download_output.splitlines():
        if line.startswith("AUDIO_PATH::"):
            current_audio = line.split("AUDIO_PATH::", 1)[1].strip()
            break

    if not current_audio or not os.path.exists(current_audio):
        print("Error: Could not determine downloaded audio file path.")
        sys.exit(1)

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

    chunk_dir = chunk_dir_for(current_audio)
    transcribe_input = chunk_dir if os.path.isdir(chunk_dir) else current_audio

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
    cleaner_cmd = [
        sys.executable, "src/cleaner.py",
        "--artifacts-dir", args.artifacts_dir,
        "--base-name", base_name,
        "--audio-file", current_audio,
        "--keep-files", str(args.keep_files),
    ]
    if os.path.isdir(chunk_dir):
        cleaner_cmd.extend(["--chunks-dir", chunk_dir])
    run_step(cleaner_cmd)

    polished = os.path.join(args.artifacts_dir, f"{base_name}.md")
    raw = os.path.join(args.artifacts_dir, f"{base_name}.txt")

    print("\n" + "=" * 55)
    print("  PIPELINE SUCCESSFUL")
    print(f"  Polished transcript : {polished}")
    print(f"  Raw transcript      : {raw}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
