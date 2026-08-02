"""
playlist_runner.py — CED 301 Playlist Transcription Runner
===========================================================
Fetches all videos from a YouTube playlist, sorts them chronologically,
and runs the full transcription pipeline (Steps 1-5) for each one.

Step 6 (book chapter writing) is handled separately in Cowork by Claude.

Usage
-----
  # Run all unprocessed videos:
  python src/playlist_runner.py

  # Force re-process everything:
  python src/playlist_runner.py --force

  # Start from a specific date (skip earlier videos):
  python src/playlist_runner.py --start-from 2026-05-01

  # Custom playlist:
  python src/playlist_runner.py --playlist "https://www.youtube.com/playlist?list=..."

Output
------
  artifacts/playlist/{YYYY-MM-DD}_{sanitized_title}/
      {YYYY-MM-DD}_{sanitized_title}.md   ← polished transcript (keep)
      {YYYY-MM-DD}_{sanitized_title}.txt  ← raw transcript     (keep)
"""

import os
import sys
import re
import json
import shutil
import subprocess
import argparse
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLCl0Kx6cA2vKnURunHr1G6oE7ZwYdhK2m"
TOPIC = "Budismo Mahayana Zen, Lankavatara Sutra, Curso de Ensinamentos do Dharma"
LANG = "pt"

TOOLBOX_DIR = Path(__file__).resolve().parent.parent  # repo root


# ── Helpers ───────────────────────────────────────────────────────────────────

def sanitize(name: str) -> str:
    """Return a filesystem-safe version of name (max 80 chars)."""
    name = re.sub(r'[^\w\s-]', '', name, flags=re.UNICODE)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def get_playlist_videos(playlist_url: str) -> list[dict]:
    """
    Use yt-dlp --flat-playlist to fetch metadata for every video.
    Returns a list of dicts sorted chronologically by upload_date.
    """
    print(f"Fetching playlist metadata from:\n  {playlist_url}\n")

    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
        playlist_url,
    ]

    cookie_file = TOOLBOX_DIR / "youtube_cookies.txt"
    if cookie_file.exists():
        cmd.extend(["--cookies", str(cookie_file)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR fetching playlist:\n{result.stderr}")
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        video_id = data.get("id", "")
        title = data.get("title") or data.get("webpage_url_basename") or "untitled"
        upload_date = data.get("upload_date", "")       # "YYYYMMDD" or empty
        url = (data.get("url")
               or data.get("webpage_url")
               or f"https://www.youtube.com/watch?v={video_id}")

        # Normalise date to YYYY-MM-DD
        if upload_date and len(upload_date) == 8 and upload_date.isdigit():
            date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        else:
            date = "0000-00-00"

        videos.append({
            "id": video_id,
            "title": title,
            "date": date,
            "url": url,
        })

    # Sort chronologically (unknown dates go first)
    videos.sort(key=lambda v: v["date"])
    return videos


def already_processed(artifacts_dir: Path, base_name: str) -> bool:
    """Return True if the polished transcript already exists."""
    return (artifacts_dir / f"{base_name}.md").exists()


def run_pipeline(video: dict, artifacts_base: Path) -> str:
    """
    Run Steps 1-5 for a single video.
    Returns 'success', 'skipped', or 'failed'.
    """
    date = video["date"]
    sanitized_title = sanitize(video["title"])
    base_name = f"{date}_{sanitized_title}"
    artifacts_dir = artifacts_base / base_name

    if already_processed(artifacts_dir, base_name):
        print(f"  [SKIP]  {date} — {video['title'][:60]}")
        return "skipped"

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─'*60}")
    print(f"  {date} — {video['title']}")
    print(f"  Artifacts : {artifacts_dir}")
    print(f"{'─'*60}")

    cmd = [
        sys.executable,
        str(TOOLBOX_DIR / "src" / "main.py"),
        video["url"],
        "--topic", TOPIC,
        "--lang", LANG,
        "--artifacts-dir", str(artifacts_dir),
        "--video-date", date,
        "--video-title", video["title"],
    ]

    result = subprocess.run(cmd, cwd=str(TOOLBOX_DIR))

    if result.returncode == 0:
        print(f"\n  [OK]    {date} — {video['title'][:60]}")
        return "success"
    else:
        print(f"\n  [FAIL]  {date} — {video['title'][:60]}")
        return "failed"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CED 301 Playlist Transcription Runner (Steps 1-5)"
    )
    parser.add_argument(
        "--playlist", default=PLAYLIST_URL,
        help="YouTube playlist URL"
    )
    parser.add_argument(
        "--artifacts-base",
        default=str(TOOLBOX_DIR / "artifacts" / "playlist"),
        help="Parent directory for per-video artifact folders"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Delete existing artifacts and re-process all videos"
    )
    parser.add_argument(
        "--start-from", default=None, metavar="YYYY-MM-DD",
        help="Skip all videos uploaded before this date"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List videos without processing anything"
    )
    args = parser.parse_args()

    artifacts_base = Path(args.artifacts_base)
    artifacts_base.mkdir(parents=True, exist_ok=True)

    # ── Fetch playlist ─────────────────────────────────────────
    videos = get_playlist_videos(args.playlist)

    if not videos:
        print("ERROR: No videos found in playlist. Check the URL and cookies.")
        sys.exit(1)

    print(f"Found {len(videos)} videos in playlist.\n")

    # ── Dry run: just list ─────────────────────────────────────
    if args.dry_run:
        print(f"{'#':>3}  {'Date':12}  Title")
        print("─" * 70)
        for i, v in enumerate(videos, 1):
            status = ""
            sane = sanitize(v["title"])
            base_name = f"{v['date']}_{sane}"
            if already_processed(artifacts_base / base_name, base_name):
                status = " ✓"
            print(f"{i:>3}  {v['date']:12}  {v['title'][:50]}{status}")
        return

    # ── Process each video ────────────────────────────────────
    results: dict[str, list] = {"success": [], "skipped": [], "failed": []}

    for i, video in enumerate(videos, 1):
        print(f"\n[{i:>2}/{len(videos)}]", end=" ")

        # Date filter
        if args.start_from and video["date"] < args.start_from:
            print(f"  [SKIP]  {video['date']} — before --start-from ({args.start_from})")
            results["skipped"].append(video)
            continue

        # Force: wipe existing artifacts dir
        if args.force:
            sane = sanitize(video["title"])
            base_name = f"{video['date']}_{sane}"
            existing = artifacts_base / base_name
            if existing.exists():
                shutil.rmtree(existing)
                print(f"  [FORCE] Removed {existing.name}")

        status = run_pipeline(video, artifacts_base)
        results[status].append(video)

    # ── Summary ───────────────────────────────────────────────
    print(f"\n\n{'='*60}")
    print("  PLAYLIST RUNNER COMPLETE")
    print(f"{'='*60}")
    print(f"  Processed  : {len(results['success'])}")
    print(f"  Skipped    : {len(results['skipped'])}")
    print(f"  Failed     : {len(results['failed'])}")
    print(f"\n  Transcripts saved in:\n  {artifacts_base}\n")

    if results["failed"]:
        print("  Failed videos:")
        for v in results["failed"]:
            print(f"    • {v['date']}  {v['title']}")

    if results["success"]:
        print("\n  Next step — open Cowork and ask Claude to write the book chapters")
        print("  from the polished transcripts in the folder above.")


if __name__ == "__main__":
    main()
