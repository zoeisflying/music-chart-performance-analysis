"""
MEMBER 1 - Step 1: Crawl Kworb "weekly totals" page for VN, US, KR.

Mục đích: Lấy danh sách TOÀN BỘ bài hát từng có mặt trên Spotify weekly chart
của mỗi thị trường (VN, US, KR) từ Kworb.
Mỗi bài trích xuất sẵn: spotify_track_id, artist, title, market,
lifetime_wks, lifetime_top10_wks, peak_rank, peak_streams, total_streams.

Output:
  - songs_master.csv: Chứa toàn bộ record (1 dòng / bài hát / thị trường)
  - unique_tracks.csv: Danh sách các spotify_track_id duy nhất để phục vụ Step 2

Cài đặt thư viện:
  pip install requests beautifulsoup4
"""

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


MARKETS = {
    "VN": "https://kworb.net/spotify/country/vn_weekly_totals.html",
    "US": "https://kworb.net/spotify/country/us_weekly_totals.html",
    "KR": "https://kworb.net/spotify/country/kr_weekly_totals.html",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# Link bài hát trên Kworb có dạng "../track/<spotify_track_id>.html"
TRACK_ID_RE = re.compile(r"track/([A-Za-z0-9]+)\.html")


def fetch_totals_page(url: str) -> BeautifulSoup:
    """Tải HTML trang totals của 1 thị trường và parse qua BeautifulSoup."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"  # Sửa lỗi font: Kworb trả về header thiếu charset khiến requests mặc định ISO-8859-1
    return BeautifulSoup(resp.text, "html.parser")



def parse_totals_table(soup: BeautifulSoup, market: str):
    """
    Kworb totals page layout:
      Bảng chứa các cột:
      Artist and Title | Wks | T10 | Pk | (x?) | PkStreams | Total
      Cột "Artist and Title" chứa các thẻ <a>: artist link và track link (ở cuối).
    """
    rows_out = []
    table = soup.find("table")
    if table is None:
        raise RuntimeError(f"Không tìm thấy table nào trên trang {market} - kiểm tra kết nối/chặn IP.")

    trs = table.find_all("tr")
    for tr in trs[1:]:  # Bỏ header row
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue

        artist_title_cell = cells[0]
        links = artist_title_cell.find_all("a")
        if not links:
            continue

        track_link = links[-1]  # Link cuối cùng trong cell là bài hát
        track_href = track_link.get("href", "")
        m = TRACK_ID_RE.search(track_href)
        if not m:
            continue
        track_id = m.group(1)

        title = track_link.get_text(strip=True)
        artist = links[0].get_text(strip=True) if len(links) > 1 else ""

        def clean_num(text):
            t = text.strip().replace(",", "")
            return int(t) if t.isdigit() else None

        wks = clean_num(cells[1].get_text())
        t10 = clean_num(cells[2].get_text())
        peak_rank = clean_num(cells[3].get_text())
        peak_streams = clean_num(cells[5].get_text())
        total_streams = clean_num(cells[6].get_text()) if len(cells) > 6 else None

        rows_out.append({
            "spotify_track_id": track_id,
            "artist": artist,
            "title": title,
            "market": market,
            "lifetime_wks": wks,
            "lifetime_top10_wks": t10,
            "peak_rank": peak_rank,
            "peak_streams": peak_streams,
            "total_streams": total_streams,
        })
    return rows_out


def crawl_all_markets(output_master="songs_master.csv", output_unique="unique_tracks.csv"):
    import os
    if os.path.exists("docs") and not os.path.dirname(output_master):
        output_master = os.path.join("docs", output_master)
    if os.path.exists("docs") and not os.path.dirname(output_unique):
        output_unique = os.path.join("docs", output_unique)

    all_rows = []
    print("=" * 60)
    print("BẮT ĐẦU CRAWL KWORB TOTALS CHO 3 THỊ TRƯỜNG: VN, US, KR")
    print("=" * 60)


    for market, url in MARKETS.items():
        print(f"\n[*] Đang crawl {market} từ: {url}")
        try:
            soup = fetch_totals_page(url)
            rows = parse_totals_table(soup, market)
            print(f"    -> Lấy thành công: {len(rows):,} bài cho thị trường {market}")
            all_rows.extend(rows)
        except Exception as e:
            print(f"    [!] Lỗi khi crawl {market}: {e}")
        time.sleep(random.uniform(2.0, 3.5))

    if not all_rows:
        print("\n[!] Không lấy được dữ liệu nào! Hãy kiểm tra lại kết nối mạng.")
        return

    # 1. Lưu songs_master.csv (đầy đủ các thị trường)
    keys = list(all_rows[0].keys())
    with open(output_master, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n[+] Đã lưu toàn bộ {len(all_rows):,} dòng vào '{output_master}'")

    # 2. Tạo danh sách unique tracks để Member 1 crawl trang con ở Step 2
    unique_tracks = {}
    for r in all_rows:
        tid = r["spotify_track_id"]
        if tid not in unique_tracks:
            unique_tracks[tid] = {
                "spotify_track_id": tid,
                "title": r["title"],
                "artist": r["artist"],
                "markets": set(),
                "max_wks": 0
            }
        unique_tracks[tid]["markets"].add(r["market"])
        if r["lifetime_wks"] and r["lifetime_wks"] > unique_tracks[tid]["max_wks"]:
            unique_tracks[tid]["max_wks"] = r["lifetime_wks"]

    unique_list = [
        {
            "spotify_track_id": tid,
            "title": v["title"],
            "artist": v["artist"],
            "markets": ",".join(sorted(v["markets"])),
            "max_wks": v["max_wks"]
        }
        for tid, v in unique_tracks.items()
    ]
    # Sắp xếp theo độ hot (max_wks giảm dần) để các bài hot được crawl trước
    unique_list.sort(key=lambda x: x["max_wks"], reverse=True)

    with open(output_unique, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["spotify_track_id", "title", "artist", "markets", "max_wks"])
        writer.writeheader()
        writer.writerows(unique_list)

    print(f"[+] Đã lưu {len(unique_list):,} bài duy nhất (unique tracks) vào '{output_unique}'")
    print("=" * 60)
    print("HOÀN THÀNH STEP 1!")
    print("BƯỚC TIẾP THEO: Chạy 'member1_step2_kworb_track_history.py' để lấy dữ liệu weekly chart.")
    print("=" * 60)


if __name__ == "__main__":
    crawl_all_markets()
