import os
import json
import csv

RESULT_FILE = os.path.join("data", "raw", "lyrics_collection_results.json")
OUTPUT_FILE = os.path.join("data", "processed", "lyrics_status.csv")


def load_results():
    if not os.path.exists(RESULT_FILE):
        print("Không tìm thấy:")
        print(RESULT_FILE)
        raise SystemExit
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def create_handoff():
    results = load_results()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    fieldnames = [
        "spotify_track_id", "title", "artist", "language",
        "source", "lyrics_status", "collection_status", "lyrics_file"
    ]

    rows = []
    for track_id, item in results.items():
        rows.append({
            "spotify_track_id": track_id,
            "title": item.get("title", ""),
            "artist": item.get("artist", ""),
            "language": item.get("language", ""),
            "source": item.get("source", ""),
            "lyrics_status": item.get("lyrics_status", ""),
            "collection_status": item.get("collection_status", ""),
            "lyrics_file": item.get("lyrics_file", ""),
        })

    rows.sort(key=lambda x: x["spotify_track_id"])

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    success = sum(1 for row in rows if row["lyrics_status"] == "success")
    not_found = sum(1 for row in rows if row["lyrics_status"] == "not_found")
    failed = sum(1 for row in rows if row["lyrics_status"] == "failed")

    print("\nLYRICS HANDOFF CREATED")
    print(f"Total tracks: {len(rows)}")
    print(f"Lyrics success: {success}")
    print(f"Not found: {not_found}")
    print(f"Failed: {failed}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_handoff()
