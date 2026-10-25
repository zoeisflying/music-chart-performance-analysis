# BÁO CÁO KỸ THUẬT: CÁC TRỞ NGẠI VÀ GIẢI PHÁP THU THẬP DỮ LIỆU AUDIO TỪ YOUTUBE

> **Tài liệu phục vụ**: Báo cáo Đồ án / Khóa luận tốt nghiệp & Trình bày với Giảng viên hướng dẫn  
> **Dự án**: Music Chart Performance Analysis  
> **Giai đoạn**: Thu thập dữ liệu âm thanh (Audio Data Ingestion & Crawling)  
> **Quy mô mẫu**: 1,912 bài hát từ bảng xếp hạng âm nhạc (Spotify)  
> **Định dạng âm thanh đầu ra**: Uncompressed PCM WAV (chuẩn bị cho bước Trích xuất đặc trưng Audio Features với Librosa)

---

## 1. TỔNG QUAN HIỆN TRẠNG THU THẬP

Trong quá trình xây dựng tập dữ liệu phân tích âm nhạc từ Spotify sang YouTube, toàn bộ 1,912 bài hát được tìm kiếm và chấm điểm ánh xạ (YouTube Matching Pipeline) với thuật toán đa tiêu chí (Title Similarity, Duration Difference, Channel Authority, Identity Evidence).

* **Đợt tải tự động ban đầu (Baseline Run)**:
  * **Thành công**: **1,905 / 1,912 bài** (tỷ lệ thành công: **99.63%**).
  * **Thất bại**: **7 / 1,912 bài** (tỷ lệ lỗi: **0.37%**).
* **Đợt xử lý sự cố & Hoàn thiện (Remediation Run)**:
  * **Thành công sau xử lý**: **1,912 / 1,912 bài** (đạt tỷ lệ **100%**).
  * **Tổng số tệp âm thanh WAV thu thập**: 1,912 files trong `data/raw/audio/`.

Mặc dù tỷ lệ thất bại ban đầu chỉ là 0.37%, việc phân tích nguyên nhân gốc rễ (Root Cause Analysis) và xử lý 7 bài hát này mang lại những bài học kỹ thuật quan trọng về **tính bền vững của Data Pipeline (Pipeline Resilience)** khi thu thập dữ liệu từ các nền tảng Big Tech.

---

## 2. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (3 NHÓM TRỞ NGẠI CHÍNH)

Khi kiểm tra chéo giữa trình duyệt cá nhân và công cụ tự động (`yt-dlp`), nhóm nghiên cứu phát hiện sự khác biệt rõ rệt: **6/7 bài hát vẫn nghe được bình thường trên trình duyệt, nhưng script tự động lại báo lỗi**. 

Sau quá trình điều tra kỹ thuật (Reverse Engineering & Network Inspection), 3 nhóm nguyên nhân cốt lõi được xác định như sau:

```
                               CÁC TRỞ NGẠI THU THẬP AUDIO
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
   [NHÓM 1: 5 bài]                   [NHÓM 2: 1 bài]                   [NHÓM 3: 1 bài]
 Anti-Scraping / Bot Block          Age-Restricted (18+)              Dead Link / Takedown
 (Lauv, Disney, Morgan Wallen,      (Drake - Pussy & Millions)        (Panchiko - DEATHMETAL)
  Phạm Lịch, PAR SG)                                                  
         │                                 │                                 │
         ▼                                 ▼                                 ▼
 InnerTube Client Emulation         Candidate Fallback #2             Candidate Fallback &
 (player_client=android)           (Cash Money Records)              Official Studio Release
```

---

### Trở ngại 1: Cơ chế Anti-Bot & Nhận diện Client của YouTube (5 bài)
* **Các bài hát gặp lỗi**:
  1. Lauv – *Steal The Show* (`q7BmlOUk-II`)
  2. Disney – *Zoo* (`Xry6B0I3pT8`)
  3. Morgan Wallen – *Just In Case* (`cLnl73R9gMc`)
  4. Phạm Lịch – *Là Anh* (`Yd5FT7RaAM4`)
  5. PAR SG – *Lý Do Nào Để Quay Lại Với Nhau* (`OsY3OK4bdpg`)
* **Hiện tượng**:
  * Trình duyệt máy tính của người dùng mở nghe hoàn toàn bình thường.
  * Khi script tự động chạy với cấu hình mặc định của `yt-dlp`, YouTube trả về lỗi giả:
    ```
    ERROR: [youtube] q7BmlOUk-II: This video is not available
    ERROR: unable to download video data: HTTP Error 403: Forbidden
    ```
* **Bản chất kỹ thuật**:
  * YouTube sử dụng hệ thống tường lửa WAF và thuật toán nhận diện bot (Bot Detection Heuristics). Khi client mặc định của `yt-dlp` gửi request (giả lập Desktop Web Client `WEB`), YouTube kiểm tra HTTP Headers, TLS Fingerprint và thiếu vắng session người dùng thật.
  * Với các bài hát có bản quyền khắt khe hoặc lượng truy cập cao, YouTube cố tình trả về mã lỗi giả mạo (`This video is not available` hoặc `403 Forbidden`) nhằm đánh lừa bot dừng việc cào dữ liệu.
* **Giải pháp kỹ thuật (InnerTube Client Switching)**:
  * Thay vì tiếp tục dùng Web Client, can thiệp vào tầng InnerTube API của YouTube bằng cờ cấu hình:
    `--extractor-args "youtube:player_client=android"`
  * Client Android của YouTube sử dụng giao thức luồng (streaming protocol) khác biệt, không yêu cầu xác thực phiên web phức tạp. Nhờ đó, cả 5 bài hát đều phân giải metadata và tải luồng audio sạch (clean audio stream) thành công 100% mà không bị chặn.

---

### Trở ngại 2: Rào cản xác thực nội dung giới hạn độ tuổi 18+ (1 bài)
* **Bài hát gặp lỗi**: Drake & 21 Savage – *Pussy & Millions* (`8LpAtRIakkk`)
* **Hiện tượng**:
  * Người dùng mở trên trình duyệt xem được video bình thường.
  * Worker chạy tự động trên terminal báo lỗi:
    ```
    ERROR: [youtube] 8LpAtRIakkk: Sign in to confirm your age. This video may be inappropriate for some users.
    ```
* **Bản chất kỹ thuật**:
  * Video này chứa nội dung hoặc ngôn từ bị YouTube gắn cờ giới hạn độ tuổi (Age-Restricted 18+).
  * Trình duyệt của sinh viên xem được vì đã đăng nhập sẵn tài khoản Google cá nhân (đã xác minh > 18 tuổi).
  * Trong khi đó, script chạy trong terminal/server là môi trường ẩn danh (headless/unauthenticated), không mang theo cookie xác thực người dùng nên bị từ chối truy cập.
* **Giải pháp kỹ thuật (Multi-Candidate Ranking & Fallback)**:
  * Thay vì phụ thuộc vào cookie cá nhân (dễ gây rủi ro bảo mật và mất tính tái lập khi chạy trên máy khác/CI-CD), hệ thống kích hoạt cơ chế **Dự phòng ứng viên (Fallback Mechanism)**:
  * Truy xuất vào cơ sở dữ liệu ứng viên (`youtube_mapping`), chọn **Candidate #2** (`UCDv0tWLjDM`) được phát hành chính thức bởi hãng đĩa liên kết **Cash Money Records**.
  * Candidate #2 có thời lượng chuẩn studio đúng 242 giây (sai lệch 0 giây so với Spotify), âm thanh nguyên bản chất lượng cao và **không bị giới hạn độ tuổi**, cho phép pipeline tự động tải về hoàn chỉnh.

---

### Trở ngại 3: Video bị xóa / Gỡ bản quyền trên toàn cầu (1 bài)
* **Bài hát gặp lỗi**: Panchiko – *D>E>A>T>H>M>E>T>A>L* (`xlX7NwTq9Zo`)
* **Hiện tượng**:
  * Cả terminal lẫn trình duyệt web đều thông báo: `Video unavailable / This video is not available`.
* **Bản chất kỹ thuật (Content Churn & Takedown)**:
  * Đây là hiện tượng "link chết" thực tế trên môi trường mạng. Video ID ban đầu được upload bởi một kênh không chính thức và sau đó đã bị YouTube hoặc bên giữ bản quyền gỡ bỏ hoàn toàn khỏi nền tảng.
* **Giải pháp kỹ thuật (Dynamic Discovery & Canonical Track Resolution)**:
  * Hệ thống rà soát và kết nối đến bản ghi chuẩn hóa (Canonical Release) của nghệ sĩ trên YouTube Music (`3dPvWnEpJJI`, phát hành bởi Nettwerk Music Group đại diện cho ban nhạc Panchiko).
  * Video này có thời lượng 261.9 giây (khớp chuẩn tuyệt đối với bản ghi Spotify), đảm bảo tính chính xác cho các bước phân tích âm học sau này.

---

## 3. BẢNG DẪN CHỨNG ĐỐI SOÁT CHI TIẾT (EVIDENCE MATRIX)

Dưới đây là bảng tổng hợp chi tiết toàn bộ 7 trường hợp gặp trở ngại và kết quả xử lý thực tế:

| STT | Spotify Track ID | Tên bài hát | Nghệ sĩ | Video ID Ban Đầu | Mã lỗi ban đầu | Nguyên nhân cốt lõi | Biện pháp xử lý | Video ID Cuối cùng | Dung lượng WAV | Trạng thái cuối |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `6R5fYCySNHrqo4Og6O1ppn` | Steal The Show | Lauv | `q7BmlOUk-II` | `This video is not available` | Anti-Scraping Web Client Block | Chuyển sang Android Client InnerTube | `q7BmlOUk-II` | 34.9 MB | **Thành công** |
| 2 | `3vJIaiTIHxHhYafTSPNiH4` | Zoo | Disney / Shakira | `Xry6B0I3pT8` | `This video is not available` | Anti-Scraping Web Client Block | Chuyển sang Android Client InnerTube | `Xry6B0I3pT8` | 34.0 MB | **Thành công** |
| 3 | `5z0LSDpPpGwc2ZyJHpsE3J` | Just In Case | Morgan Wallen | `cLnl73R9gMc` | `HTTP 403 Forbidden` | Anti-Scraping Stream Block | Chuyển sang Android Client InnerTube | `cLnl73R9gMc` | 29.3 MB | **Thành công** |
| 4 | `2LhXE2daNpLVv9LYXvYm8F` | Là Anh | Phạm Lịch | `Yd5FT7RaAM4` | `This video is not available` | Anti-Scraping Web Client Block | Chuyển sang Android Client InnerTube | `Yd5FT7RaAM4` | 37.4 MB | **Thành công** |
| 5 | `11OxuU5y7ebAJyKaY8dOl0` | Lý Do Nào Để Quay Lại Với Nhau | PAR SG | `OsY3OK4bdpg` | `This video is not available` | Anti-Scraping Web Client Block | Chuyển sang Android Client InnerTube | `OsY3OK4bdpg` | 20.6 MB | **Thành công** |
| 6 | `2KLwPaRDOB87XOYAT2fgxh` | Pussy & Millions | Drake, 21 Savage | `8LpAtRIakkk` | `Sign in to confirm age (18+)` | Rào cản Cookie đăng nhập | Fallback sang Candidate #2 (Cash Money Records) | `UCDv0tWLjDM` | 42.7 MB | **Thành công** |
| 7 | `4sIFi8LpJWPvI5xviWFyA6` | D>E>A>T>H>M>E>T>A>L | Panchiko | `xlX7NwTq9Zo` | `Video unavailable (Dead Link)` | Video bị xóa/gỡ bản quyền | Thay thế bằng Official Studio Release (Nettwerk) | `3dPvWnEpJJI` | 46.2 MB | **Thành công** |

---

## 4. TÀI LIỆU DẪN CHỨNG & TẬP TIN LƯU TRỮ (AUDIT TRAIL)

Để phục vụ việc kiểm tra và bảo vệ trước Hội đồng chấm đồ án, toàn bộ lịch sử lỗi và mã nguồn xử lý được lưu trữ nguyên vẹn trong kho mã nguồn:

1. **Bằng chứng trạng thái ban đầu**:
   * Tập tin: [`data/raw/audio_download_log_initial.csv`](file:///d:/ADY/music-chart-performance-analysis/data/raw/audio_download_log_initial.csv)
   * Nội dung: Lưu lại chính xác nhật ký đợt 1 với 1,905 bài thành công và 7 bài thất bại kèm theo toàn bộ thông báo lỗi từ YouTube.
2. **Bằng chứng trạng thái nghiệm thu hoàn chỉnh**:
   * Tập tin: [`data/raw/audio_download_log.csv`](file:///d:/ADY/music-chart-performance-analysis/data/raw/audio_download_log.csv)
   * Nội dung: Cập nhật đầy đủ 1,912 bài hát với trạng thái `success`, số lần thử và đường dẫn file wav hoàn chỉnh.
3. **Kho lưu trữ tệp âm thanh thực tế**:
   * Thư mục: [`data/raw/audio/`](file:///d:/ADY/music-chart-performance-analysis/data/raw/audio/)
   * Số lượng tệp: **1,912 tệp `.wav`** (100% khớp với danh sách mẫu).
4. **Mã nguồn thực thi khắc phục sự cố**:
   * Tập tin: [`src/youtube/download_failed_audio.py`](file:///d:/ADY/music-chart-performance-analysis/src/youtube/download_failed_audio.py)
   * Kịch bản chính cải tiến: [`src/youtube/download_audio.py`](file:///d:/ADY/music-chart-performance-analysis/src/youtube/download_audio.py) (đã tích hợp client Android chống bot).

---

## 5. GIÁ TRỊ HỌC THUẬT & ĐÓNG GÓP KỸ THUẬT CHO ĐỒ ÁN

Khi trình bày với Giảng viên, sinh viên có thể tự tin nêu bật các giá trị kỹ thuật đã đạt được qua sự cố này:

1. **Tính kiên cường của hệ thống dữ liệu (Data Pipeline Resilience)**:
   * Không chấp nhận bỏ sót 7 bài hát (dẫn đến mất cân bằng mẫu hoặc thiếu dữ liệu phân tích), mà chủ động xây dựng quy trình phân tích lỗi và giải pháp bù trừ thông minh.
2. **Kỹ thuật vượt rào cản nền tảng (Platform Scraping Countermeasures)**:
   * Hiểu sâu cơ chế InnerTube API, phân biệt rõ giữa request ẩn danh của bot và session của người dùng trên trình duyệt.
   * Áp dụng thành công kỹ thuật Client Switching (`player_client=android`) để thu thập dữ liệu hợp lệ mà không cần lưu trữ Cookie nhạy cảm.
3. **Hiệu quả của kiến trúc Ánh xạ Đa ứng viên (Candidate Ranking Architecture)**:
   * Thiết kế ban đầu lưu trữ Top 5 ứng viên cho mỗi bài hát (`youtube_mapping`) đã phát huy tác dụng tối đa: khi ứng viên số 1 bị khóa tuổi hoặc bị xóa, hệ thống dễ dàng kích hoạt ứng viên số 2 mà không cần cào lại từ đầu toàn bộ hệ thống.
