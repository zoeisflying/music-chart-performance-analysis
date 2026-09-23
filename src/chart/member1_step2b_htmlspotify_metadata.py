"""
MEMBER 1 - Step 2b: Bổ sung Metadata (Album, Release Date) qua HTML công khai của Spotify.
KHÔNG CẦN SPOTIFY WEB API / KHÔNG CẦN SPOTIFY PREMIUM.

Mục đích:
  Cào trực tiếp từ trang HTML công khai https://open.spotify.com/track/<id>
  để bóc tách ngày phát hành (release_date) và tên album (album)
  cho các bài hát đã lấy mẫu (hoặc toàn bộ unique_tracks.csv).

Output:
  docs/songs_enriched.csv (hoặc songs_enriched.csv)
"""

import os
import sys
import re
import csv
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
    Bóc tách release_date và album từ trang web công khai của Spotify mà không cần API.
    """
    url = f"https://open.spotify.com/track/{track_id}"
    release_date = None
    album_name = None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. Bóc tách release_date từ thẻ meta
            meta_date = soup.find("meta", {"name": "music:release_date"})
            if meta_date and meta_date.get("content"):
                release_date = meta_date["content"].strip()
            else:
                # Dự phòng tìm trong meta description: "... Song · Artist · YYYY"
                meta_desc = soup.find("meta", {"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    parts = meta_desc["content"].split("·")
                    if len(parts) >= 3:
                        possible_year = parts[-1].strip()
                        if re.match(r"^\d{4}$", possible_year):
                            release_date = f"{possible_year}-01-01"

            # 2. Bóc tách tên Album từ thẻ link album
            album_tag = soup.find("a", href=re.compile(r"^/album/"))
            if album_tag:
                span = album_tag.find("span")
                if span and span.get_text(strip=True):
                    album_name = span.get_text(strip=True)

    except Exception:
        pass

    return release_date, album_name


def enrich_songs(input_csv=None, output_csv=None, limit=None, delay_range=(0.8, 1.5)):
    """
    Đọc danh sách bài hát và làm giàu metadata album + release_date.
    """
    # Tự động tìm file đầu vào
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

    # Tự động chọn file đầu ra
    if output_csv is None:
        if os.path.exists("docs"):
            output_csv = "docs/songs_enriched.csv"
        else:
            output_csv = "songs_enriched.csv"

    print("=" * 60)
    print("BẮT ĐẦU ENRICH METADATA QUA HTML SPOTIFY (KHÔNG CẦN API)")
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

    # Đọc tiến độ đã có nếu file output tồn tại
    seen_ids = set()
    rows_out = []
    if os.path.exists(output_csv):
        with open(output_csv, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                seen_ids.add(r["spotify_track_id"])
                rows_out.append(r)
        print(f"[*] Tìm thấy dữ liệu cũ: Đã có {len(seen_ids):,} bài trong '{output_csv}'.")

    # Mở file ghi tiếp tục
    file_exists = os.path.exists(output_csv)
    out_f = open(output_csv, "a", newline="", encoding="utf-8-sig")
    fieldnames = ["spotify_track_id", "title", "artist", "album", "release_date"]
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
        out_f.flush()

    pending = [s for s in songs if s["spotify_track_id"] not in seen_ids]
    print(f"[*] Số bài còn lại cần enrich: {len(pending):,} bài.\n")

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

            print(f"-> Date: {r_date or 'N/A'} | Album: {album or 'N/A'}")
            time.sleep(random.uniform(*delay_range))

    finally:
        out_f.close()

    print("\n" + "=" * 60)
    print(f"HOÀN THÀNH ENRICH METADATA! Lưu tại: '{output_csv}'")
    print("=" * 60)


if __name__ == "__main__":
    # Mặc định: Chạy test 5 bài nếu chạy trực tiếp
    import sys
    if "--full" in sys.argv:
        enrich_songs()
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        enrich_songs(limit=int(sys.argv[1]))
    else:
        print("=== CHẾ ĐỘ TEST: Chạy thử 5 bài đầu ===")
        print("(Để chạy toàn bộ: python member1_step2b_htmlspotify_metadata.py --full)")
        enrich_songs(limit=5)