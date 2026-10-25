# Thu thập Lyrics

## Mục đích

Thư mục này chứa quy trình thu thập và kiểm tra lyrics của các bài hát.

Member 3 chịu trách nhiệm:
- Thu thập lyrics cho các bài hát được lấy mẫu.
- Đối chiếu lyrics với đúng tên bài hát và nghệ sĩ.
- Ghi nhận ngôn ngữ và trạng thái thu thập lyrics.
- Lưu lyrics thô bằng `spotify_track_id`.
- Chuẩn bị metadata cho bảng `lyrics_features`.

## Input

Quy trình thu thập lyrics nhận danh sách bài hát mẫu từ Member 4.

Các cột đầu vào:

- `spotify_track_id`
- `title`
- `artist`
- `market`
- `year`
- `quarter`
- `rank_stratum`

Ví dụ:

```csv
spotify_track_id,title,artist,market,year,quarter,rank_stratum
abc123,Example Song,Example Artist,Vietnam,2025,Q1,top_10
Lưu ý: dữ liệu trên chỉ là ví dụ. Danh sách bài hát chính thức sẽ được nhận từ Member 4.

Lưu Lyrics Thô
Lyrics thô được lưu tại:
data/raw/lyrics/<spotify_track_id>.txt

Ví dụ:
data/raw/lyrics/abc123.txt
Sử dụng spotify_track_id làm tên file vì đây là mã định danh được sử dụng chung giữa các pipeline của project.

Trạng thái Lyrics
Mỗi bài hát cần có một trạng thái thu thập:
pending - đang chờ xử lý
processing - đang được xử lý
success - đã thu thập và kiểm tra thành công
failed - quá trình thu thập bị lỗi
not_found - không tìm thấy lyrics
rejected - tìm thấy kết quả nhưng không khớp với bài hát hoặc nghệ sĩ cần tìm
Metadata

Quy trình thu thập cần ghi nhận:
spotify_track_id
language
source
lyrics_status
collection_status
Quy tắc quan trọng
Tìm kiếm bằng tên bài hát và tên nghệ sĩ.
Kiểm tra kết quả có đúng bài hát và nghệ sĩ cần tìm hay không.
Chưa tính các NLP features trong giai đoạn thu thập lyrics.
Chưa sử dụng BERT, Transformers, embeddings, sentiment analysis hoặc topic modeling ở giai đoạn này.
Lyrics thô được lưu dưới dạng file .txt.
Những bài không tìm thấy lyrics vẫn phải được ghi nhận với trạng thái phù hợp.

Bàn giao cho Member 4
Sau khi hoàn thành việc thu thập, Member 3 bàn giao:
spotify_track_id
trạng thái lyrics
ngôn ngữ
nguồn lyrics
danh sách bài hát có lyrics
danh sách bài hát không có lyrics
các file lyrics thô