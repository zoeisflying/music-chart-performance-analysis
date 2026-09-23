"""
MEMBER 1 - Step 3: Nạp songs_enriched.csv + chart_weekly.csv vào Supabase.

Quy trình nạp:
  1. Nạp bảng 'songs' trước (vì chart_weekly có foreign key tham chiếu đến songs.spotify_track_id).
  2. Nạp bảng 'chart_weekly' sau.

Yêu cầu cấu hình .env:
  SUPABASE_URL=https://xxxx.supabase.co
  SUPABASE_KEY=eyJh... (service_role key hoặc anon key có quyền insert)

Cài đặt thư viện:
  pip install supabase python-dotenv
"""

import os
import sys
import csv
import re
from datetime import datetime
from dotenv import load_dotenv

if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

BATCH_SIZE = 500  # Batch size tối ưu cho Supabase REST API


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Chưa cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong file .env!\n"
            "Hãy lấy URL và Key trong Supabase Dashboard -> Project Settings -> API."
        )
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def sanitize_date(date_str):
    """Chuẩn hóa ngày sang định dạng YYYY-MM-DD hoặc None nếu không hợp lệ."""
    if not date_str:
        return None
    date_str = date_str.strip().replace("/", "-")
    # Nếu chỉ có năm (VD '2022') -> chuyển thành '2022-01-01'
    if re.match(r"^\d{4}$", date_str):
        return f"{date_str}-01-01"
    # Nếu chỉ có năm và tháng (VD '2022-05') -> chuyển thành '2022-05-01'
    if re.match(r"^\d{4}-\d{2}$", date_str):
        return f"{date_str}-01"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str
    return None


def load_songs(csv_path=None):
    supabase = get_supabase_client()

    # Tìm file metadata bài hát
    if csv_path is None:
        candidates = [
            "docs/songs_enriched.csv", "docs/unique_tracks.csv", "docs/songs_master.csv",
            "songs_enriched.csv", "unique_tracks.csv", "songs_master.csv"
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                csv_path = candidate
                break


    if not csv_path or not os.path.exists(csv_path):
        print("[!] Không tìm thấy file songs CSV để nạp vào DB!")
        return

    print(f"[*] Đang đọc dữ liệu songs từ '{csv_path}'...")
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # De-duplicate theo spotify_track_id
    seen = {}
    for r in rows:
        tid = r.get("spotify_track_id", "").strip()
        if not tid or tid in seen:
            continue

        seen[tid] = {
            "spotify_track_id": tid,
            "title": r.get("title", "").strip() or "Unknown Title",
            "artist": r.get("artist", "").strip() or "Unknown Artist",
            "album": r.get("album", "").strip() or None,
            "release_date": sanitize_date(r.get("release_date")),
        }

    songs_payload = list(seen.values())
    print(f"[*] Bắt đầu upsert {len(songs_payload):,} bản ghi vào bảng 'songs'...")

    success_count = 0
    for i in range(0, len(songs_payload), BATCH_SIZE):
        batch = songs_payload[i:i + BATCH_SIZE]
        try:
            supabase.table("songs").upsert(batch, on_conflict="spotify_track_id").execute()
            success_count += len(batch)
            print(f"    -> Đã nạp batch {i + 1} đến {i + len(batch)} ({success_count:,}/{len(songs_payload):,})")
        except Exception as e:
            print(f"    [!] Lỗi khi nạp batch {i}: {e}")

    print(f"[+] Hoàn thành bảng 'songs'! Thành công: {success_count:,}/{len(songs_payload):,}\n")


def load_chart_weekly(csv_pattern="chart_weekly*.csv"):
    import glob
    matching_files = sorted(glob.glob(os.path.join("docs", csv_pattern)) if os.path.exists("docs") and glob.glob(os.path.join("docs", csv_pattern)) else glob.glob(csv_pattern))
    if not matching_files:
        print(f"[!] Không tìm thấy bất kỳ file nào khớp với '{csv_pattern}'!")
        return


    print("=" * 60)
    print(f"[*] TỰ ĐỘNG MERGE VÀ NẠP {len(matching_files)} FILE CHART WEEKLY:")
    for f in matching_files:
        print(f"    + {f}")
    print("=" * 60)

    supabase = get_supabase_client()
    payload = []
    seen_uq = set()
    total_raw_rows = 0

    for file_path in matching_files:
        print(f"[*] Đang đọc '{file_path}'...")
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            file_rows = 0
            for r in reader:
                total_raw_rows += 1
                tid = r.get("spotify_track_id", "").strip()
                mkt = r.get("market", "").strip()
                c_date = sanitize_date(r.get("chart_date"))
                if not tid or not mkt or not c_date:
                    continue

                uq_key = (tid, mkt, c_date)
                if uq_key in seen_uq:
                    continue
                seen_uq.add(uq_key)
                file_rows += 1

                try:
                    rank_val = int(r.get("rank", 0))
                    streams_val = int(r.get("streams")) if r.get("streams") else None
                except ValueError:
                    continue

                payload.append({
                    "spotify_track_id": tid,
                    "market": mkt,
                    "chart_date": c_date,
                    "rank": rank_val,
                    "streams": streams_val,
                })
            print(f"    -> Đã đọc {file_rows:,} dòng hợp lệ từ '{file_path}'")

    print(f"\n[+] Tổng số dòng thô từ tất cả các file: {total_raw_rows:,}")
    print(f"[+] Sau khi tự động lọc trùng (De-duplicate): {len(payload):,} bản ghi duy nhất!")
    print(f"[*] Bắt đầu upsert {len(payload):,} bản ghi vào bảng 'chart_weekly' trên Supabase...")

    success_count = 0
    for i in range(0, len(payload), BATCH_SIZE):
        batch = payload[i:i + BATCH_SIZE]
        try:
            supabase.table("chart_weekly").upsert(
                batch, on_conflict="spotify_track_id,market,chart_date"
            ).execute()
            success_count += len(batch)
            if (i // BATCH_SIZE) % 10 == 0 or (i + len(batch)) == len(payload):
                print(f"    -> Đã nạp batch {i + 1} đến {i + len(batch)} ({success_count:,}/{len(payload):,})")
        except Exception as e:
            print(f"    [!] Lỗi khi nạp batch {i}: {e}")

    print(f"[+] Hoàn thành bảng 'chart_weekly'! Thành công: {success_count:,}/{len(payload):,}\n")



if __name__ == "__main__":
    try:
        load_songs()
        load_chart_weekly()
        print("=" * 60)
        print("TẤT CẢ DỮ LIỆU CỦA MEMBER 1 ĐÃ ĐƯỢC NẠP LÊN SUPABASE THÀNH CÔNG!")
        print("=" * 60)
    except Exception as e:
        print(f"[!] Lỗi: {e}")
