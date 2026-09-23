"""
MEMBER 1 - Step 2b: Bổ sung Metadata (Release Date, Album) qua Spotify Embed.
Dành riêng cho tập mẫu phân tầng của Member 4 (sample_list_v1.csv).

Tối ưu hóa:
  - Sử dụng ThreadPoolExecutor (4 workers) để hoàn thành ~1,912 bài chỉ trong 5-7 phút.
  - Tự động lưu tiến độ vào file CSV, hỗ trợ Resume nếu bị gián đoạn.
  - Tự động cập nhật trực tiếp lên bảng 'songs' trên Supabase.

Cài đặt / Yêu cầu:
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


def fetch_track_spotify_embed(track_id: str, max_retries=2, timeout=8):
    """
    Trích xuất release_date và album name từ trang nhúng công khai của Spotify.
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

                    # Bóc tách releaseDate
                    release_date = None
                    r_date = entity.get("releaseDate")
                    if isinstance(r_date, dict):
                        iso = r_date.get("isoString", "")
                        if len(iso) >= 10:
                            release_date = iso[:10]
                    elif r_date:
                        release_date = str(r_date)[:10]

                    # Bóc tách album (nếu có đối tượng album riêng)
                    album_name = None
                    album_obj = entity.get("album")
                    if isinstance(album_obj, dict):
                        album_name = album_obj.get("name")
                    
                    return track_id, release_date, album_name
            elif resp.status_code == 404:
                return track_id, None, None
        except Exception:
            time.sleep(0.5 * (attempt + 1))

    return track_id, None, None


def enrich_sample_list(input_csv="data/processed/sample_list_v1.csv",
                       output_csv="data/processed/sample_list_v1_enriched.csv",
                       max_workers=4):
    """
    Enrich danh sách bài hát của Member 4 với release_date và album.
    """
    if not os.path.exists(input_csv):
        print(f"[!] Không tìm thấy '{input_csv}'. Hãy kiểm tra lại đường dẫn!")
        return

    print("=" * 65)
    print("BẮT ĐẦU ENRICH RELEASE_DATE CHO SAMPLE LIST CỦA MEMBER 4")
    print(f"File đầu vào: {input_csv}")
    print(f"File đầu ra:  {output_csv}")
    print(f"Số luồng song song: {max_workers} workers")
    print("=" * 65)

    with open(input_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        fieldnames = list(reader.fieldnames)

    # Thêm 2 cột mới nếu chưa có
    if "release_date" not in fieldnames:
        fieldnames.append("release_date")
    if "album" not in fieldnames:
        fieldnames.append("album")

    # Lấy danh sách unique track_ids
    unique_ids = list(dict.fromkeys(r["spotify_track_id"] for r in all_rows if r.get("spotify_track_id")))
    print(f"[*] Tổng số dòng trong sample_list: {len(all_rows):,}")
    print(f"[*] Số lượng bài hát duy nhất cần enrich: {len(unique_ids):,}")

    # Đọc cache nếu đã có dữ liệu trước đó
    meta_cache = {}
    if os.path.exists(output_csv):
        with open(output_csv, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                tid = r.get("spotify_track_id")
                if tid and r.get("release_date"):
                    meta_cache[tid] = (r.get("release_date"), r.get("album"))
        print(f"[*] Đã tìm thấy cache: {len(meta_cache):,} bài đã có metadata.")

    pending_ids = [tid for tid in unique_ids if tid not in meta_cache]
    print(f"[*] Số bài còn lại cần cào: {len(pending_ids):,} bài.")

    if pending_ids:
        print(f"[*] Đang cào song song với {max_workers} luồng (dự kiến ~5-7 phút)...")
        completed_count = 0
        t0 = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tid = {executor.submit(fetch_track_spotify_embed, tid): tid for tid in pending_ids}
            for future in as_completed(future_to_tid):
                tid, r_date, album = future.result()
                meta_cache[tid] = (r_date, album)
                completed_count += 1

                if completed_count % 50 == 0 or completed_count == len(pending_ids):
                    elapsed = time.time() - t0
                    speed = completed_count / elapsed if elapsed > 0 else 0
                    print(f"    -> Đã cào: {completed_count:,}/{len(pending_ids):,} bài "
                          f"({completed_count/len(pending_ids)*100:.1f}%) | "
                          f"Tốc độ: {speed:.1f} bài/s | Vừa lấy: {tid} -> {r_date or 'N/A'}")

    # Ghi dữ liệu đầy đủ ra file enriched
    print(f"\n[*] Đang ghi toàn bộ kết quả vào '{output_csv}'...")
    enriched_rows = []
    for r in all_rows:
        tid = r.get("spotify_track_id")
        r_date, album = meta_cache.get(tid, (None, None))
        r["release_date"] = r_date or ""
        r["album"] = album or ""
        enriched_rows.append(r)

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    print(f"[+] Đã lưu thành công {len(enriched_rows):,} dòng vào '{output_csv}'!")

    # Cập nhật lên Supabase bảng 'songs'
    if SUPABASE_URL and SUPABASE_KEY:
        print("\n[*] Đang cập nhật metadata mới vào bảng 'songs' trên Supabase...")
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

            # Chuẩn bị payload unique bài hát có release_date
            update_payload = []
            for tid in unique_ids:
                r_date, album = meta_cache.get(tid, (None, None))
                if r_date:
                    update_payload.append({
                        "spotify_track_id": tid,
                        "release_date": r_date,
                        "album": album or None
                    })

            batch_size = 500
            for i in range(0, len(update_payload), batch_size):
                batch = update_payload[i:i + batch_size]
                supabase.table("songs").upsert(batch, on_conflict="spotify_track_id").execute()
                print(f"    -> Đã update Supabase batch {i + 1} đến {i + len(batch)}")

            print(f"[+] Cập nhật thành công {len(update_payload):,} bài vào bảng 'songs' trên Supabase!")
        except Exception as e:
            print(f"[!] Lỗi khi update Supabase: {e}")

    print("=" * 65)
    print("HOÀN THÀNH STEP 2B CHO SAMPLE LIST CỦA MEMBER 4!")
    print("=" * 65)


if __name__ == "__main__":
    enrich_sample_list()