# Báo Cáo Khám Phá Dữ Liệu Tích Hợp Đa Phương Thức — Member 4 (Report 4)

* **Học phần:** ADY201m — Advanced Data Analytics / Applied Data Science Project  
* **Thành viên phụ trách:** Member 4 (Data Integration, Quality Control & Report Coordination)  
* **Ngày cập nhật:** 2026-10-26  
* **Nguồn dữ liệu:** Tập dữ liệu mô hình hóa `data/processed/modeling_dataset.csv` ($N = 2.860$) và tập xu hướng theo quý `data/processed/quarterly_feature_trends.csv` ($N = 2.760$).

---

## 1. Tóm Tắt Nhiệm Vụ Trực Quan Hóa Của Member 4

Bên cạnh việc review và thống nhất quy chuẩn trực quan hóa cho toàn bộ biểu đồ của Member 1, 2, và 3 (về mã màu thị trường, đơn vị đo, kích thước font, và ghi rõ số lượng quan sát $N$), Member 4 trực tiếp phụ trách **5 biểu đồ tích hợp đa phương thức & phân tích chuỗi thời gian**:
1. **Hình 1:** Ma trận tương quan đa phương thức tổng thể (Multimodal Correlation Heatmap).
2. **Hình 2:** So sánh cấu trúc tương quan phân tầng theo thị trường (Tri-Market Faceted Correlation Heatmap).
3. **Hình 3:** Quỹ đạo tiến hóa các đặc trưng âm học theo quý giai đoạn 2021-Q1 đến 2026-Q3 (Longitudinal Quarterly Acoustic Trajectories).
4. **Hình 4:** Quỹ đạo tiến hóa độ phức tạp ca từ theo quý giai đoạn 2021-Q1 đến 2026-Q3 (Longitudinal Quarterly Lyrical Trajectories).
5. **Hình 5:** Mối liên hệ nhị biến có đường hồi quy giữa ChartScore và các đặc trưng âm thanh/ca từ tiêu biểu (Bivariate Multimodal Associations).

Toàn bộ biểu đồ độ nét cao (300 DPI) được lưu trữ tại `reports/report4/figures/member4/`, đi kèm các file CSV nguồn độc lập tại `reports/report4/chart_data/member4/`.

---

## 2. Danh Mục Biểu Đồ & Phân Tích Chuyên Sâu

### 2.1. Hình 1: Ma trận Tương quan Đa phương thức Toàn cầu
* **File ảnh:** [`reports/report4/figures/member4/fig1_correlation_matrix_overall.png`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/figures/member4/fig1_correlation_matrix_overall.png)
* **Dữ liệu nguồn:** [`reports/report4/chart_data/member4/fig1_correlation_overall.csv`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_data/member4/fig1_correlation_overall.csv)
* **Cỡ mẫu:** $N = 2.860$ quan sát trên toàn bộ 3 thị trường.

**Nhận định phân tích:**
- Mối tương quan tuyến tính đơn biến giữa biến mục tiêu `chart_score` và toàn bộ các biến số âm thanh/ca từ đều ở mức rất thấp ($|r| < 0.15$). Cụ thể: `rms_energy` ($r = 0.04$), `tempo_bpm` ($r = 0.02$), `spectral_centroid` ($r = 0.05$), `word_count` ($r = -0.06$).
- **Hàm ý thực nghiệm:** Điều này chứng minh thành công thương mại không bị chi phối đơn giản bởi một thuộc tính vật lý đơn lẻ (như nhạc phải to hơn hay tempo phải nhanh hơn). Thành công trên bảng xếp hạng là hàm phi tuyến kết hợp của nhiều yếu tố.
- Cụm biến âm học nội tại có liên kết chặt chẽ: `rms_energy` tương quan mạnh với `onset_rate` ($r = 0.48$) và `spectral_centroid` ($r = 0.41$).

---

### 2.2. Hình 2: Ma trận Tương quan Phân tầng 3 Thị trường
* **File ảnh:** [`reports/report4/figures/member4/fig2_correlation_matrix_by_market.png`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/figures/member4/fig2_correlation_matrix_by_market.png)
* **Dữ liệu nguồn:** [`reports/report4/chart_data/member4/fig2_correlation_by_market.csv`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_data/member4/fig2_correlation_by_market.csv)
* **Cỡ mẫu:** VN ($n = 885$), US ($n = 955$), KR ($n = 1.020$).

**Nhận định phân tích:**
- Sự tương phản rõ rệt nhất nằm ở mối quan hệ giữa **Năng lượng sóng âm (`rms_energy`) và Thứ hạng**:
  * Tại **Hàn Quốc (KR)**, `rms_energy` tương quan dương với `chart_score` ($r = +0.08$), phù hợp với xu hướng các nhóm nhạc thần tượng K-Pop đạt thứ hạng cao với các bản nhạc Dance/EDM dồn dập.
  * Tại **Việt Nam (VN)**, `rms_energy` tương quan âm với `chart_score` ($r = -0.05$), phản ánh thị hiếu ưa chuộng các bản Pop-Ballad, Indie trữ tình nhẹ nhàng có mức năng lượng vừa phải.
- Tại **Hoa Kỳ (US)**, `word_count` tương quan âm ($r = -0.09$) với `chart_score`, cho thấy các ca khúc có ca từ cô đọng, dễ ghi nhớ có xu hướng đạt thứ hạng bền bỉ hơn.

---

### 2.3. Hình 3: Quỹ đạo Tiến hóa Đặc trưng Âm học theo Quý (2021Q1–2026Q3)
* **File ảnh:** [`reports/report4/figures/member4/fig3_quarterly_acoustic_trends.png`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/figures/member4/fig3_quarterly_acoustic_trends.png)
* **Dữ liệu nguồn:** [`reports/report4/chart_data/member4/fig3_quarterly_acoustic_trends.csv`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_data/member4/fig3_quarterly_acoustic_trends.csv)
* **Cỡ mẫu:** $N = 2.760$ quan sát theo quý từ `song_quarter_sampling`.

**Nhận định phân tích:**
- **Độ ổn định của nhịp phách:** Qua 23 quý liên tục, đường trung bình `tempo_bpm` trên cả 3 thị trường duy trì ổn định xung quanh dải $118 - 124$ BPM.
- **Dấu ấn K-Pop kiên định:** Mật độ nốt (`onset_rate`) của Hàn Quốc luôn vượt trội và dẫn đầu liên tục qua toàn bộ 23 quý, củng cố kết luận đây là đặc trưng phong cách phối khí cố định của K-Pop.
- **Sự hội tụ năng lượng:** Khoảng cách `rms_energy` giữa Việt Nam và quốc tế có xu hướng thu hẹp từ năm 2024 trở đi, phản ánh tiêu chuẩn mastering trong nước tiệm cận chuẩn thế giới.

---

### 2.4. Hình 4: Quỹ đạo Tiến hóa Đặc trưng Ca từ theo Quý (2021Q1–2026Q3)
* **File ảnh:** [`reports/report4/figures/member4/fig4_quarterly_lyric_trends.png`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/figures/member4/fig4_quarterly_lyric_trends.png)
* **Dữ liệu nguồn:** [`reports/report4/chart_data/member4/fig4_quarterly_lyric_trends.csv`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_data/member4/fig4_quarterly_lyric_trends.csv)
* **Cỡ mẫu:** $N = 2.760$ quan sát theo quý.

**Nhận định phân tích:**
- Tỷ lệ đa dạng từ vựng (`lexical_diversity`) và tỷ lệ lặp lại (`repetition_ratio`) duy trì xu hướng gần như đi ngang tuyệt đối qua các quý.
- Các nhạc sĩ pop thương mại vận hành theo cấu trúc lặp lại từ vựng rất ổn định (khoảng 60% từ vựng được lặp lại) nhằm cân bằng giữa tính bắt tai và tính mạch lạc.

---

### 2.5. Hình 5: Mối Liên hệ Nhị biến giữa ChartScore và Các Đặc trưng Đa phương thức
* **File ảnh:** [`reports/report4/figures/member4/fig5_chartscore_multimodal_associations.png`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/figures/member4/fig5_chartscore_multimodal_associations.png)
* **Dữ liệu nguồn:** [`reports/report4/chart_data/member4/fig5_chartscore_multimodal_associations.csv`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_data/member4/fig5_chartscore_multimodal_associations.csv)
* **Cỡ mẫu:** $N = 2.860$ quan sát.

**Nhận định phân tích:**
- Đám mây điểm (scatter cloud) của các bài hát Hit ($\text{ChartScore} > 0$) trải rộng đồng đều trên toàn bộ phổ giá trị của năng lượng, độ sáng phổ, và độ dài lời bài hát.
- Đường hồi quy tuyến tính của cả 3 thị trường đều có độ dốc thấp, minh họa trực quan rằng không có một ngưỡng giá trị đơn lẻ nào là điều kiện cần hoặc đủ để tạo hit.

---

## 3. Quản Trị Kho Biểu Đồ Nghiên Cứu (`reports/report4/chart_inventory.xlsx`)

Member 4 đã kiểm toán và đóng gói toàn bộ **18 biểu đồ nghiên cứu khoa học** của 4 thành viên vào file Excel [`reports/report4/chart_inventory.xlsx`](file:///c:/Users/Laptop/ADY201m-main/reports/report4/chart_inventory.xlsx), bao gồm:
* 4 biểu đồ phân hệ Bảng xếp hạng (Member 1)
* 5 biểu đồ phân hệ Âm thanh (Member 2)
* 9 biểu đồ phân hệ Ca từ (Member 3)
* 5 biểu đồ phân hệ Tích hợp đa phương thức (Member 4)
Mỗi biểu đồ được chuẩn hóa đầy đủ thông tin: Mã hình, Tiêu đề, Đường dẫn ảnh, Dữ liệu nguồn CSV, Phương pháp kiểm định thống kê, Cỡ mẫu $N$, và Tóm tắt phát hiện học thuật.

---

## 4. Hướng Dẫn Tái Lập Biểu Đồ Member 4

```bash
# Chạy script tạo toàn bộ 5 biểu đồ, 5 CSV dữ liệu nguồn và file chart_inventory.xlsx
python src/integration/generate_integrated_charts.py
```
