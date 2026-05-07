import os
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 5: Cleaner")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--keep-final", action="store_true", default=True)
    args = parser.parse_args()

    print("--- Step 5: Cleaning up artifacts ---")
    
    if not os.path.exists(args.artifacts_dir):
        print("Nothing to clean.")
        return

    # Files we definitely want to keep (the final result)
    protected = ["cleaned_transcript.md", "raw_transcript.txt"]

    for item in os.listdir(args.artifacts_dir):
        item_path = os.path.join(args.artifacts_dir, item)
        
        if args.keep_final and item in protected:
            print(f"Keeping final result: {item}")
            continue
            
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
