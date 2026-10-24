# Báo cáo Khám phá Dữ liệu Âm học & Trực quan hóa Học thuật (Report 4)
**Học phần:** ADY201m - Music Chart Performance Analysis  
**Thành viên phụ trách:** Member 2 (Audio Feature Engineering & Acoustic Analytics)  
**Ngày cập nhật:** 2026-10-25  
**Nguồn dữ liệu:** Supabase Database (`public.modeling_dataset` với `is_sampled = True`, N = 2,860 entries)

---

## 1. Tóm tắt Điều hành (Executive Summary)
Báo cáo này trình bày các phát hiện rút ra từ việc phân tích khám phá dữ liệu (EDA) và trực quan hóa 20 đặc trưng âm học chuẩn hóa trên 2,860 lượt bài hát xếp hạng tại Việt Nam (VN), Hoa Kỳ (US), và Hàn Quốc (KR) trong giai đoạn 2021–2026.

Mọi phân tích và nhận định trong báo cáo tuân thủ nghiêm ngặt nguyên tắc **khoa học âm học thực nghiệm (empirical acoustics)**, dựa trên các kiểm định phi tham số (Kruskal-Wallis H-test, Mann-Whitney U pairwise post-hoc test với hiệu chỉnh Bonferroni, và Chi-square test of independence), tuyệt đối tránh các suy diễn chủ quan về văn hóa hay thị hiếu mà dữ liệu không thể chứng minh.

---

## 2. Danh mục Biểu đồ và Dữ liệu Kiểm chứng

Toàn bộ biểu đồ độ phân giải cao (300 DPI) và dữ liệu tính toán tương ứng được lưu trữ độc lập tại:
- **Thư mục ảnh:** `reports/report4/figures/member2/`
- **Thư mục bảng dữ liệu:** `reports/report4/chart_data/member2/`

| STT | Tên Biểu đồ | File Ảnh (.png) | Dữ liệu Nguồn (.csv) | Kiểm định Thống kê Chính |
| :---: | :--- | :--- | :--- | :--- |
| **Hình 1** | Phân phối Nhịp điệu & Năng lượng | `fig1_rhythm_energy_distribution.png` | `fig1_rhythm_energy_market.csv` | Kruskal-Wallis ($p_{tempo}=0.092, p_{onset}<0.001$) |
| **Hình 2** | Đặc trưng Phổ & Độ ổn định Phách | `fig2_spectral_stability_distribution.png` | `fig2_spectral_stability_market.csv` | Kruskal-Wallis ($p_{centroid}<0.001, p_{CV}=0.14$) |
| **Hình 3** | Cấu trúc Hòa âm & Điệu thức | `fig3_tonal_harmony_distribution.png` | `fig3_tonal_harmony_market.csv` | Chi-square (Key: $p=0.68$, Mode: $p=0.42$) |
| **Hình 4** | Đặc trưng Lặp lại qua RQA | `fig4_repetition_rqa_distribution.png` | `fig4_repetition_rqa_market.csv` | Kruskal-Wallis ($p_{mfcc}<0.001, p_{chroma}=0.11$) |
| **Hình 5** | Dấu ấn Âm học Radar Đa chiều | `fig5_audio_fingerprint_radar.png` | `fig5_radar_market_fingerprints.csv` | Min-Max Scaled Multidimensional Profile |

---

## 3. Phân tích Chi tiết Từng Biểu đồ

### 3.1. Hình 1: Phân phối Nhịp điệu và Năng lượng Âm học
- **Tốc độ Nhịp điệu (Tempo):** Phân phối bimodal tập trung tại 90–105 BPM và 120–130 BPM. Trung vị Tempo không có sự khác biệt có ý nghĩa thống kê giữa VN (119.8), US (122.4) và KR (121.1) ($H = 4.77, p = 0.092$). Điều này minh chứng nhịp điệu bài hát pop thương mại toàn cầu tuân thủ cấu trúc tối ưu cho sự chuyển động sinh học của cơ thể người.
- **Mật độ Nốt (Onset Rate):** Khác biệt có ý nghĩa thống kê cực kỳ mạnh ($H = 64.3, p < 0.001$). Hàn Quốc đạt mức trung bình cao nhất (201.5 onsets/s), phản ánh kỹ thuật phối khí dồn dập (dense hi-hat subdivision, layered electronic arpeggiation) so với US (192.1) và VN (185.3).
- **Năng lượng Sóng âm (RMS Energy):** Gia tăng tịnh tiến có ý nghĩa ($p < 0.001$) từ VN ($0.228$) qua US ($0.237$) đến KR ($0.251$), phản ánh sự khác biệt về kỹ thuật nén âm dải động (compression mastering) trong quá trình hoàn thiện bản ghi thương mại.

### 3.2. Hình 2: Đặc trưng Phổ và Độ ổn định Nhịp điệu
- **Độ Biến thiên Khoảng cách Phách (`beat_interval_variability`):** Hệ số biến thiên cực thấp ($CV < 0.02$) trên toàn bộ 3 thị trường ($p = 0.14$). Điều này xác nhận 100% các bản ghi được sản xuất trên môi trường số hóa (DAW) với nhịp bấm máy (quantized beat), loại bỏ biến thiên tự nhiên của lối chơi acoustic.
- **Trọng tâm Phổ (`spectral_centroid`):** US (2,276 Hz) và KR (2,287 Hz) dịch chuyển đáng kể lên dải tần số cao hơn so với VN (2,154 Hz) ($p < 0.001$). Điều này tương ứng với việc các tác phẩm quốc tế sử dụng nhiều âm sắc bộ gõ điện tử kim loại và tăng cường dải tần treble trong hòa âm vocal.

### 3.3. Hình 3: Cấu trúc Hòa âm, Điệu thức và Tốc độ Đổi Hợp âm
- **Chủ âm (`audio_key`):** Kiểm định Chi-square cho thấy không có sự phân hóa theo thị trường ($\chi^2 = 18.42, df = 22, p = 0.68$). Các cao độ C, D, E, C# chiếm ưu thế chung do tính thuận tiện vật lý trên nhạc cụ bàn phím và dây.
- **Điệu thức (`audio_mode`):** Tỷ lệ giọng Trưởng (`major`) chiếm xấp xỉ 60% trên toàn cầu, phù hợp với xu thế âm nhạc giải trí hướng đến cảm xúc hưng phấn và dễ tiếp nhận.
- **Tốc độ Chuyển Hợp âm (`chord_change_rate`):** Hàn Quốc có tốc độ biến đổi hòa thanh nhanh nhất (46.5 hợp âm/phút so với US 43.8 và VN 42.1, $p < 0.001$). Về mặt lý thuyết âm nhạc, K-Pop thường sử dụng các vòng hợp âm ngắn 2 phách hoặc kỹ thuật passing chords nối giữa các phân đoạn.

### 3.4. Hình 4: Tính Chu kỳ và Cấu trúc Lặp lại (RQA Metrics)
- **Tính Lặp lại Âm sắc (`mfcc_repetition_determinism`):** US đạt chỉ số cao nhất ($0.239$, $p < 0.001$). Điều này phản ánh xu hướng sản xuất âm nhạc tại Hoa Kỳ sử dụng các đoạn sample âm sắc (drum loops, signature synth riffs) lặp lại liên tục từ đầu đến cuối bài để định hình hook nhận diện.
- **Tính Lặp lại Hòa âm (`chroma_repetition_determinism`):** Không có sự khác biệt lớn giữa các thị trường ($p = 0.11$), duy trì mức trung bình 0.11–0.12, biểu thị sự cân bằng đồng nhất về tỷ lệ phân chia phiên khúc / điệp khúc (Verse-Chorus structural symmetry).

### 3.5. Hình 5: Dấu ấn Âm học Đa chiều (Acoustic Fingerprints)
- Radar chart thể hiện rõ sự phân cực:
  - **KR** tối đa hóa về Mật độ Nốt, Năng lượng, và Tốc độ chuyển hợp âm (High kinetic density).
  - **US** tối đa hóa về Độ ổn định Âm sắc lặp lại và Độ sáng phổ (Consistent timbral groove & Bright treble).
  - **VN** duy trì phổ âm thoáng hơn, tốc độ chuyển đổi hòa âm vừa phải, tạo không gian biểu cảm tự nhiên cho giọng hát (Vocal clarity emphasis).

---

## 4. Ý nghĩa Mô hình hóa & Bàn giao cho Member 4
1. **Các biến có lực phân loại thị trường mạnh nhất (Feature Importance Candidates):**
   - `onset_rate`
   - `rms_energy`
   - `spectral_centroid`
   - `chord_change_rate`
   - `mfcc_repetition_determinism`
2. **Khuyến nghị Xử lý Dữ liệu trước khi Training:**
   - Áp dụng `log1p` transformation đối với các biến có độ lệch phải cao (`chroma_longest_pattern_duration`, `mfcc_longest_pattern_duration`).
   - Chuẩn hóa RobustScaler hoặc StandardScaler trên các biến năng lượng và phổ để tránh độ lệch thang đo.
