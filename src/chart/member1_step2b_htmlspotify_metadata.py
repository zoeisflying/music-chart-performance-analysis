"""
MEMBER 1 - Step 2b: Bổ sung Metadata (Release Date, Album) qua Spotify Embed.
LẤY DANH SÁCH BÀI MẪU TRỰC TIẾP TỪ BẢNG 'song_quarter_sampling' TRÊN SUPABASE.

Quy trình:
  1. Kết nối Supabase -> Đọc toàn bộ 2,760 dòng mẫu từ bảng 'song_quarter_sampling'.
  2. Lọc ra 1,912 bài hát duy nhất (unique spotify_track_ids).
  3. Cào song song đa luồng (5 workers) qua trang Spotify Embed (KHÔNG CẦN API / PREMIUM).
  4. Lưu tiến độ liên tục vào 'data/processed/sample_songs_enriched.csv' (chống rớt mạng).
  5. Upsert ngược trực tiếp vào bảng 'songs' trên Supabase.

Cài đặt thư viện:
  pip install requests beautifulsoup4 supabase python-dotenv
"""

import os
import sys
import re
import csv
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Chưa cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong file .env!")
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_track_spotify_embed(track_id: str, max_retries=2, timeout=8):
    """
    Trích xuất release_date và album từ trang nhúng công khai của Spotify.
    """
    url = f"https://open.spotify.com/embed/track/{track_id}"
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                script = soup.find("script", id="__NEXT_DATA__")
                if script and script.string:
                    data = json.loads(script.string)
                    entity = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})

                    # 1. Bóc tách releaseDate
                    release_date = None
                    r_date = entity.get("releaseDate")
                    if isinstance(r_date, dict):
                        iso = r_date.get("isoString", "")
                        if len(iso) >= 10:
                            release_date = iso[:10]
                    elif r_date:
                        release_date = str(r_date)[:10]

                    # 2. Bóc tách album
                    album_name = None
                    album_obj = entity.get("album")
                    if isinstance(album_obj, dict):
                        album_name = album_obj.get("name")
                    
                    return track_id, release_date, album_name
            elif resp.status_code == 404:
                return track_id, None, None
        except Exception:
            time.sleep(0.4 * (attempt + 1))

    return track_id, None, None


def enrich_from_supabase_sampling(output_csv="data/processed/sample_songs_enriched.csv", max_workers=5):
    supabase = get_supabase()
    print("=" * 65)
    print("BẮT ĐẦU STEP 2B: ENRICH METADATA TỪ SUPABASE (BẢNG song_quarter_sampling)")
    print(f"Số luồng cào song song: {max_workers} workers")
    print("=" * 65)

    # 1. Đọc danh sách từ Supabase song_quarter_sampling
    print("[*] Đang kết nối Supabase và tải danh sách bài hát từ 'song_quarter_sampling'...")
    all_rows = []
    page = 0
    page_size = 1000
    while True:
        res = supabase.table("song_quarter_sampling").select("*").range(page * page_size, (page + 1) * page_size - 1).execute()
        if not res.data:
            break
        all_rows.extend(res.data)
        if len(res.data) < page_size:
            break
        page += 1

    print(f"[+] Đã tải thành công {len(all_rows):,} bản ghi mẫu từ Supabase!")

    # Lấy danh sách unique track IDs
    unique_ids = list(dict.fromkeys(r["spotify_track_id"] for r in all_rows if r.get("spotify_track_id")))
    print(f"[+] Lọc ra được {len(unique_ids):,} bài hát DUY NHẤT cần enrich metadata.")

    # 2. Đọc cache nếu file CSV đầu ra đã có dữ liệu trước đó
    meta_cache = {}
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    if os.path.exists(output_csv):
        with open(output_csv, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                tid = r.get("spotify_track_id")
                if tid and r.get("release_date"):
                    meta_cache[tid] = (r.get("release_date"), r.get("album"))
        print(f"[*] Đã tìm thấy cache: {len(meta_cache):,} bài đã có metadata trước đó.")

    pending_ids = [tid for tid in unique_ids if tid not in meta_cache]
    print(f"[*] Số bài còn lại cần cào: {len(pending_ids):,} bài.")

    # 3. Cào song song qua Spotify Embed
    if pending_ids:
        print(f"[*] Bắt đầu cào song song với {max_workers} luồng (dự kiến ~5 phút)...")
        completed_count = 0
        t0 = time.time()

        # Mở file append để ghi nhận ngay khi có kết quả
        file_exists = os.path.exists(output_csv)
        out_f = open(output_csv, "a", newline="", encoding="utf-8-sig")
        writer = csv.DictWriter(out_f, fieldnames=["spotify_track_id", "release_date", "album"])
        if not file_exists:
            writer.writeheader()
            out_f.flush()

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_tid = {executor.submit(fetch_track_spotify_embed, tid): tid for tid in pending_ids}
                for future in as_completed(future_to_tid):
                    tid, r_date, album = future.result()
                    meta_cache[tid] = (r_date, album)
                    writer.writerow({
                        "spotify_track_id": tid,
                        "release_date": r_date or "",
                        "album": album or ""
                    })
                    out_f.flush()
                    completed_count += 1

                    if completed_count % 50 == 0 or completed_count == len(pending_ids):
                        elapsed = time.time() - t0
                        speed = completed_count / elapsed if elapsed > 0 else 0
                        percent = (completed_count / len(pending_ids)) * 100
                        print(f"    -> Đã cào: {completed_count:,}/{len(pending_ids):,} bài ({percent:.1f}%) | Tốc độ: {speed:.1f} bài/s")
        finally:
            out_f.close()

    print(f"\n[+] Đã hoàn thành cào metadata! Lưu backup tại: '{output_csv}'")

    # 4. Upsert trực tiếp vào bảng 'songs' trên Supabase
    print("\n[*] Đang nạp cập nhật 'release_date' và 'album' vào bảng 'songs' trên Supabase...")
    song_info = {}
    candidate_paths = [
        "data/raw/chart/unique_tracks.csv", "data/raw/chart/songs_master.csv",
        "docs/unique_tracks.csv", "unique_tracks.csv"
    ]
    for c in candidate_paths:
        if os.path.exists(c):
            with open(c, encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    song_info[r["spotify_track_id"]] = (r.get("title", ""), r.get("artist", ""))
            break

    update_payload = []
    for tid in unique_ids:
        r_date, album = meta_cache.get(tid, (None, None))
        if r_date:
            title, artist = song_info.get(tid, ("Unknown Title", "Unknown Artist"))
            update_payload.append({
                "spotify_track_id": tid,
                "title": title,
                "artist": artist,
                "release_date": r_date,
                "album": album or None
            })


    batch_size = 500
    success_count = 0
    for i in range(0, len(update_payload), batch_size):
        batch = update_payload[i:i + batch_size]
        try:
            supabase.table("songs").upsert(batch, on_conflict="spotify_track_id").execute()
            success_count += len(batch)
            print(f"    -> Đã cập nhật Supabase batch {i + 1} đến {i + len(batch)} ({success_count:,}/{len(update_payload):,})")
        except Exception as e:
            print(f"    [!] Lỗi khi nạp batch {i}: {e}")

    print("\n" + "=" * 65)
    print(f"HOÀN THÀNH TOÀN BỘ STEP 2B! ĐÃ CẬP NHẬT {success_count:,} BÀI VÀO BẢNG 'songs'!")
    print("=" * 65)


if __name__ == "__main__":
    enrich_from_supabase_sampling()