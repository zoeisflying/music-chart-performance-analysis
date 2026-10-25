import csv
import os
import random
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INPUT_CSV = Path("data/sampling/youtube_matching_results.csv")
OUTPUT_DIR = Path("data/raw/audio")
LOG_CSV = Path("data/raw/audio_download_log.csv")

FFMPEG_LOCATION = Path(r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build-shared\bin")

SLEEP_MIN = 0.8
SLEEP_MAX = 1.8
MAX_RETRIES = 3


def run_command(command):
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def load_existing_log():
    if not LOG_CSV.exists():
        return {}

    with LOG_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        return {
            row["spotify_track_id"]: row
            for row in csv.DictReader(f)
            if row.get("spotify_track_id")
        }


def save_log(log):
    LOG_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "spotify_track_id",
        "title",
        "artist",
        "youtube_video_id",
        "youtube_title",
        "status",
        "attempts",
        "output_file",
        "error",
    ]

    with LOG_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in log.values():
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def check_dependencies():
    checks = {
        "yt-dlp": [sys.executable, "-m", "yt_dlp", "--version"],
        "ffmpeg": [str(FFMPEG_LOCATION / "ffmpeg.exe"), "-version"],
        "ffprobe": [str(FFMPEG_LOCATION / "ffprobe.exe"), "-version"],
    }

    for name, command in checks.items():
        result = run_command(command)

        if result.returncode != 0:
            print(f"[ERROR] {name} is not available.")
            print(result.stdout[-1500:])
            return False

        first_line = result.stdout.splitlines()[0] if result.stdout else "OK"
        print(f"[OK] {name}: {first_line}")

    return True


def download_one(row, output_path):
    video_id = row["youtube_video_id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    for attempt in range(1, MAX_RETRIES + 1):
        command = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--ffmpeg-location",
            str(FFMPEG_LOCATION),
            "--extractor-args",
            "youtube:player_client=android",
            "--no-playlist",
            "--no-overwrites",
            "--continue",
            "--ignore-errors",
            "-x",
            "--audio-format",
            "wav",
            "--audio-quality",
            "0",
            "-o",
            str(output_path),
            url,
        ]

        result = run_command(command)

        if result.returncode == 0 and output_path.exists():
            return True, attempt, ""

        if attempt < MAX_RETRIES:
            time.sleep(2 * attempt)

        error_text = result.stdout[-3000:] if result.stdout else "Unknown error"

    return False, MAX_RETRIES, error_text


def main():
    input_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_CSV

    if not input_csv.exists():
        print(f"[ERROR] Input CSV not found: {input_csv}")
        print("Usage:")
        print("  python src/youtube/download_audio.py path/to/youtube_matching_results.csv")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not (FFMPEG_LOCATION / "ffmpeg.exe").exists():
        print(f"[ERROR] ffmpeg.exe not found at: {FFMPEG_LOCATION}")
        sys.exit(1)

    if not (FFMPEG_LOCATION / "ffprobe.exe").exists():
        print(f"[ERROR] ffprobe.exe not found at: {FFMPEG_LOCATION}")
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    with input_csv.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    required = {
        "spotify_track_id",
        "title",
        "artist",
        "youtube_video_id",
        "status",
    }

    missing = required - set(rows[0].keys()) if rows else required
    if missing:
        print(f"[ERROR] Missing columns: {sorted(missing)}")
        sys.exit(1)

    existing_log = load_existing_log()
    log = dict(existing_log)

    total = len(rows)
    print(f"\nSongs in CSV: {total}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print(f"Log file: {LOG_CSV.resolve()}\n")

    for index, row in enumerate(rows, start=1):
        spotify_id = row["spotify_track_id"]
        output_path = OUTPUT_DIR / f"{spotify_id}.wav"

        # Resume: already downloaded successfully.
        if output_path.exists() and output_path.stat().st_size > 0:
            log[spotify_id] = {
                "spotify_track_id": spotify_id,
                "title": row["title"],
                "artist": row["artist"],
                "youtube_video_id": row["youtube_video_id"],
                "youtube_title": row["youtube_title"],
                "status": "success",
                "attempts": "0",
                "output_file": str(output_path),
                "error": "",
            }
            save_log(log)
            print(f"[{index}/{total}] SKIP  {row['title']} — already downloaded")
            continue

        success, attempts, error = download_one(row, output_path)

        status = "success" if success else "failed"

        log[spotify_id] = {
            "spotify_track_id": spotify_id,
            "title": row["title"],
            "artist": row["artist"],
            "youtube_video_id": row["youtube_video_id"],
            "youtube_title": row["youtube_title"],
            "status": status,
            "attempts": str(attempts),
            "output_file": str(output_path) if success else "",
            "error": error,
        }

        save_log(log)

        if success:
            print(f"[{index}/{total}] OK    {row['title']} — {row['artist']}")
        else:
            print(f"[{index}/{total}] FAIL  {row['title']} — {row['artist']}")
            print(error[-1000:])

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    success_count = sum(
        row.get("status") == "success"
        for row in log.values()
    )
    failed_count = sum(
        row.get("status") == "failed"
        for row in log.values()
    )

    print("\n===== DOWNLOAD COMPLETE =====")
    print(f"Success: {success_count}")
    print(f"Failed:  {failed_count}")
    print(f"Total:   {len(rows)}")
    print(f"Log:     {LOG_CSV}")


if __name__ == "__main__":
    main()