import os
import argparse
import time
import glob
from groq import Groq, RateLimitError
from dotenv import load_dotenv

# Correct import for Mistral SDK v2.x
try:
    from mistralai.client import Mistral
except ImportError:
    try:
        from mistralai import Mistral
    except ImportError:
        Mistral = None

# Load from root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

PRIMARY_MODEL = "whisper-large-v3"
SECONDARY_MODEL = "whisper-large-v3-turbo"
# Use the verified working model ID
MISTRAL_MODEL = "voxtral-mini-latest"

def transcribe_chunk(groq_client, mistral_client, chunk_path, language, base_name=None, max_retries=5):
    """Transcribes a single chunk with a triple-layer fallback system."""
    # Create transcript path with video identifier if provided
    if base_name:
        chunk_basename = os.path.basename(chunk_path).replace(".mp3", "")
        transcript_path = os.path.join(os.path.dirname(chunk_path), f"{base_name}_{chunk_basename}.txt")
    else:
        transcript_path = chunk_path.replace(".mp3", ".txt")
        
    if os.path.exists(transcript_path):
        print(f"Transcript already exists for {os.path.basename(chunk_path)}. Skipping.")
        with open(transcript_path, "r", encoding="utf-8") as f:
            return f.read()

    for attempt in range(max_retries):
        # --- Layer 1: Groq Primary ---
        try:
            print(f"Attempting {os.path.basename(chunk_path)} with Groq {PRIMARY_MODEL}...")
            with open(chunk_path, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=f,
                    model=PRIMARY_MODEL,
                    language=language if language != "auto" else None,
                    response_format="text",
                )
                with open(transcript_path, "w", encoding="utf-8") as tf:
                    tf.write(transcription)
                return transcription
        except RateLimitError:
            print(f"Groq {PRIMARY_MODEL} rate limited. Trying {SECONDARY_MODEL}...")
            
            # --- Layer 2: Groq Secondary ---
            try:
                with open(chunk_path, "rb") as f:
                    transcription = groq_client.audio.transcriptions.create(
                        file=f,
                        model=SECONDARY_MODEL,
                        language=language if language != "auto" else None,
                        response_format="text",
                    )
                    with open(transcript_path, "w", encoding="utf-8") as tf:
                        tf.write(transcription)
                    return transcription
            except RateLimitError:
                if mistral_client:
                    # --- Layer 3: Mistral Safety Net ---
                    print(f"Groq exhausted. Switching to Mistral {MISTRAL_MODEL}...")
                    try:
                        with open(chunk_path, "rb") as f:
                            # Correct Mistral SDK v2.x syntax
                            res = mistral_client.audio.transcriptions.complete(
                                model=MISTRAL_MODEL,
                                file={
                                    "content": f.read(),
                                    "file_name": os.path.basename(chunk_path),
                                },
                            )
                            transcription = res.text
                            with open(transcript_path, "w", encoding="utf-8") as tf:
                                tf.write(transcription)
                            return transcription
                    except Exception as me:
                        print(f"Mistral also failed: {me}")
                
                # If all failed, wait and retry the whole cycle
                wait_time = 120 * (attempt + 1)
                print(f"All models exhausted. Waiting {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            except Exception as e:
                print(f"Unexpected Groq error: {e}. Retrying in 30s...")
                time.sleep(30)
    
    raise Exception(f"Failed to transcribe {chunk_path} after {max_retries} attempts.")

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 3: Transcriber (Triple Fallback)")
    parser.add_argument("-i", help="Path to audio file or directory of chunks")
    parser.add_argument("--lang", default="es", help="Language code")
    parser.add_argument("-o", help="Base name for output files")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found.")
        return

    groq_client = Groq(api_key=GROQ_API_KEY)
    
    mistral_client = None
    if MISTRAL_API_KEY and Mistral:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
        print("Mistral fallback enabled.")

    if os.path.isdir(args.i):
        chunks = sorted(glob.glob(os.path.join(args.i, "chunk_*.mp3")))
        print(f"--- Step 3: Transcribing {len(chunks)} chunks ---")
        full_text = []
        for i, chunk in enumerate(chunks):
            print(f"Processing {i+1}/{len(chunks)}: {os.path.basename(chunk)}")
            text = transcribe_chunk(groq_client, mistral_client, chunk, args.lang, args.o)
            full_text.append(text)
            time.sleep(2)
        result = " ".join(full_text)
    else:
        result = transcribe_chunk(groq_client, mistral_client, args.i, args.lang, args.o)

    # Use provided output name or default
    base_name = args.o if args.o else "raw_transcript"
    output_path = os.path.join("artifacts", f"{base_name}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    # Also create a _raw version for compatibility
    # raw_output_path = os.path.join("artifacts", f"{base_name}_raw.txt")
    # # Copy to _raw version as well
    # with open(raw_output_path, "w", encoding="utf-8") as f:
    #     f.write(result)
    
    print(f"SUCCESS: Raw transcript saved to {output_path}")

if __name__ == "__main__":
    main()
