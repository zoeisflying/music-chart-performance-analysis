import json
import csv


# =========================
# FILE PATHS
# =========================

input_file = "data/raw/lyrics_collection_results.json"
output_file = "data/raw/lyrics_missing_inventory.csv"


# =========================
# LOAD RESULTS
# =========================

with open(input_file, "r", encoding="utf-8") as f:
    results = json.load(f)


# =========================
# FIND CURRENTLY MISSING
# =========================

missing = []

for track_id, item in results.items():

    if item.get("lyrics_status") in ["not_found", "failed"]:

        sampling = item.get("sampling_provenance")

        # sampling_provenance là list
        # nên chuyển thành JSON text để lưu vào CSV
        if isinstance(sampling, list):
            sampling = json.dumps(
                sampling,
                ensure_ascii=False
            )

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


# =========================
# CSV COLUMNS
# =========================

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


# =========================
# WRITE CSV
# =========================

with open(
    output_file,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(missing)


# =========================
# SUMMARY
# =========================

not_found_count = sum(
    1
    for item in missing
    if item["lyrics_status"] == "not_found"
)

failed_count = sum(
    1
    for item in missing
    if item["lyrics_status"] == "failed"
)


print("=" * 60)
print("UPDATED MISSING INVENTORY")
print("=" * 60)

print(
    f"Total missing: {len(missing)}"
)

print(
    f"Not found: {not_found_count}"
)

print(
    f"Failed: {failed_count}"
)

print(
    f"Output: {output_file}"
)