# Report 4 — Member 1: Exploratory Data Analysis & Chart Visualization
**Đề tài:** What Makes a Hit Song? Comparing chart performance between Vietnam, US, and South Korea (2021–2026)  
**Tác giả:** Member 1 (Data Engineer / Chart Data, Performance Metrics & Visualization)  
**Quy mô dữ liệu:** $N = 10.887$ cặp bài hát × thị trường từ $161.734$ bản ghi BXH tuần (VN: 2.644 cặp / 57.278 tuần; US: 4.460 cặp / 49.596 tuần; KR: 3.783 cặp / 54.860 tuần).

---

## 1. Tóm tắt Thống kê Mô tả Tổng hợp

Dữ liệu được trích xuất từ bảng `public.chart_performance` trên Supabase (khớp 100% với file dữ liệu tái lập tại [`reports/report4/chart_data/member1/fig2_chart_score_boxplot_stats.csv`](file:///D:/music-chart-performance-analysis/reports/report4/chart_data/member1/fig2_chart_score_boxplot_stats.csv)):

| Thị trường (Market) | Số cặp ($n$) | Bản ghi tuần | Mean ChartScore | Median ChartScore | IQR ChartScore | Tỷ lệ > 0 (Top 100) | Mean Weeks on Chart | Median Weeks (IQR) | Max Weeks |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Việt Nam (VN)** | 2.644 | 57.278 | -23.20 | -25.50 | 61.80 (-55.80 → +6.00) | **29.88%** | **21.66 tuần** | 5.0 tuần (19.0) | 297 tuần |
| **Mỹ (US)** | 4.460 | 49.596 | **-7.92** | **-3.00** | 70.95 (-43.95 → +27.00) | **47.69%** | 11.12 tuần | 3.0 tuần (10.0) | 289 tuần |
| **Hàn Quốc (KR)** | 3.783 | 54.860 | -20.47 | -19.80 | 61.50 (-52.00 → +9.50) | 32.91% | 14.50 tuần | 4.0 tuần (13.0) | 272 tuần |
| **Toàn bộ (ALL)** | **10.887** | **161.734** | **-15.99** | **-14.92** | **67.12** (-50.44 → +16.68) | **38.23%** | **14.86 tuần** | 4.0 tuần (13.0) | **297 tuần** |

---

## 2. Phân tích Chi tiết 4 Biểu đồ Khoa học (300 DPI)

### Biểu đồ 1: Phân phối Mật độ ChartScore theo Thị trường (`chart_score_distribution.png`)
* **Tệp ảnh:** [`reports/report4/figures/member1/chart_score_distribution.png`](file:///D:/music-chart-performance-analysis/reports/report4/figures/member1/chart_score_distribution.png)  
* **Dữ liệu tái lập:** [`reports/report4/chart_data/member1/fig1_chart_score_distribution_bins.csv`](file:///D:/music-chart-performance-analysis/reports/report4/chart_data/member1/fig1_chart_score_distribution_bins.csv)  
* **Số quan sát:** $N = 10.887$ (VN: 2.644, US: 4.460, KR: 3.783). Đơn vị: Điểm số (thang đo: $-99$ đến $+100$).

#### Quan sát & Nhận định:
1. **Phân định Ngưỡng Top 100 tại $x = 0$:**
   Đường ranh giới thẳng đứng $x = 0$ (ứng với $\text{LifetimeAverageRank} = 101$) phân tách rõ ràng hai miền phân phối:
   * **Miền bên phải ($x > 0$ — Vùng Hit Top 100):** Tỷ lệ bài hát đạt điểm dương ở Mỹ (US) áp đảo hoàn toàn với **$47.69\%$**, trong khi Hàn Quốc (KR) đạt **$32.91\%$** và Việt Nam (VN) chỉ có **$29.88\%$**.
   * **Miền bên trái ($x < 0$ — Vùng Nửa dưới BXH):** Chiếm tới $61.77\%$ tổng số bài trên toàn bộ dataset ($6.725 / 10.887$ cặp). Đây là các bài hát dao động ở nửa dưới Top 101–200.
2. **Hình dáng phân phối (Distribution Shape):**
   * Đường KDE của US tương đối cân bằng và có đỉnh tiệm cận mốc $-3.0$, phân tán rộng khắp dải điểm.
   * Phân phối của VN và KR lệch sang bên trái rõ nét hơn (đỉnh mật độ nằm quanh vùng $-20$ đến $-30$), phản ánh phần lớn ca khúc khi lọt vào chart thường tích lũy thứ hạng ở nửa sau bảng xếp hạng.

---

### Biểu đồ 2: So sánh Trung vị & Độ phân tán liên Thị trường (`chart_score_boxplot.png`)
* **Tệp ảnh:** [`reports/report4/figures/member1/chart_score_boxplot.png`](file:///D:/music-chart-performance-analysis/reports/report4/figures/member1/chart_score_boxplot.png)  
* **Dữ liệu tái lập:** [`reports/report4/chart_data/member1/fig2_chart_score_boxplot_stats.csv`](file:///D:/music-chart-performance-analysis/reports/report4/chart_data/member1/fig2_chart_score_boxplot_stats.csv)  
* **Số quan sát:** $N = 10.887$.

#### Quan sát & Nhận định:
1. **Khoảng cách Trung vị (Median Disparity):**
   * Thị trường US dẫn đầu hoàn toàn với trung vị $\text{Median} = -3.00$ điểm ($\text{Mean} = -7.92$), vượt trội đáng kể so với KR ($-19.80$) và VN ($-25.50$).
2. **Độ phân tán (Interquartile Range - IQR):**
   * Cả 3 thị trường đều có khoảng tứ phân vị rất rộng và tương đồng ($IQR_{\text{US}} = 70.95$, $IQR_{\text{VN}} = 61.80$, $IQR_{\text{KR}} = 61.50$). 
   * Điều này chứng minh sự phân hóa cực kỳ sâu sắc trong nội bộ mỗi nền âm nhạc: một bài hát khi đã lọt vào Spotify Weekly có thể là "Super Hit" bám trụ top 10 (điểm $> 70$), hoặc chỉ là bài hát hoạt động mờ nhạt ở nhóm cuối (điểm $< -50$).
3. **Ý nghĩa của Điểm trung bình (Mean Diamond Marker):**
   * Ở cả 3 nước, giá trị `Mean` đều nằm gần `Median` (độ lệch xiên $\text{Skewness} \in [-0.21, 0.30]$), xác nhận biến mục tiêu ChartScore có phân phối gần đối xứng sau khi đã chuẩn hóa về thang tuyến tính $101 - \text{Rank}$, rất thuận lợi cho giả định phân phối phần dư (normality of residuals) của mô hình hồi quy OLS sau này.

---

### Biểu đồ 3: Phân phối Rank gốc trong BXH Tuần (`raw_rank_distribution.png`)
* **Tệp ảnh:** [`reports/report4/figures/member1/raw_rank_distribution.png`](file:///D:/music-chart-performance-analysis/reports/report4/figures/member1/raw_rank_distribution.png)  
* **Dữ liệu tái lập:** [`reports/report4/chart_data/member1/fig3_raw_rank_distribution.csv`](file:///D:/music-chart-performance-analysis/reports/report4/chart_data/member1/fig3_raw_rank_distribution.csv)  
* **Số quan sát:** $161.734$ bản ghi tuần (VN: 57.278; US: 49.596; KR: 54.860).

#### Quan sát & Nhận định:
1. **Bằng chứng thực nghiệm về BXH Top 200:**
   * Dữ liệu tuần trải dài liên tục và đồng đều từ hạng $1$ đến đúng hạng $200$. 
   * Tỷ lệ bản ghi nằm ở nửa dưới Top 101–200 là **$50.49\%$** ($81.659 / 161.734$ dòng).
2. **Cơ sở Toán học của Hiện tượng Điểm Âm:**
   * Biểu đồ này là bằng chứng đanh thép giải thích vì sao $\text{ChartScore}$ xuất hiện giá trị âm: vì công thức thống nhất của nhóm là $101 - \text{LifetimeAverageRank}$. Khi một bài hát có thứ hạng trung bình cả đời rơi vào khoảng $102$ đến $200$, điểm số chắc chắn mang dấu âm (từ $-1$ đến $-99$). Thứ tự xếp hạng tương đối của các bài không hề bị đảo lộn.

---

### Biểu đồ 4: Độ bền Trụ hạng và Cấu trúc Đuôi dài (`chart_longevity_weeks.png`)
* **Tệp ảnh:** [`reports/report4/figures/member1/chart_longevity_weeks.png`](file:///D:/music-chart-performance-analysis/reports/report4/figures/member1/chart_longevity_weeks.png)  
* **Dữ liệu tái lập:** [`reports/report4/chart_data/member1/fig4_chart_longevity_weeks.csv`](file:///D:/music-chart-performance-analysis/reports/report4/chart_data/member1/fig4_chart_longevity_weeks.csv)  
* **Số quan sát:** $N = 10.887$ cặp bài hát × thị trường. Trục tung biểu diễn trên thang Logarithmic ($\log_{10}$).

#### Quan sát & Nhận định:
1. **Việt Nam có Độ bền Chart cao nhất (Highest Longevity):**
   * Số tuần trụ hạng trung bình của bài hát tại Việt Nam đạt **$21.66$ tuần**, cao **gấp đôi** thị trường Mỹ ($11.12$ tuần) và cao hơn hẳn Hàn Quốc ($14.50$ tuần).
   * Phân tích phân nhóm sinh tồn (Panel B): Ở VN, có tới **$21.75\%$** số bài hát trụ hạng bền bỉ từ $26$ tuần trở lên ($\ge 6$ tháng), trong đó $12.37\%$ bài trụ trên 1 năm ($52+$ tuần). Tỷ lệ bài rời chart ngay sau 1 tuần ở VN chỉ là $4.76\%$.
2. **Thị trường Mỹ có Tốc độ Đào thải Khắc nghiệt nhất (Fastest Turnover):**
   * Tại US, số tuần trụ hạng trung vị chỉ vỏn vẹn **$3$ tuần** (Q3 là $11$ tuần). Hơn **$44.98\%$** số ca khúc tại US văng khỏi BXH chỉ trong vòng $1\text{–}4$ tuần đầu tiên.
   * Điều này lý giải vì sao điểm trung vị của US lại cao hơn VN: Các bài hát ở US khi vào chart thường đạt thứ hạng tốt nhưng nhanh chóng out chart; trong khi ở VN, các bài hát bám trụ dai dẳng hàng chục tuần ở nửa sau bảng xếp hạng (hạng 120–180), kéo giá trị trung bình rank cả đời xuống thấp.

---

## 3. Ba Insights Nổi bật Định hướng cho Giai đoạn Xây dựng Mô hình (Member 4)

1. **Khuyến nghị Bắt buộc Phân tầng Mô hình theo Thị trường (Stratified Regression):**
   Do cơ chế đào thải của US (biến động cao, tuổi thọ ngắn) hoàn toàn đối lập với VN (trung thành cao, tuổi thọ dài), việc chạy một mô hình hồi quy OLS gộp chung (Pooled Model) sẽ gây ra hiện tượng thiên lệch cấu trúc (Structural Break). Member 4 cần chạy **3 mô hình hồi quy tách biệt** cho từng thị trường hoặc bắt buộc phải thêm **biến tương tác** ($\text{Feature} \times \text{Market}$).
2. **Hiện tượng Thiên lệch Chọn lọc & Sống sót (Selection & Survivorship Bias):**
   Tập dữ liệu US phản ánh các bài hát có sức sống thực sự đã vượt qua bộ lọc ban đầu của trang Totals (độ phủ tuần đạt $83.2\%$). Cần ghi nhận đây là giới hạn quan sát của phương pháp crawl theo hạt giống (Seed-based crawling), giúp loại bỏ bớt nhiễu từ các ca khúc vô danh.
3. **Phân biệt Rạch ròi giữa Vị trí Đỉnh cao ($Y_1 = \text{ChartScore}$) và Độ bền ($Y_2 = \text{weeks\_on\_chart}$):**
   $\text{ChartScore}$ đo lường "độ cao" của bài hát, trong khi `weeks_on_chart` đo lường "sức bền". Hai đại lượng này bắt nguồn từ cùng một lịch sử tuần, do đó `weeks_on_chart` **tuyệt đối không được làm biến độc lập $X$** khi dự đoán $Y_1$, nhưng là biến phụ trợ đắt giá cho phần Thảo luận mở rộng.

---

> [!NOTE]
> **Nguyên tắc phương pháp luận:** Mọi diễn giải trên chỉ phản ánh mối liên hệ thống kê quan sát (**Association**), không khẳng định mối quan hệ nhân quả (**Causation**) rằng đặc tính thị trường gây ra sự thay đổi điểm số.
