# Hướng dẫn: chuyển quy trình edit video Smilee sang Claude Code

## 1. Quy trình đã chốt

```
[Một lần]  Cài đặt → Học phong cách từ video tham khảo → Duyệt style-guide
[Mỗi lô]   Bỏ video gốc vào Drive → Điền brief → Claude phân tích → Claude viết kịch bản dựng (edl)
           → Render N biến thể → QA tự động → Bạn xem + chấm điểm → Claude học
[Giai đoạn 2] Thêm lớp motion graphic kiểu Vox bằng Remotion
```

Claude làm: cắt khoảng lặng, chọn hook, ghép đoạn từ nhiều video gốc, phụ đề, chữ, hiệu ứng, cân âm lượng, kiểm tra từ cấm, xuất nhiều bản.
Bạn làm: quay, bỏ video vào Drive, điền brief, xem và chấm điểm.

## 2. Tình trạng tài nguyên trong Drive (kiểm tra ngày 13/10/2026)

| Thứ cần | Tình trạng |
|---|---|
| Hồ sơ sản phẩm | Có: `Thông tin sản phẩm smilee.docx`. Còn nhiều mục `[CẦN XÁC NHẬN]` (xem mục 3) |
| Video gốc | Có 1 file: `source gốc 1 quyenqui.mov` (khoảng 172 MB). Bạn từng nói có 2 nguồn nên hãy thêm file còn lại |
| Video tham khảo | Có 4 file mp4 tải từ TikTok (tên `snaptik...`) |
| Brand kit (font, logo, mã màu, nhạc, SFX) | Chưa có |
| Ảnh/clip sản phẩm, ảnh chụp đánh giá, before/after thật | Chưa có |
| Brief cho lô đầu | Chưa có (Claude Code sẽ tạo file mẫu để bạn điền) |

## 3. Cần chốt trước khi chạy ads (không chặn việc dựng thử)

Hồ sơ sản phẩm ghi 3 cam kết: "trắng sau 5–7 ngày", "bật 3–4 tone", "trắng như răng sứ". Chúng chưa có bằng chứng đi kèm. Pipeline sẽ **không đưa các claim này lên chữ trên màn hình** cho tới khi bạn bổ sung bằng chứng. Việc cần làm:

1. Có kết quả test hoặc before/after thật (ghi rõ số ngày, ánh sáng giống nhau).
2. Chụp màn hình đánh giá 4.8 sao và số lượt bán, ghi ngày chụp.
3. Xin đồng ý của khách trước khi dùng review hay ảnh của họ.
4. Xác nhận có cần kiêng cà phê/trà sau khi dùng không.

Video tham khảo chỉ dùng để học nhịp dựng, kiểu chuyển cảnh và kiểu chữ. Đừng dùng lại hình, nhạc hay giọng của chúng trong video của bạn.

## 4. Các bước chuyển sang Claude Code

**Bước 1. Cài công cụ trên máy bạn** (render video nặng nên chạy trên máy, không chạy trên cloud)

- Claude Code: cài theo hướng dẫn chính thức tại https://docs.claude.com/en/docs/claude-code/overview (bản desktop hoặc dòng lệnh đều được).
- ffmpeg, Python 3.11, Node 20:
  - Windows: `winget install Gyan.FFmpeg`, `winget install Python.Python.3.11`, `winget install OpenJS.NodeJS.LTS`
  - Mac: `brew install ffmpeg python@3.11 node`
- Google Drive for Desktop: cài và đăng nhập đúng tài khoản `mailhoang0720@gmail.com`.

**Bước 2. Đưa thư mục EDIT xuống máy**

Trong Drive for Desktop, bấm chuột phải thư mục `EDIT` → *Available offline* (Có sẵn khi ngoại tuyến). Việc này giúp Claude đọc video trực tiếp như file thường. Ghi lại đường dẫn, ví dụ `G:\My Drive\EDIT` hoặc `~/Library/CloudStorage/GoogleDrive-.../My Drive/EDIT`.

**Bước 3. Tạo thư mục dự án trên ổ máy, không đặt trong Drive**

Tạo `video-factory` ở nơi bình thường, ví dụ `C:\Users\<tên>\video-factory`. Code và file tạm không nên nằm trong Drive vì đồng bộ sẽ rất chậm. Chỉ video (gốc, tham khảo, thành phẩm) nằm trong Drive.

Chép 2 file này vào `video-factory/docs/superpowers/plans/`: `2026-10-13-video-batch-edit.md` và file này. Cả hai đang ở Project "auto editting".

**Bước 4. Bật plugin**

Mở Claude Code trong `video-factory`, gõ `/plugin` và kiểm tra các plugin sau đã bật: superpowers, ffmpeg-llm, video-cleanup, watch-video, video-shotcraft. Nếu chưa thấy **Social Media Skills** và **Remotion** thì cài thêm (Remotion chỉ cần cho giai đoạn 2).

**Bước 5. Dán lệnh đầu tiên**

Mở Claude Code tại `video-factory` và dán:

```
Đọc docs/superpowers/plans/2026-10-13-video-batch-edit.md và HUONG-DAN-CLAUDE-CODE.md.
Thư mục Drive của tôi là: <DÁN ĐƯỜNG DẪN EDIT Ở BƯỚC 2>.
Dùng superpowers:subagent-driven-development để thực thi lần lượt Task 0 đến Task 9.
Trong Task 1, chuyển file "Thông tin sản phẩm smilee.docx" trong thư mục Drive thành library/product.md, giữ nguyên các dấu [CẦN XÁC NHẬN].
Dừng lại sau Task 7 để tôi chạy thử 1 video, và sau Task 9 để tôi duyệt style-guide.md.
Không xoá hay sửa file trong "source gốc" và "video tham khảo".
```

**Bước 6. Duyệt phong cách (sau Task 9)**

Claude xem 4 video tham khảo, đo nhịp cắt, rồi viết `library/style-guide.md`. Bạn đọc, sửa chỗ nào không giống ý bạn muốn, rồi xác nhận.

**Bước 7. Điền brief cho lô đầu và chạy thử**

Claude tạo `jobs/lo-01/brief.yaml` từ mẫu. Bạn điền: nền tảng, độ dài, số biến thể (đề xuất 3), mục tiêu (nhận diện / giáo dục / chuyển đổi), thông điệp một câu, CTA, vai trò từng video gốc, ý hook. Sau đó gõ:

```
Edit lô lo-01 theo skill video-batch-edit.
```

Claude sẽ phân tích, viết kịch bản dựng, render 3 biến thể vào `EDIT/out/lo-01/` (Drive tự đồng bộ), kèm ảnh tổng quan mỗi video và file `review.csv`.

**Bước 8. Chấm điểm để Claude học**

Xem video, điền cột `score` (1–5) và `notes` trong `review.csv`. Sau đó gõ:

```
Chạy video-learnings cho các lô đã chấm.
```

Lặp lại bước 7–8 khoảng 3 lô cho tới khi hài lòng. Khi đã đăng, nhập thêm số view và tỷ lệ xem qua 3 giây đầu vào `review.csv` để Claude học hook nào giữ người xem tốt nhất.

**Bước 9. Chạy hàng loạt và nâng cấp**

Bỏ nhiều video vào `source gốc` và tạo nhiều brief, rồi gõ `Edit lô lo-02, lo-03, lo-04`. Khi bạn hài lòng với bản pilot, nhắn "làm Task 10" để thêm motion graphic kiểu Vox (highlight chữ, nhãn chú thích, chữ chạy từng từ).

## 5. Gặp lỗi thì làm gì

| Triệu chứng | Cách xử lý |
|---|---|
| Claude không thấy file video | Kiểm tra đã bật *Available offline* và đường dẫn trong `vf.toml` đúng |
| Tiếng và hình lệch nhau | Báo Claude: "chuẩn hoá lại nguồn này", file `.mov` iPhone hay dính lỗi khung hình biến thiên |
| Render bị chặn vì "ClaimViolation" | Đúng chủ đích: chữ trên màn hình có cụm trong `library/forbidden.txt`. Sửa chữ, không sửa danh sách |
| Phụ đề sai chữ | Mở `work/<nguồn>/transcript.json`, sửa từ sai, rồi chạy lại `vf render` |
| Lệnh ffmpeg lỗi | Nhờ Claude gọi agent `ffmpeg-expert` |
