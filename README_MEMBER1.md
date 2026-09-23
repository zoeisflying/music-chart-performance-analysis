# HƯỚNG DẪN THỰC THI TOÀN BỘ PIPELINE — MEMBER 1
## Chart Data Collection & Song Metadata (Spotify / Kworb)

### 📁 Danh sách tệp đã hoàn thiện tại `D:\`:
1. `create_songs_and_chart_weekly.sql`: Script migration SQL cho Supabase.
2. `member1_step1_kworb_totals.py`: Crawl bảng tổng hợp toàn bộ bài hát từng chart ở VN, US, KR.
3. `member1_step2_kworb_track_history.py`: Crawl lịch sử tuần chi tiết (2021–2026) cho từng bài, hỗ trợ checkpoint/resume.
4. `member1_step2b_spotify_metadata.py`: Enrich metadata album & ngày phát hành từ Spotify API batch (50 bài/call).
5. `member1_step3_load_to_supabase.py`: Upsert dữ liệu vào 2 bảng `songs` và `chart_weekly` trên Supabase.
6. `data_dictionary_member1.md`: Data Dictionary chi tiết để nộp Report 2 và bàn giao cho Member 4.

---

### 🚀 Quy trình thực thi từng bước

#### Bước 1: Cài đặt thư viện Python cần thiết
Mở terminal tại `D:\` và chạy:
```powershell
pip install requests beautifulsoup4 supabase python-dotenv
```

#### Bước 2: Chạy Step 1 (Đã chạy thành công ✅)
```powershell
python member1_step1_kworb_totals.py
```
- **Kết quả**:
  - `songs_master.csv`: 17,972 dòng (4,344 bài VN, 9,798 bài US, 3,830 bài KR).
  - `unique_tracks.csv`: 15,036 bài duy nhất, đã sắp xếp theo độ phổ biến (`max_wks`).

#### Bước 3: Chạy Step 2 (Crawl lịch sử tuần)
- **Chế độ kiểm tra (Test 5 bài đầu tiên - Đã nghiệm thu ✅)**:
  ```powershell
  python member1_step2_kworb_track_history.py
  ```
  -> Đã thu về 1,131 mốc tuần chính xác tuyệt đối.

- **Chế độ chạy toàn bộ (Full Run với Checkpoint/Resume)**:
  ```powershell
  python member1_step2_kworb_track_history.py --full
  ```
  > **💡 Tính năng quan trọng:**
  > - Script có cơ chế ghi nhận checkpoint vào `crawled_track_ids.txt`.
  > - Nếu rớt mạng hoặc bạn bấm `Ctrl+C` dừng lại, lần sau chạy lại script sẽ **tự động chạy tiếp các bài chưa crawl**, không bao giờ mất dữ liệu hay crawl trùng.

#### Bước 4: Chuẩn hóa metadata qua Spotify API (Tùy chọn)
Nếu có `SPOTIFY_CLIENT_ID` và `SPOTIFY_CLIENT_SECRET` (tạo free tại [developer.spotify.com](https://developer.spotify.com/dashboard)), tạo file `.env` tại `D:\`:
```env
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
```
Sau đó chạy:
```powershell
python member1_step2b_spotify_metadata.py
```
*(Nếu chưa có API key, Step 3 vẫn nạp vào Supabase bình thường với trường album/release_date tạm để trống).*

#### Bước 5: Tạo bảng trên Supabase (Migration)
Theo quy định nhóm, không tạo bảng thủ công trên Web UI:
1. Nếu đã link Supabase CLI:
   ```powershell
   npx supabase migration new create_songs_and_chart_weekly
   ```
2. Mở file migration vừa sinh ra trong `supabase/migrations/` và dán toàn bộ nội dung từ `create_songs_and_chart_weekly.sql` vào.
3. Chạy migration lên Supabase:
   ```powershell
   npx supabase db push
   ```

#### Bước 6: Nạp dữ liệu vào Supabase
Thêm cấu hình Supabase vào file `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-or-anon-key
```
Chạy script nạp:
```powershell
python member1_step3_load_to_supabase.py
```

---

### 🌿 Quy trình Git chuẩn của dự án (khi clone repo)
```powershell
# 1. Clone repo nhóm
git clone <URL_REPO_NHOM>
cd music-chart-performance-analysis

# 2. Tạo và chuyển sang branch của Member 1
git checkout -b feature/member1-chart

# 3. Copy các script vào đúng cấu trúc repo:
#    - Đặt các file .py vào: src/chart/
#    - Đặt file .sql vào: supabase/migrations/
#    - Đặt data_dictionary_member1.md vào: docs/

# 4. Commit và Push:
git add .
git commit -m "feat(chart): complete kworb 2-stage crawler and supabase pipeline for member 1"
git push -u origin feature/member1-chart

# 5. Tạo Pull Request trên GitHub vào branch main để cả nhóm review.
```
