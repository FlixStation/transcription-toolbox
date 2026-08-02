import os
import shutil
import argparse
import glob


def str2bool(value):
    """Parses 'True'/'False' (case-insensitive) into a bool for argparse."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Expected True or False, got: {value!r}")


def main():
    parser = argparse.ArgumentParser(description="Toolbox Step 5: Cleaner")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--base-name", help="Base name used for this video's files")
    parser.add_argument("--audio-file", help="Path to this run's downloaded/source audio file")
    parser.add_argument("--chunks-dir", help="Path to this run's audio chunk directory")
    parser.add_argument("--keep-files", type=str2bool, default=True,
                        help="Keep this run's intermediate audio and chunks. Pass True or "
                             "False (default: True). False deletes only this run's "
                             "intermediates; the final .md and .txt are never touched.")
    args = parser.parse_args()

    print("--- Step 5: Cleaning up artifacts ---")

    if args.keep_files:
        print("--keep-files True: leaving this run's intermediate files in place.")
        return

    if args.audio_file and os.path.exists(args.audio_file):
        os.remove(args.audio_file)
        print(f"Deleted audio file: {args.audio_file}")

    if args.chunks_dir and os.path.isdir(args.chunks_dir):
        shutil.rmtree(args.chunks_dir)
        print(f"Deleted chunk folder: {args.chunks_dir}")

    if args.base_name:
        pattern = os.path.join(args.artifacts_dir, f"polished_chunk_{args.base_name}_*.txt")
        for path in glob.glob(pattern):
            os.remove(path)
            print(f"Deleted polished chunk: {os.path.basename(path)}")

    print("Cleanup complete.")

if __name__ == "__main__":
    main()
