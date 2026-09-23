"""
MEMBER 1 - Step 2b: Bổ sung Metadata (Release Date, Album) qua Spotify Embed.
KHÔNG CẦN SPOTIFY WEB API / KHÔNG CẦN TÀI KHOẢN SPOTIFY PREMIUM.

Cơ chế hoạt động:
  Spotify cung cấp trang nhúng công khai: https://open.spotify.com/embed/track/<id>
  Trang này nhúng sẵn dữ liệu JSON trong thẻ script id='__NEXT_DATA__',
  chứa đầy đủ:
    - Ngày phát hành chính thức (releaseDate -> isoString)
    - Tên bài hát chuẩn Spotify (title / name)
    - Nghệ sĩ chính thức (artists)

Output:
  docs/songs_enriched.csv (hoặc songs_enriched.csv)
"""

import os
import sys
import re
import csv
import json
import time
import random
import requests
from bs4 import BeautifulSoup

if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def get_track_metadata_from_html(track_id: str, timeout=12):
    """
    Trích xuất release_date và canonical metadata từ Spotify Embed mà không cần API.
    """
    url = f"https://open.spotify.com/embed/track/{track_id}"
    release_date = None
    album_name = None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if script and script.string:
                data = json.loads(script.string)
                entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})

                # 1. Bóc tách releaseDate
                r_date = entity.get("releaseDate")
                if isinstance(r_date, dict):
                    iso = r_date.get("isoString", "")
                    if len(iso) >= 10:
                        release_date = iso[:10]
                elif r_date:
                    release_date = str(r_date)[:10]

                # 2. Bóc tách album (nếu là album riêng, hoặc single)
                album_obj = entity.get("album")
                if isinstance(album_obj, dict):
                    album_name = album_obj.get("name")
                elif not album_name:
                    album_name = entity.get("title") or entity.get("name")

    except Exception:
        pass

    return release_date, album_name


def enrich_songs(input_csv=None, output_csv=None, limit=None, delay_range=(0.6, 1.2)):
    """
    Đọc danh sách bài hát và làm giàu metadata ngày phát hành + album.
    """
    if input_csv is None:
        candidates = [
            "docs/unique_tracks.csv", "unique_tracks.csv",
            "docs/songs_master.csv", "songs_master.csv"
        ]
        for c in candidates:
            if os.path.exists(c):
                input_csv = c
                break

    if not input_csv or not os.path.exists(input_csv):
        print(f"[!] Không tìm thấy file đầu vào. Hãy chạy Step 1 trước!")
        return

    if output_csv is None:
        output_csv = "docs/songs_enriched.csv" if os.path.exists("docs") else "songs_enriched.csv"

    print("=" * 60)
    print("BẮT ĐẦU ENRICH METADATA QUA SPOTIFY EMBED (KHÔNG CẦN API)")
    print(f"File đầu vào: {input_csv}")
    print(f"File đầu ra:  {output_csv}")
    print("=" * 60)

    with open(input_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        songs = list(reader)

    if limit:
        songs = songs[:limit]
        print(f"[*] Chế độ giới hạn: Chạy {limit} bài.")

    print(f"[*] Tổng số bài cần enrich: {len(songs):,} bài.")

    seen_ids = set()
    if os.path.exists(output_csv):
        with open(output_csv, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                seen_ids.add(r["spotify_track_id"])
        print(f"[*] Đã có {len(seen_ids):,} bài trong '{output_csv}'.")

    file_exists = os.path.exists(output_csv)
    out_f = open(output_csv, "a", newline="", encoding="utf-8-sig")
    fieldnames = ["spotify_track_id", "title", "artist", "album", "release_date"]
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
        out_f.flush()

    pending = [s for s in songs if s["spotify_track_id"] not in seen_ids]
    print(f"[*] Số bài còn lại: {len(pending):,} bài.\n")

    try:
        for i, s in enumerate(pending, 1):
            tid = s["spotify_track_id"]
            title = s.get("title", "")
            artist = s.get("artist", "")
            print(f"[{i}/{len(pending)}] {artist} - {title} ...", end=" ", flush=True)

            r_date, album = get_track_metadata_from_html(tid)
            row = {
                "spotify_track_id": tid,
                "title": title,
                "artist": artist,
                "album": album or "",
                "release_date": r_date or ""
            }
            writer.writerow(row)
            out_f.flush()

            print(f"-> Date: {r_date or 'N/A'}")
            time.sleep(random.uniform(*delay_range))

    finally:
        out_f.close()

    print("\n" + "=" * 60)
    print(f"HOÀN THÀNH ENRICH METADATA! Đã lưu tại: '{output_csv}'")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    if "--full" in sys.argv:
        enrich_songs()
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        enrich_songs(limit=int(sys.argv[1]))
    else:
        print("=== TEST NHANH 5 BÀI ===")
        enrich_songs(limit=5)