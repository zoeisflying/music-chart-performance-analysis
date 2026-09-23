import os
import sys
import csv
import time
import random
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
DATE_RE = re.compile(r"^\d{4}/\d{2}/\d{2}$")
POS_STREAMS_RE = re.compile(r"^(\d+)\s*\(([\d,]+)\)$")
TARGET_MARKETS = ["VN", "US", "KR"]
MIN_CHART_DATE = "2021/01/01"

def fetch_page(track_id):
    url = f"https://kworb.net/spotify/track/{track_id}.html"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=25)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None

def parse_data(track_id, soup):
    if not soup:
        return []
    tables = soup.find_all("table")
    weekly_table = None
    for t in tables:
        trs = t.find_all("tr")
        if not trs:
            continue
        headers = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]
        if "Date" in headers:
            weekly_table = t
            break
    if not weekly_table:
        return []

    trs = weekly_table.find_all("tr")
    headers = [c.get_text(strip=True) for c in trs[0].find_all(["th", "td"])]
    market_indices = {m: headers.index(m) for m in TARGET_MARKETS if m in headers}
    if not market_indices:
        return []

    records = []
    for tr in trs[1:]:
        cells = tr.find_all("td")
        if not cells:
            continue
        d_str = cells[0].get_text(strip=True)
        if not DATE_RE.match(d_str) or d_str < MIN_CHART_DATE:
            continue
        for mkt, idx in market_indices.items():
            if idx >= len(cells):
                continue
            val = cells[idx].get_text(strip=True)
            m = POS_STREAMS_RE.match(val)
            if m:
                records.append({
                    "spotify_track_id": track_id,
                    "market": mkt,
                    "chart_date": d_str.replace("/", "-"),
                    "rank": int(m.group(1)),
                    "streams": int(m.group(2).replace(",", ""))
                })
    return records

def start_worker2():
    input_file = "unique_tracks.csv" if os.path.exists("unique_tracks.csv") else "songs_master.csv"
    with open(input_file, encoding="utf-8-sig") as f:
        unique_ids = []
        seen = set()
        for r in csv.DictReader(f):
            tid = r["spotify_track_id"]
            if tid not in seen:
                seen.add(tid)
                unique_ids.append((tid, r.get("title", ""), r.get("artist", "")))

    # Chỉ lấy nửa sau: từ bài 7501 đến hết
    target = unique_ids[7500:]
    output_csv = "chart_weekly_part2.csv"
    ckpt_file = "crawled_track_ids_part2.txt"

    crawled = set()
    if os.path.exists(ckpt_file):
        with open(ckpt_file, encoding="utf-8") as f:
            crawled = set(line.strip() for line in f if line.strip())

    file_exists = os.path.exists(output_csv)
    out_f = open(output_csv, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(out_f, fieldnames=["spotify_track_id", "market", "chart_date", "rank", "streams"])
    if not file_exists:
        writer.writeheader()
        out_f.flush()

    ckpt_f = open(ckpt_file, "a", encoding="utf-8")
    pending = [x for x in target if x[0] not in crawled]

    print(f"=== WORKER 2 (Thonny): Chạy nửa sau ===")
    print(f"[*] Tổng bài cần cào: {len(pending):,} bài.")

    try:
        for i, (tid, title, artist) in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] Track: {tid} | {artist} - {title} ...", end=" ", flush=True)
            try:
                soup = fetch_page(tid)
                records = parse_data(tid, soup)
                if records:
                    writer.writerows(records)
                    out_f.flush()
                    print(f"-> {len(records)} tuần")
                else:
                    print("-> 0 tuần")
                ckpt_f.write(f"{tid}\n")
                ckpt_f.flush()
            except Exception as e:
                print(f"-> Lỗi: {e}")
            time.sleep(random.uniform(1.2, 2.5))
    finally:
        out_f.close()
        ckpt_f.close()

if __name__ == "__main__":
    start_worker2()