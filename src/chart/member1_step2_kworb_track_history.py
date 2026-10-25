"""
MEMBER 1 - Step 2: Crawl per-track Kworb page for weekly chart history.

Đặc điểm cấu trúc trang Kworb track:
  URL: https://kworb.net/spotify/track/<id>.html
  - Table 0: Bảng WEEKLY (mốc thời gian cách nhau 7 ngày).
  - Cột của Table 0 chính là các thị trường: Date, Global, VN, US, KR, v.v.
  - Một request duy nhất cho 1 track_id sẽ lấy đồng thời lịch sử của cả VN, US và KR!

Cơ chế an toàn (Fault Tolerance):
  - Checkpoint & Resume: Ghi nhớ các track_id đã crawl vào 'crawled_track_ids.txt'.
    Nếu bị ngắt kết nối hoặc dừng giữa chừng, khi chạy lại script sẽ TỰ ĐỘNG bỏ qua các bài đã xong.
  - Append trực tiếp vào 'chart_weekly.csv': Dữ liệu được ghi ngay tức thì, không lo mất nếu crash.
  - Filter thời gian: Chỉ lấy các tuần từ 2021-01-01 trở đi (đúng phạm vi 2021-2026 của đề tài).

Cài đặt thư viện:
  pip install requests beautifulsoup4
"""

import os
import sys
import re
import csv
import time
import random
from datetime import datetime
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

TRACK_URL_TMPL = "https://kworb.net/spotify/track/{track_id}.html"
DATE_RE = re.compile(r"^\d{4}/\d{2}/\d{2}$")
POS_STREAMS_RE = re.compile(r"^(\d+)\s*\(([\d,]+)\)$")

TARGET_MARKETS = ["VN", "US", "KR"]
MIN_CHART_DATE = "2021/01/01"  # Phạm vi đề tài: 2021-2026


def fetch_track_page(track_id: str, max_retries=3) -> BeautifulSoup:
    url = TRACK_URL_TMPL.format(track_id=track_id)
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 * (attempt + 1))
    return None


def is_weekly_table(trs):
    """Kiểm tra xem table có phải là weekly table không (khoảng cách 2 dòng đầu ~7 ngày)."""
    dates = []
    for tr in trs[1:]:
        cells = tr.find_all("td")
        if not cells:
            continue
        d_text = cells[0].get_text(strip=True)
        if DATE_RE.match(d_text):
            dates.append(d_text)
            if len(dates) == 2:
                break
    if len(dates) < 2:
        return False
    try:
        d0 = datetime.strptime(dates[0], "%Y/%m/%d")
        d1 = datetime.strptime(dates[1], "%Y/%m/%d")
        return abs((d1 - d0).days) >= 6
    except Exception:
        return False


def parse_track_weekly_data(track_id: str, soup: BeautifulSoup):
    """
    Tìm bảng weekly và bóc tách dữ liệu cho VN, US, KR.
    Trả về list dict các bản ghi: spotify_track_id, market, chart_date, rank, streams.
    """
    if soup is None:
        return []

    tables = soup.find_all("table")
    weekly_table = None

    for t in tables:
        trs = t.find_all("tr")
        if not trs:
            continue
        headers = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]
        if "Date" in headers and is_weekly_table(trs):
            weekly_table = t
            break

    if weekly_table is None:
        return []

    trs = weekly_table.find_all("tr")
    headers = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]

    # Xác định vị trí cột của VN, US, KR
    market_indices = {}
    for mkt in TARGET_MARKETS:
        if mkt in headers:
            market_indices[mkt] = headers.index(mkt)

    if not market_indices:
        return []

    records = []
    for tr in trs[1:]:
        cells = tr.find_all("td")
        if not cells:
            continue

        date_str = cells[0].get_text(strip=True)
        if not DATE_RE.match(date_str):
            continue

        # Lọc phạm vi từ 2021 trở đi
        if date_str < MIN_CHART_DATE:
            continue

        for mkt, col_idx in market_indices.items():
            if col_idx >= len(cells):
                continue
            val = cells[col_idx].get_text(strip=True)
            if val == "--" or not val:
                continue  # Tuần đó bài hát không chart ở market này

            m = POS_STREAMS_RE.match(val)
            if m:
                rank = int(m.group(1))
                streams = int(m.group(2).replace(",", ""))
                records.append({
                    "spotify_track_id": track_id,
                    "market": mkt,
                    "chart_date": date_str.replace("/", "-"),  # format YYYY-MM-DD
                    "rank": rank,
                    "streams": streams,
                })

    return records


def crawl_chart_history(input_file="unique_tracks.csv",
                        output_csv="chart_weekly.csv",
                        checkpoint_file="crawled_track_ids.txt",
                        test_limit=None,
                        sleep_range=(1.2, 2.5)):
    """
    Crawl lịch sử chart của từng bài hát với cơ chế checkpoint/resume.
    """
    # 1. Đọc danh sách bài cần crawl
    if not os.path.exists(input_file):
        candidates = [
            os.path.join("docs", input_file),
            "songs_master.csv",
            os.path.join("docs", "songs_master.csv")
        ]
        for c in candidates:
            if os.path.exists(c):
                input_file = c
                break
        else:
            print(f"[!] Không tìm thấy file '{input_file}'. Hãy chạy Step 1 trước!")
            return


    with open(input_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_songs = list(reader)

    # Lấy unique IDs theo thứ tự
    unique_ids = []
    seen = set()
    for s in all_songs:
        tid = s["spotify_track_id"]
        if tid not in seen:
            seen.add(tid)
            unique_ids.append((tid, s.get("title", ""), s.get("artist", "")))

    # 2. Đọc checkpoint đã crawl trước đó
    crawled_ids = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            crawled_ids = set(line.strip() for line in f if line.strip())
        print(f"[*] Tìm thấy checkpoint: Đã có {len(crawled_ids):,} bài đã crawl trước đó.")

    # Khởi tạo file output_csv nếu chưa có
    file_exists = os.path.exists(output_csv)
    fieldnames = ["spotify_track_id", "market", "chart_date", "rank", "streams"]

    out_f = open(output_csv, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(out_f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
        out_f.flush()

    ckpt_f = open(checkpoint_file, "a", encoding="utf-8")

    # Lọc danh sách bài chưa crawl
    pending = [item for item in unique_ids if item[0] not in crawled_ids]
    if test_limit:
        pending = pending[:test_limit]
        print(f"[*] ĐANG CHẠY TEST: Giới hạn {test_limit} bài.")

    print(f"[*] Tổng bài cần crawl: {len(pending):,} bài.")
    total_records = 0

    try:
        for i, (tid, title, artist) in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] Track: {tid} | {artist} - {title} ...", end=" ", flush=True)
            try:
                soup = fetch_track_page(tid)
                records = parse_track_weekly_data(tid, soup)

                if records:
                    writer.writerows(records)
                    out_f.flush()
                    total_records += len(records)
                    mkts = set(r["market"] for r in records)
                    print(f"-> {len(records)} tuần (Markets: {','.join(mkts)})")
                else:
                    print("-> 0 tuần (không chart VN/US/KR sau 2021 hoặc lỗi)")

                # Lưu checkpoint
                ckpt_f.write(f"{tid}\n")
                ckpt_f.flush()

            except Exception as e:
                print(f"-> [!] Lỗi: {e}")

            time.sleep(random.uniform(*sleep_range))

    finally:
        out_f.close()
        ckpt_f.close()

    print("\n" + "=" * 60)
    print(f"HOÀN THÀNH ĐỢT CRAWL! Ghi nhận thêm {total_records:,} dòng vào '{output_csv}'")
    print(f"Checkpoint lưu tại '{checkpoint_file}'.")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    # Nếu truyền tham số --full từ terminal: python member1_step2_kworb_track_history.py --full
    # Mặc định: Chạy test 5 bài trước để người dùng kiểm chứng
    if "--full" in sys.argv:
        print("=== BẮT ĐẦU CHẠY TOÀN BỘ DANH SÁCH ===")
        crawl_chart_history()
    else:
        print("=== CHẾ ĐỘ TEST: Crawl thử 5 bài đầu tiên ===")
        print("(Để chạy toàn bộ sau khi test, chạy: python member1_step2_kworb_track_history.py --full)\n")
        crawl_chart_history(test_limit=5)
