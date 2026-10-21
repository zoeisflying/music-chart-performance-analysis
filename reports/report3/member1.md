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
3. **Phạm vi:** chỉ có bài từng lên chart trong cửa sổ trên (8.909 bài, 10.887 cặp). `song_quarter_sampling` không dùng để tính điểm.
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
