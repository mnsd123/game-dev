---
name: smilee-video
description: Use when có source gốc mới trong thư mục Drive EDIT/"source gốc" của Smilee, hoặc người dùng nói "có source mới", "dựng video mới", "edit lô mới", "làm video từ source mới", hoặc gõ /smilee-video.
---

# Dựng video Smilee từ source gốc mới (trọn quy trình)

Điểm vào duy nhất mỗi khi có video quay mới. Kết quả: N file MP4 9:16 trong `EDIT/out/<lô>/` (chữ động bằng Remotion + ffmpeg, không phụ đề toàn bộ lời, chỉ highlight hook, cam kết, lợi ích, CTA), kèm ảnh tổng quan, `qa.json`, `review.csv`.

Chạy mọi lệnh ở gốc repo (thư mục có `vf.toml`). Không bao giờ sửa, xoá, di chuyển file trong `source gốc` và `video tham khảo`.

## 0. Kiểm tra môi trường (chỉ dừng khi thiếu)

- Có `vf.toml` và lệnh `vf` chạy được. Nếu thiếu thì làm theo README (venv, `pip install -e ".[dev]"`, `cd remotion && npm install`).
- Chưa có `remotion/node_modules` thì vẫn chạy được, nhưng chữ sẽ tĩnh. Báo người dùng một dòng.

## 1. Xem có gì mới

```
vf status
```
- Không có nguồn nào ghi `MỚI` → hỏi người dùng muốn dựng lại từ nguồn cũ hay chờ thêm nguồn. Dừng.
- Có lô cũ đã chấm điểm mà chưa học → chạy skill `video-learnings` TRƯỚC, để lô mới dùng bài học mới.

## 2. Tạo lô và brief

```
vf new auto
```
Lệnh tạo `jobs/lo-NN/brief.yaml`, `source_roles` điền sẵn các nguồn mới (mặc định `a_roll`).

Yêu cầu người dùng gõ kèm lệnh (ví dụ `/smilee-video cắt xuống dưới 1 phút 30 giây`) là ràng buộc cứng, ghi vào brief trước khi hỏi:
- Giới hạn thời lượng "dưới X giây" → `target_seconds` = X ÷ 1.1, làm tròn xuống (dưới 90 s → 80), vì pipeline cho phép ±10%. Ghi thêm X vào `must_keep`/ghi chú và kiểm tra mọi biến thể < X ở bước 5.
- Yêu cầu khác (số bản, kiểu hook, nguồn nào dùng) → điền thẳng vào trường tương ứng, không hỏi lại.

Hỏi người dùng MỘT lần, gộp vào một tin nhắn, mỗi mục kèm đề xuất mặc định để họ chỉ cần trả lời "ok":
- mục tiêu (awareness / education / conversion), thời lượng, số biến thể (mặc định 3)
- thông điệp một câu, CTA
- vai trò từng nguồn mới (a_roll có lời nói / b_roll chỉ có hình), ý hook nếu có

Nếu người dùng nói "tự quyết", tự điền dựa trên `library/product.md`, `library/hooks.md` rồi ghi vào brief.

## 3. Phân tích

```
vf analyze lo-NN
```
Đọc kết quả in ra: nguồn nào không có tiếng thì đổi vai trò thành `b_roll`.

## 4. Viết kịch bản dựng

**REQUIRED SUB-SKILL:** Làm theo skill `video-batch-edit`, bước 2–3, để viết `jobs/lo-NN/edl.json`: đọc đủ ngữ cảnh, mỗi biến thể một kiểu hook, chữ động chỉ ở đoạn quan trọng. 3 cam kết kết quả được tự phát hiện trong lời nói và tự highlight.

## 5. Render và tự kiểm tra

```
vf render lo-NN
```
- Có giới hạn thời lượng từ người dùng thì mọi biến thể phải ngắn hơn giới hạn đó; vượt thì cắt bớt đoạn trong edl và render lại.
- Xem từng `*_sheet.png` và `qa.json`. Biến thể lỗi thì sửa edl rồi chạy `vf render lo-NN --only <id>`.
- Bị `ClaimViolation` thì sửa chữ hoặc đoạn trong edl. Không sửa `forbidden.txt` hay `claims_pending.txt`.

## 6. Báo người dùng

- Đường dẫn `EDIT/out/lo-NN/`.
- Mỗi biến thể một dòng: `id — kiểu hook — câu hook — thời lượng — ý tưởng`.
- Nhắc chấm `score` (1–5) + `notes` trong `review.csv`. Lần sau có source mới, skill này tự chạy `video-learnings` trước (bước 1).

## Lỗi thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `vf status` không thấy file vừa bỏ vào Drive | Drive chưa đồng bộ hoặc chưa bật *Available offline*; kiểm tra `drive_root` trong `vf.toml` |
| Tiếng và hình lệch | Xoá `work/<tên file nguồn>/normalized.mp4` rồi chạy lại `vf analyze` |
| Chữ không động | Chưa `npm install` trong `remotion/`; hoặc thêm `--static-text` để chủ ý dùng chữ tĩnh |
| Phiên âm rỗng | Lần trước chạy `--no-transcribe`; chạy lại `vf analyze lo-NN` (tự phiên âm lại) |
| Chưa có `library/style-guide.md` đã duyệt | Vẫn dựng được, báo người dùng; muốn học phong cách thì chạy skill `video-style-learning` |
