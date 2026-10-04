import csv
import os
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = Path("data/raw/audio")
LOG_CSV = Path("data/raw/audio_download_log.csv")
FFMPEG_LOCATION = Path(
    r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build-shared\bin"
)

# 7 problematic tracks with their resolved YouTube video IDs
FAILED_TRACKS_RESOLUTION = {
    "6R5fYCySNHrqo4Og6O1ppn": {
        "title": "Steal The Show",
        "artist": "Lauv",
        "youtube_video_id": "q7BmlOUk-II",
        "youtube_title": "Lauv - Steal The Show (From \"Elemental\"/Official Audio)",
        "resolution_note": "Bypassed YouTube web scraper block using player_client=android",
    },
    "3vJIaiTIHxHhYafTSPNiH4": {
        "title": "Zoo",
        "artist": "Disney",
        "youtube_video_id": "Xry6B0I3pT8",
        "youtube_title": "Shakira - Zoo (From \"Zootopia 2\") Lyric Video",
        "resolution_note": "Bypassed YouTube web scraper block using player_client=android",
    },
    "5z0LSDpPpGwc2ZyJHpsE3J": {
        "title": "Just In Case",
        "artist": "Morgan Wallen",
        "youtube_video_id": "cLnl73R9gMc",
        "youtube_title": "Morgan Wallen - Just In Case (Official Audio)",
        "resolution_note": "Bypassed YouTube 403 Forbidden streaming block using player_client=android",
    },
    "2LhXE2daNpLVv9LYXvYm8F": {
        "title": "Là Anh",
        "artist": "Phạm Lịch",
        "youtube_video_id": "Yd5FT7RaAM4",
        "youtube_title": "Phạm Lịch  Là Anh - Phạm Lịch [ Official Lyrics Video]",
        "resolution_note": "Bypassed YouTube web scraper block using player_client=android",
    },
    "11OxuU5y7ebAJyKaY8dOl0": {
        "title": "Lý Do Nào Để Quay Lại Với Nhau",
        "artist": "PAR SG",
        "youtube_video_id": "OsY3OK4bdpg",
        "youtube_title": "Ly do nao de quay lai voi nhau - PAR SG x New$oulZ",
        "resolution_note": "Bypassed YouTube web scraper block using player_client=android",
    },
    "2KLwPaRDOB87XOYAT2fgxh": {
        "title": "Pussy & Millions",
        "artist": "Drake",
        "youtube_video_id": "UCDv0tWLjDM",
        "youtube_title": "Drake & 21 Savage - Pussy & Millions ft. Travis Scott",
        "resolution_note": "Fallback to Candidate #2 (Cash Money Records) to bypass 18+ age restriction",
    },
    "4sIFi8LpJWPvI5xviWFyA6": {
        "title": "D>E>A>T>H>M>E>T>A>L",
        "artist": "Panchiko",
        "youtube_video_id": "3dPvWnEpJJI",
        "youtube_title": "DEATHMETAL",
        "resolution_note": "Replaced dead/deleted video with verified official studio release (262s)",
    },
}


def download_track(spotify_id, info):
    output_path = OUTPUT_DIR / f"{spotify_id}.wav"
    if output_path.exists() and output_path.stat().st_size > 0:
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"\n[ALREADY EXISTS] {spotify_id} | {info['artist']} - {info['title']} ({file_size_mb:.2f} MB)")
        return True, str(output_path), ""

    url = f"https://www.youtube.com/watch?v={info['youtube_video_id']}"

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ffmpeg-location",
        str(FFMPEG_LOCATION),
        "--extractor-args",
        "youtube:player_client=android",
        "--no-playlist",
        "--continue",
        "-x",
        "--audio-format",
        "wav",
        "--audio-quality",
        "0",
        "-o",
        str(output_path),
        url,
    ]

    print(f"\n[DOWNLOADING] {spotify_id} | {info['artist']} - {info['title']}")
    print(f"  URL: {url} ({info['youtube_title']})")
    print(f"  Reason: {info['resolution_note']}")

    res = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  --> SUCCESS: {output_path.name} ({file_size_mb:.2f} MB)")
        return True, str(output_path), ""
    else:
        err = res.stdout[-2000:] if res.stdout else "Unknown error"
        print(f"  --> FAILED: {err}")
        return False, "", err


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download the 7 songs
    results = {}
    for spotify_id, info in FAILED_TRACKS_RESOLUTION.items():
        success, out_file, err = download_track(spotify_id, info)
        results[spotify_id] = {
            "success": success,
            "output_file": out_file,
            "error": err,
        }
        time.sleep(1)

    # 2. Update audio_download_log.csv
    if LOG_CSV.exists():
        with LOG_CSV.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        updated_count = 0
        for r in rows:
            sid = r["spotify_track_id"]
            if sid in results and results[sid]["success"]:
                r["youtube_video_id"] = FAILED_TRACKS_RESOLUTION[sid]["youtube_video_id"]
                r["youtube_title"] = FAILED_TRACKS_RESOLUTION[sid]["youtube_title"]
                r["status"] = "success"
                r["attempts"] = str(int(r.get("attempts", "1") or "1") + 1)
                r["output_file"] = results[sid]["output_file"]
                r["error"] = ""
                updated_count += 1

        with LOG_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\n[LOG UPDATED] Successfully updated {updated_count}/7 records in {LOG_CSV}")


if __name__ == "__main__":
    main()
