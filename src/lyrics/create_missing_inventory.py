import json
import csv

# Đọc file kết quả lyrics
input_file = "data/raw/lyrics_collection_results.json"
output_file = "data/raw/lyrics_missing_inventory.csv"

with open(input_file, "r", encoding="utf-8") as f:
    results = json.load(f)

# Chỉ lấy những bài chưa có lyrics
missing = []

for track_id, item in results.items():
    if item.get("lyrics_status") in ["not_found", "failed"]:
        sampling = item.get("sampling_provenance")

        if isinstance(sampling, list):
            sampling = json.dumps(sampling, ensure_ascii=False)

        missing.append({
            "spotify_track_id": item.get("spotify_track_id"),
            "title": item.get("title"),
            "artist": item.get("artist"),
            "lyrics_status": item.get("lyrics_status"),
            "collection_status": item.get("collection_status"),
            "source": item.get("source"),
            "genius_url": item.get("genius_url"),
            "language": item.get("language"),
            "release_date": item.get("release_date"),
            "album": item.get("album"),
            "sampling_provenance": sampling
        })

# Ghi CSV
fieldnames = [
    "spotify_track_id",
    "title",
    "artist",
    "lyrics_status",
    "collection_status",
    "source",
    "genius_url",
    "language",
    "release_date",
    "album",
    "sampling_provenance"
]

with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(missing)

print("Đã tạo:", output_file)
print("Tổng số bài missing:", len(missing))