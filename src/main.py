import os
import sys
import argparse
import subprocess

# Add current dir to path to import tools if needed, but we'll call them via subprocess 
# for true isolation as per the "Toolbox" architectural style.

def run_step(command):
    """Runs a step and handles failure."""
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"\nERROR: Step failed. Command: {' '.join(command)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Podcast Transcription Orchestrator")
    parser.add_argument("url", help="YouTube or Spotify URL")
    parser.add_argument("--topic", required=True, help="Topic for cleaning context")
    parser.add_argument("--lang", default="es", help="Language code (e.g., es, pt, en)")
    args = parser.parse_args()

    artifacts_dir = "artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    print("\n" + "="*50)
    print("PODCAST TRANSCRIPTION PIPELINE")
    print("="*50 + "\n")

    # Step 1: Download
    # Note: We call it via sys.executable to ensure we use the same python environment
    run_step([sys.executable, "src/downloader.py", args.url, "--output-dir", artifacts_dir])

    # Find the downloaded file (Step 1 outputs its path, but for simplicity we search artifacts)
    import glob
    audio_files = sorted(glob.glob(os.path.join(artifacts_dir, "*.mp3")), key=os.path.getmtime, reverse=True)
    if not audio_files:
        print("Error: No audio file found in artifacts after download.")
        sys.exit(1)
    
    current_audio = audio_files[0]
    print(f"Current audio: {current_audio}")

    # Step 2: Process (Convert/Split)
    run_step([sys.executable, "src/processor.py", current_audio])
    
    # Check if chunks were created
    chunk_dirs = glob.glob(os.path.join(artifacts_dir, "chunks_*"))
    transcribe_input = chunk_dirs[0] if chunk_dirs else current_audio

    # Step 3: Transcribe
    base_name = os.path.splitext(os.path.basename(current_audio))[0]
    run_step([sys.executable, "src/transcriber.py", transcribe_input, "--lang", args.lang, "--output-name", base_name])

    # Step 4: Polish
    raw_text = os.path.join(artifacts_dir, f"{base_name}.txt")
    run_step([sys.executable, "src/polisher.py", raw_text, "--topic", args.topic, "--lang", args.lang, "--output-name", base_name])

    # Step 5: Cleanup
    run_step([sys.executable, "src/cleaner.py", "--artifacts-dir", artifacts_dir, "--base-name", base_name])

    print("\n" + "="*50)
    print("PIPELINE SUCCESSFUL")
    print(f"Final Transcript: {os.path.join(artifacts_dir, f'{base_name}.md')}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
