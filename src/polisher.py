import os
import argparse
import time
from groq import Groq, RateLimitError
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Quality-First Model Strategy
PRIMARY_POLISH_MODEL = "llama-3.3-70b-versatile"
FALLBACK_POLISH_MODEL = "groq/compound"
# groq/compound rejects requests as large as the 4,000-word primary chunks
# (413 Request Entity Too Large), so it gets smaller sub-chunks.
FALLBACK_CHUNK_WORD_LIMIT = 1000

def polish_with_fallback_model(client, chunk, topic, language):
    """Polishes a chunk with the fallback model, splitting it to fit its smaller payload limit."""
    words = chunk.split()
    sub_chunks = [
        " ".join(words[i:i + FALLBACK_CHUNK_WORD_LIMIT])
        for i in range(0, len(words), FALLBACK_CHUNK_WORD_LIMIT)
    ] or [chunk]

    polished_parts = []
    for sub_chunk in sub_chunks:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a specialized editor in {topic}. Clean this raw {language} transcript. "
                               f"Correct spelling, remove fillers, maintain speaker's voice. Return ONLY cleaned text.",
                },
                {"role": "user", "content": sub_chunk},
            ],
            model=FALLBACK_POLISH_MODEL,
            temperature=0.3,
        )
        polished_parts.append(chat_completion.choices[0].message.content)
    return "\n".join(polished_parts)

def polish_chunk(client, chunk, topic, language, chunk_id, artifacts_dir, base_name, retries=3):
    """Clean a transcript chunk with a Quality-First fallback system."""
    persist_path = os.path.join(artifacts_dir, f"polished_chunk_{base_name}_{chunk_id}.txt")
    if os.path.exists(persist_path):
        print(f"Polished transcript already exists for chunk {chunk_id}. Skipping.")
        with open(persist_path, "r", encoding="utf-8") as f:
            return f.read()

    # Try Primary High-Quality Model
    try:
        print(f"Polishing chunk {chunk_id} with {PRIMARY_POLISH_MODEL} (High Quality)...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a specialized editor with deep expertise in {topic}. "
                               f"The following is a raw transcription in {language}. "
                               f"Meticulously clean it: correct spelling, grammar, and specialized terms. "
                               f"Remove fillers but preserve the speaker's unique voice and the depth of the content. "
                               f"Return ONLY the cleaned text.",
                },
                {"role": "user", "content": chunk},
            ],
            model=PRIMARY_POLISH_MODEL,
            temperature=0.3,
        )
        content = chat_completion.choices[0].message.content
        with open(persist_path, "w", encoding="utf-8") as f:
            f.write(content)
        return content
    except RateLimitError:
        print(f"Rate limit reached for {PRIMARY_POLISH_MODEL}. Falling back to {FALLBACK_POLISH_MODEL}...")
        # Fallback to the more generous model
        try:
            content = polish_with_fallback_model(client, chunk, topic, language)
            with open(persist_path, "w", encoding="utf-8") as f:
                f.write(content)
            return content
        except Exception as e:
            print(f"All models failed for chunk {chunk_id}: {e}. Waiting 60s...")
            time.sleep(60)
            raise e

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 4: Polisher (Quality-First)")
    parser.add_argument("input", help="Path to the raw transcript file")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--lang", default="Spanish")
    parser.add_argument("--output-name", help="Base name for the output file")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found.")
        return

    client = Groq(api_key=GROQ_API_KEY)
    
    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Using moderate chunks (4,000 words) for high-quality context and TPM safety
    words = raw_text.split()
    chunk_size = 4000 
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]

    artifacts_dir = os.path.dirname(args.input)
    base_name = args.output_name or "default"
    print(f"--- Step 4: Polishing {len(chunks)} chunks (Quality-First Strategy) ---")

    polished_text = []
    for i, chunk in enumerate(chunks):
        print(f"Processing {i+1}/{len(chunks)}...")
        cleaned = polish_chunk(client, chunk, args.topic, args.lang, i, artifacts_dir, base_name)
        polished_text.append(cleaned)
        time.sleep(10) # Safety delay to respect the 30 RPM limit of Llama 3.3

    output_filename = f"{args.output_name}.md" if args.output_name else "cleaned_transcript.md"
    output_path = os.path.join(artifacts_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(polished_text))
    
    print(f"SUCCESS: Polished transcript saved to {output_path}")

if __name__ == "__main__":
    main()
