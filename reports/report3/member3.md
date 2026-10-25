# Báo cáo Kiểm kê Đặc trưng Ca từ & Thống kê Mô tả (Report 3 — Member 3)
**Học phần:** ADY201m — Music Chart Performance Analysis  
**Thành viên phụ trách:** Member 3 (Lyrics Feature Engineering & Natural Language Processing)  
**Ngày cập nhật:** 2026-10-26  
**Nguồn dữ liệu:** `data/raw/lyrics/` (1,909 tệp .txt) & `data/processed/lyrics_status.csv` ($N = 1.912$ tracks)

---

## 1. Tổng quan Trích xuất & Quy trình Chuẩn hóa Đa Ngôn ngữ
Phân hệ ca từ xử lý tập dữ liệu thô gồm $1.912$ ca khúc thuộc mẫu nghiên cứu đại diện cho 3 thị trường **Việt Nam (VN)**, **Hoa Kỳ (US)**, và **Hàn Quốc (KR)**.

### Quy tắc chuẩn hóa kỹ thuật:
1. **Làm sạch văn bản:** Loại bỏ toàn bộ nhãn section metadata (`[Chorus]`, `[Verse]`, `[Intro]`, v.v.), URL, và định dạng markdown trước khi tính toán độ dài từ và tần suất.
2. **Nhận diện điệp khúc (Chorus Detection):** Phát hiện số lần xuất hiện của các nhãn `[Chorus]` hoặc các khổ thơ (stanzas) lặp lại nguyên văn. Nếu không phát hiện cấu trúc điệp khúc rõ ràng, giá trị được gán `NULL` (không tự gán bằng 0).
3. **Phân tách từ (Tokenization):**
   - **Tiếng Anh (en):** Chuẩn hóa chữ thường, tách từ theo ranh giới từ vựng Unicode.
   - **Tiếng Việt (vi):** Tách từ theo âm tiết/từ đơn Unicode, loại bỏ dấu câu và khoảng trắng thừa.
   - **Tiếng Hàn (ko):** Tách từ theo cụm hình vị/ký tự Hangul.
4. **Từ điển đại từ (Pronoun Dictionary):** Áp dụng từ điển đại từ nhân xưng phiên bản hóa trong `src/lyrics/language_rules.yaml`.
5. **Tiêu đề trong ca từ (`title_word_in_lyrics`):** Lọc bỏ các từ chức năng (stopwords) trong tên bài hát; kiểm tra xem có ít nhất một từ nội dung cốt lõi của tiêu đề xuất hiện trong lời bài hát hay không.

---

## 2. Bảng Kiểm kê Dữ liệu Ca từ (Lyrics Inventory)

| Thị trường | Tổng bài hát trong mẫu | Thu thập thành công | Không tìm thấy (Not Found) | Tỷ lệ thành công (%) | Số từ trung bình (`word_count`) | Độ phong phú từ vựng (`lexical_diversity`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Việt Nam (VN)** | 608 | 607 | 1 | 99.84% | 451.0 | 0.3685 |
| **Hoa Kỳ (US)** | 797 | 797 | 0 | 100.00% | 425.2 | 0.3560 |
| **Hàn Quốc (KR)** | 693 | 691 | 2 | 99.71% | 328.7 | 0.4221 |
| **Toàn bộ (Overall)** | **1,912** | **1,909** | **3** | **99.84%** | **400.9** | **0.3814** |

*Ghi chú kiểm toán dữ liệu:*
- Ba ca khúc không tìm thấy lời (`not_found`): `1Px44tw80Q4rcCl8FxDGOi`, `6WY4wvlmgccWapnIg14Vy0`, và `7M30L99pePlQ3wh8IxVUsD`. Cả 3 bài này được bảo toàn trạng thái thiếu thông tin (`NaN`/`NULL`), không bị gán 0 sai lệch.

---

## 3. Từ điển Dữ liệu Đặc trưng Ca từ (Lyrics Data Dictionary)

| Trường dữ liệu | Kiểu DL | Đơn vị / Miền giá trị | Công thức & Phương pháp | Ý nghĩa Ngôn ngữ học / Cảm thụ |
| :--- | :--- | :--- | :--- | :--- |
| `word_count` | Integer | [12 - 2070] | Đếm số lượng word tokens sau khi làm sạch | Độ dài tổng thể của văn bản ca từ. |
| `unique_word_count` | Integer | [12 - 641] | Số lượng từ đơn duy nhất (lower case) | Quy mô vốn từ vựng được tác giả sử dụng. |
| `lexical_diversity` | Float | Tỷ số (0, 1] | $unique\_word\_count / word\_count$ | Độ đa dạng từ vựng; thấp thể hiện ca từ có tính lặp lại cao. |
| `repetition_ratio` | Float | Tỷ số [0, 1) | $1.0 - lexical\_diversity$ | Mức độ trùng lặp ca từ phục vụ bắt tai/ghi nhớ (catchiness). |
| `avg_word_length` | Float | Ký tự/token [2.1 - 13.2] | Tổng ký tự từ vựng / $word\_count$ | Độ phức tạp hình thái từ ngữ. |
| `line_count` | Integer | [3 - 193] | Số dòng lời bài hát không rỗng | Cấu trúc phân đoạn và độ dài nhịp câu hát. |
| `chorus_repetition_count` | Float | Số lần [0 - 18] hoặc NULL | Số lần điệp khúc được tái lặp | Cường độ nhấn mạnh điệp khúc của ca khúc. |
| `title_word_in_lyrics` | Boolean | `True` / `False` | Tồn tại từ nội dung của Title trong Lyrics | Tính liên kết giữa tên bài hát và nội dung bài hát. |
| `punctuation_ratio` | Float | Tỷ số [0, 0.18] | Ký tự dấu câu / Tổng ký tự | Mức độ ngắt nghỉ và tính biểu cảm cú pháp. |
| `pronoun_ratio` | Float | Tỷ số [0, 0.37] | Số đại từ / $word\_count$ | Mức độ hướng tâm lý cá nhân ("tôi", "em", "anh", "you", "me"). |

---

## 4. Bàn giao cho Member 4
1. File dữ liệu trích xuất hoàn chỉnh: `data/processed/lyrics_features.csv` ($1.912$ dòng).
2. Dữ liệu nguồn cho EDA: `reports/report3/lyrics_inventory.csv` và `reports/report3/lyrics_statistics.csv`.
3. Validation log: 8/8 test cases đạt trạng thái `PASS`.
4. Danh sách 3 bài thiếu lời để Member 4 lập báo cáo missingness và xử lý loại trừ mẫu khi phân tích complete-case.
