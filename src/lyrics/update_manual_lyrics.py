import os
import json


# =========================
# CONFIG
# =========================

RESULT_FILE = os.path.join(
    "data",
    "raw",
    "lyrics_collection_results.json"
)

LYRICS_FOLDER = os.path.join(
    "data",
    "raw",
    "lyrics"
)


# =========================
# LOAD RESULTS
# =========================

def load_results():
    if not os.path.exists(RESULT_FILE):
        print("Không tìm thấy:")
        print(RESULT_FILE)
        raise SystemExit

    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# SAVE RESULTS
# =========================

def save_results(results):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# UPDATE MANUAL LYRICS
# =========================

def update_manual_lyrics():

    results = load_results()

    updated = []
    not_in_results = []
    empty_files = []

    for track_id, item in results.items():

        lyrics_file = os.path.join(
            LYRICS_FOLDER,
            f"{track_id}.txt"
        )

        # Không có file lyrics
        if not os.path.exists(lyrics_file):
            continue

        # Kiểm tra file có nội dung hay không
        with open(lyrics_file, "r", encoding="utf-8") as f:
            lyrics = f.read().strip()

        if not lyrics:
            empty_files.append(track_id)
            continue

        old_status = item.get("lyrics_status")

        # Chỉ cập nhật những bài trước đó chưa success
        if old_status != "success":

            item["source"] = "manual"
            item["lyrics_status"] = "success"
            item["collection_status"] = "success"
            item["lyrics_file"] = os.path.join(
                "data",
                "raw",
                "lyrics",
                f"{track_id}.txt"
            )

            updated.append(track_id)

    save_results(results)

    # =========================
    # PRINT SUMMARY
    # =========================

    print()
    print("=" * 60)
    print("UPDATE MANUAL LYRICS")
    print("=" * 60)

    print("Tổng số bài:", len(results))
    print("Đã cập nhật:", len(updated))
    print("File rỗng:", len(empty_files))

    print()

    if updated:
        print("Các bài vừa cập nhật:")

        for track_id in updated:
            item = results[track_id]

            print(
                f"- {item.get('title')} "
                f"| {item.get('artist')} "
                f"| {track_id}"
            )

    if empty_files:
        print()
        print("Các file rỗng:")

        for track_id in empty_files:
            print(f"- {track_id}")

    print()
    print("Đã cập nhật:")
    print(RESULT_FILE)
    print("=" * 60)


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    update_manual_lyrics()