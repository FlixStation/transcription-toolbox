import os
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 5: Cleaner")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--base-name", help="Base name used for this video's files")
    args = parser.parse_args()

    print("--- Step 5: Cleaning up artifacts ---")

    if not os.path.exists(args.artifacts_dir):
        print("Nothing to clean.")
        return

    # Files to always preserve: polished transcript (.md) and raw transcript (.txt)
    keep_files = set()
    if args.base_name:
        keep_files.add(f"{args.base_name}.md")
        keep_files.add(f"{args.base_name}.txt")

    for item in os.listdir(args.artifacts_dir):
        item_path = os.path.join(args.artifacts_dir, item)

        # Always preserve .md files (polished transcripts)
        if item.endswith(".md"):
            print(f"Keeping polished transcript: {item}")
            continue

        # Preserve the raw .txt for the current video (not intermediate chunk txts)
        if item in keep_files:
            print(f"Keeping raw transcript: {item}")
            continue

        # Delete everything else: audio, chunk dirs, polished_chunk_*.txt, etc.
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"Deleted folder: {item}")
            else:
                os.remove(item_path)
                print(f"Deleted file: {item}")
        except Exception as e:
            print(f"Error deleting {item}: {e}")

    print("Cleanup complete.")

if __name__ == "__main__":
    main()
