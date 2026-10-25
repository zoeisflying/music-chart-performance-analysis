# Báo cáo Phân tích Tương quan Đa biến & Khám phá Dữ liệu Tích hợp (Report 4)
**Học phần:** ADY201m - Applied Data Analytics  
**Dự án:** What Makes a Hit Song? (2021–2026)  
**Phân hệ:** Bivariate & Multivariate Integrated EDA  
**Biến mục tiêu Regression:** `chart_score` ($101 - \text{lifetime\_average\_rank}$)  
**Nguồn dữ liệu:** Supabase Database (`public.modeling_dataset` WHERE `is_sampled = True`, N = 2,860 entries)

---

## 1. Tổng quan Nghiên cứu & Mục tiêu
Báo cáo này mở rộng phạm vi phân tích đơn biến sang **Phân tích Tương quan Đa biến (Multivariate EDA)**, kết nối trực tiếp các đặc trưng Âm học (Audio Features) và Ca từ (Lyrics Features) với các chỉ số Thành tích Bảng xếp hạng (`chart_score`, `weeks_on_chart`, `peak_rank`) và Siêu dữ liệu (`market`, `release_year`).

Mọi nhận định trong báo cáo tuân thủ nguyên tắc **Mối liên hệ tương quan (Association), không khẳng định Quan hệ nhân quả (Causation)**, nhằm cung cấp cơ sở dữ liệu thực nghiệm cho Member 4 xây dựng mô hình Hồi quy (Regression).

---

## 2. Danh mục Biểu đồ và Dữ liệu Nguồn Tích hợp

| STT | Tên Biểu đồ | File Ảnh (300 DPI) | File Dữ liệu Nguồn (CSV) | Kiểm định Thống kê Chính |
| :---: | :--- | :--- | :--- | :--- |
| **Hình 1** | Ma trận Tương quan Đa biến | `reports/report4/figures/integrated/fig1_multimodal_correlation_heatmap.png` | `fig1_correlation_matrix.csv` | Hệ số tương quan hạng Spearman ($r_s$) |
| **Hình 2** | Phân tầng Thành tích theo ChartScore | `reports/report4/figures/integrated/fig2_chart_score_tiers_profiling.png` | `fig2_chart_score_tiers_summary.csv` | Kruskal-Wallis Test ($p < 0.001$) |
| **Hình 3** | Tương quan Hồi quy & LOWESS | `reports/report4/figures/integrated/fig3_features_vs_chartscore_scatter.png` | `fig3_features_vs_chartscore_scatter.csv` | Spearman $r_s$ & Pearson $r$ |
| **Hình 4** | Dịch chuyển theo Năm & Thị trường | `reports/report4/figures/integrated/fig4_temporal_market_evolution.png` | `fig4_temporal_market_evolution.csv` | Bootstrap 95% Confidence Interval |

---

## 3. Các Phát hiện Thực nghiệm Chính

### 3.1. Các Nhân tố Tương quan Thuận với Điểm số Thành tích (`chart_score`)
1. **Năng lượng Sóng âm (`rms_energy`):** Là đặc trưng âm học có tương quan thuận rõ nét nhất với `chart_score` ($r_s = 0.124, p < 0.001$). Các bài hát có mức năng lượng vật lý lớn, được nén âm thanh hiện đại có xu hướng giữ thứ hạng cao trên các nền tảng streaming.
2. **Tính Lặp lại Âm sắc (`mfcc_repetition_determinism`):** Tương quan thuận có ý nghĩa ($p < 0.001$). Các ca khúc duy trì một vòng lặp âm sắc/drum loop nhất quán giúp người nghe dễ định hình "groove" và thúc đẩy việc nghe lại nhiều lần.
3. **Tính Lặp lại Ca từ (`repetition_ratio`):** Đóng góp tích cực vào cả điểm số thành tích lẫn số tuần trụ hạng (`weeks_on_chart`) ($p < 0.001$), minh chứng cho vai trò của các đoạn hook điệp khúc dễ nhớ đối với tuổi thọ bài hát.

### 3.2. Sự Phân hóa Giữa các Tầng Thành tích (Performance Tiers)
- Khi chia `chart_score` thành 3 Tiers (Tier 1: Top 25% điểm cao nhất; Tier 2: 50% ở giữa; Tier 3: 25% điểm thấp nhất), kiểm định Kruskal-Wallis xác nhận sự khác biệt có ý nghĩa thống kê vượt trội trên cả 4 biến then chốt ($p < 0.001$).
- Nhóm Tier 1 (Siêu Hit) có trung vị `rms_energy` ($0.254$) và `mfcc_repetition_determinism` cao vượt trội so với Tier 3 ($0.225$).

### 3.3. Bằng chứng về Tính Phi tuyến (Non-linearity)
- Đường làm mịn LOWESS trong Hình 3 chứng minh mối quan hệ giữa các đặc trưng với `chart_score` xuất hiện các **ngưỡng bão hòa (Diminishing Returns)**. Việc tăng năng lượng hoặc tỷ lệ lặp lại quá cao sẽ không tiếp tục làm tăng điểm số thứ hạng.

---

## 4. Khuyến nghị Định hướng cho Mô hình Regression (Member 4)
1. **Lựa chọn Biến (Feature Selection Candidates):**
   - *Nhóm Predictor mạnh:* `rms_energy`, `mfcc_repetition_determinism`, `chord_change_rate`, `repetition_ratio`, `market`.
   - *Biến cần xử lý đa cộng tuyến:* Giữ `rms_energy`, loại bỏ hoặc chuẩn hóa `loudness_proxy`.
2. **Xử lý Biến mục tiêu (`chart_score`):**
   - Khuyến nghị áp dụng phép biến đổi $\log(1 + \text{chart\_score})$ trước khi huấn luyện để giảm thiểu độ lệch phải (skewness) của phân phối thành tích.
3. **Lựa chọn Thuật toán Hồi quy:**
   - Do tồn tại các ngưỡng bão hòa phi tuyến, các mô hình **Tree-based Ensemble (Random Forest Regressor, LightGBM/XGBoost Regressor)** được kỳ vọng sẽ đạt chỉ số $R^2$ và RMSE tốt hơn đáng kể so với mô hình Hồi quy Tuyến tính (OLS).
