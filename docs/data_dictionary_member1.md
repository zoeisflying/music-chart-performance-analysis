# DATA DICTIONARY & HANDOFF REPORT — MEMBER 1
## Pipeline: Chart Data Collection & Song Metadata (VN - US - KR, 2021–2026)

---

### 1. Giới thiệu tổng quan
Member 1 chịu trách nhiệm xây dựng pipeline thu thập dữ liệu Spotify Weekly Chart từ Kworb và chuẩn hóa Song Metadata từ Spotify API cho 3 thị trường:
- **Việt Nam (VN)**
- **Mỹ (US)**
- **Hàn Quốc (KR)**
- **Khung thời gian**: 2021 đến hiện tại (2026).

Stable Song Identifier duy nhất xuyên suốt toàn bộ đề tài là **`spotify_track_id`**.

---

### 2. Data Dictionary

#### Bảng: `songs` (Song-level Entity)
- **Grain**: 1 dòng = 1 bài hát duy nhất (Universal song registry).
- **Mục đích**: Là bảng gốc (Parent table) liên kết khóa ngoại với tất cả các bảng khác (`chart_weekly`, `youtube_mapping`, `song_quarter_sampling`, `lyrics_features`, `audio_features`, `chart_performance`).

| Column Name | Data Type | Constraint | Description | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `spotify_track_id` | `TEXT` | `PRIMARY KEY` | Định danh chuẩn duy nhất 22 ký tự từ Spotify | `2HRgqmZQC0MC7GeNuDIXHN` |
| `title` | `TEXT` | `NOT NULL` | Tên bài hát chuẩn | `Seven (feat. Latto)` |
| `artist` | `TEXT` | `NOT NULL` | Tên nghệ sĩ / các nghệ sĩ chính | `Jung Kook, Latto` |
| `album` | `TEXT` | `NULLABLE` | Tên album phát hành | `GOLDEN` |
| `release_date` | `DATE` | `NULLABLE` | Ngày phát hành chuẩn (YYYY-MM-DD) | `2023-07-14` |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT now()` | Thời gian tạo record trong database | `2026-09-21 10:30:00+07` |

---

#### Bảng: `chart_weekly` (Weekly Observation Entity)
- **Grain**: 1 dòng = 1 lần bài hát xuất hiện trên bảng xếp hạng weekly của một thị trường cụ thể tại một tuần cụ thể (`song × market × week`).
- **Mục đích**: Lưu toàn bộ lịch sử rank và streams thực tế để Member 4 tổng hợp thành quý (Quarters) và tính target `ChartScore`.

| Column Name | Data Type | Constraint | Description | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `BIGINT` | `IDENTITY PRIMARY KEY` | Khóa chính tự tăng | `1` |
| `spotify_track_id` | `TEXT` | `REFERENCES songs(spotify_track_id) ON DELETE CASCADE` | Khóa ngoại trỏ về bảng songs | `2HRgqmZQC0MC7GeNuDIXHN` |
| `market` | `TEXT` | `NOT NULL, CHECK (market IN ('VN', 'US', 'KR'))` | Thị trường âm nhạc | `VN` |
| `chart_date` | `DATE` | `NOT NULL` | Ngày chốt bảng xếp hạng tuần (YYYY-MM-DD) | `2023-07-20` |
| `rank` | `INT` | `NOT NULL, CHECK (rank > 0)` | Thứ hạng trong tuần đó (1 đến 200) | `1` |
| `streams` | `BIGINT` | `NULLABLE` | Số lượt nghe trong tuần đó (từ Kworb/Spotify) | `6489307` |

**Constraints & Indexes**:
- `UNIQUE (spotify_track_id, market, chart_date)`: Đảm bảo tính toàn vẹn dữ liệu, chống duplicate khi chạy sync định kỳ.
- `idx_chart_weekly_track`: Index tối ưu tốc độ JOIN và tính toán lifetime performance.
- `idx_chart_weekly_market_date`: Index tối ưu phân chia Quarters và phục vụ Stratified Sampling của Member 4.
- `idx_chart_weekly_market_rank`: Index tối ưu truy vấn theo stratum (Rank 1-10, 11-20, 21-50, 51+).

---

### 3. Pipeline Kiến trúc 2 Giai đoạn (2-Stage Crawling Architecture)

```
[Kworb Totals: VN, US, KR]
        │
        ▼ (member1_step1_kworb_totals.py)
  songs_master.csv (17,972 rows)
  unique_tracks.csv (15,036 unique track IDs)
        │
        ▼ (member1_step2_kworb_track_history.py)
   [Kworb Track Page: Table 0 Weekly]
   (VN, US, KR trích xuất đồng thời qua 1 request / bài)
   Lọc mốc thời gian: 2021-01-01 đến 2026
   Checkpoint & Auto-resume (crawled_track_ids.txt)
        │
        ▼
  chart_weekly.csv
        │
        ├──> (member1_step2b_spotify_metadata.py - Enrich album & release_date)
        │       │
        │       ▼
        │    songs_enriched.csv
        │
        └──> (member1_step3_load_to_supabase.py)
                │
                ▼
      [Supabase Database: songs + chart_weekly]
```

---

### 4. Kết quả nghiệm thu thực tế (Live Verification)

1. **Step 1 Totals Crawling**:
   - VN: 4,344 bài hát
   - US: 9,798 bài hát
   - KR: 3,830 bài hát
   - Tổng cộng: **17,972 dòng** dữ liệu thô.
   - Unique tracks sau khi de-duplicate: **15,036 bài duy nhất**.

2. **Step 2 Track Weekly Extraction**:
   - Đã chạy test nghiệm thu 5 bài đầu tiên (gồm J. Cole, Vũ., Da LAB, The Neighbourhood, Sơn Tùng M-TP).
   - Trích xuất thành công **1,131 mốc tuần** (Weekly records) trải dài từ `2021-01-07` đến `2026-09-17`.
   - Toàn bộ mốc tuần cách đều 7 ngày, rank và streams bóc tách chính xác 100%.

3. **Bàn giao cho Member 4**:
   - Danh sách `unique_tracks.csv` và `chart_weekly.csv` sẵn sàng để Member 4 áp dụng công thức chia Quarter (2021-Q1 ... 2026-Q3) và chạy Stratified Sampling (10 bài/stratum × 4 strata = 40 bài/market-quý).
