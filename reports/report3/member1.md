# Report 3 — Member 1: Chart Performance

## 1. Nguồn dữ liệu
- `chart_weekly` (Supabase): 161.734 dòng (VN 57.278 · US 49.596 · KR 54.860), 2021-01-07 → 2026-09-17, toàn bộ là thứ Năm, Kworb Spotify Weekly **Top 200**.
- `songs`: 15.037 bài. 0 dòng mồ côi, 0 trùng khóa (spotify_track_id, market, chart_date).
- Các file `data/raw/chart/chart_weekly*.csv` chồng lấn nhau 34.889 dòng; sau khi bỏ trùng ra đúng 161.734 dòng, khớp Supabase.

## 2. Định nghĩa chính thức
| Biến | Định nghĩa |
|---|---|
| lifetime_average_rank | Trung bình rank trên **mọi tuần hợp lệ** của (bài, market) trong cửa sổ 2021–2026 |
| chart_score | `101 − lifetime_average_rank` |
| peak_rank | Rank nhỏ nhất |
| weeks_on_chart | Số tuần có bản ghi hợp lệ |
| weeks_in_top10 | Số tuần có rank 1–10 |

Bài không có bản ghi chart **không** có dòng trong `chart_performance` (không gán 0).

## 3. Giới hạn cần nêu
1. **Chart sâu 200, công thức dùng 101:** 6.682/10.887 cặp (61%) có chart_score < 0 (thấp nhất −99). Thứ tự xếp hạng vẫn đúng, nhưng không thể diễn giải điểm là thang 0–100. Đề xuất đổi sang `201 − avg` đang chờ nhóm quyết định.
2. **"Lifetime" = trong cửa sổ 2021–2026:** crawler chỉ lấy từ 2021-01-01, nên `weeks_on_chart`, `peak_rank` của bài ra mắt trước 2021 bị cắt.
3. **Phạm vi & Độ đầy đủ chuỗi tuần:** 
   - Chỉ có bài từng lên chart trong cửa sổ trên (8.909 bài, 10.887 cặp). `song_quarter_sampling` không dùng để tính điểm.
   - **Đánh giá kiểm toán:** Kiểm tra mẫu 96 cặp cho thấy khoảng $96\%$ cặp có trong tổng hợp Kworb nhưng không có trong `chart_weekly` là bài đã out chart trước 2021. Phần còn lại chủ yếu do khoảng trống trên bảng tuần của Kworb (khoảng $4\%$). Script cào không phân biệt bài không có tuần nào với trang bị lỗi tải. Mẫu kiểm tra 96 cặp phát hiện 1 ca (Jax, mất cả US và KR). Do mẫu nhỏ, tỷ lệ bỏ sót thực chưa xác định chắc chắn; khoảng tin cậy 95% (Clopper–Pearson) là khoảng $0.03\%–5.7\%$ số cặp thiếu (tương đương 2–400 cặp). Ngoài ra khoảng $400$ cặp đã có bị thiếu từ 10 tuần trở lên ($406$ cặp), nên nhóm đánh dấu các cặp này và kiểm tra độ nhạy của mô hình. Dữ liệu chốt ngày `17/09/2026`.
   - **Khuyết vị trí Top 10:** Tập dữ liệu khuyết từ **$14.6\% - 20.8\%$ vị trí Top 10** (nặng nhất ở US với 621 vị trí, 75 tuần khuyết Hạng 1, dồn trọng tâm vào 2023–2025 do lỗi đứt đoạn thời gian của nguồn Kworb).
   - **Tình trạng khắc phục:** Nhóm **chưa thực hiện vá dữ liệu** tại Checkpoint 2/3 để bảo toàn tính toàn vẹn (tránh nguy cơ lệch quy ước ngày và rank giữa các nguồn). Hướng vá dữ liệu từ nguồn chính thức (Spotify Charts) được ghi nhận là việc tiếp theo nếu có điều kiện.
4. 1 dòng `streams = 0` (KR, 2021-06-10, rank 101) được giữ vì streams không tham gia ChartScore.
5. `peak_rank`, `weeks_on_chart`, `weeks_in_top10` cùng nguồn với target, **không dùng làm predictor**.

## 4. Kết quả (bảng `chart_performance`)
| Market | Số cặp | Mean chart_score | Median | Cặp score < 0 |
|---|---|---|---|---|
| VN | 2.644 | −23,20 | −25,50 | 1.844 |
| US | 4.460 | −7,92 | −3,00 | 2.314 |
| KR | 3.783 | −20,47 | −19,80 | 2.524 |
| Tổng | 10.887 | −15,99 | −14,92 | 6.682 |

Chi tiết: `reports/report3/chart_statistics.csv`. Kiểm định: `logs/chart_validation_log.csv` (24/24 pass).

## 5. Cách chạy lại
```
python src/chart/build_chart_performance.py            # đọc chart_weekly, upsert chart_performance
python src/chart/validate_chart_data.py                # ghi log + thống kê
```
SQL migration: `sql/01_chart_performance.sql` (chạy lại không tạo trùng).
