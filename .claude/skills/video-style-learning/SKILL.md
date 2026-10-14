---
name: video-style-learning
description: Dùng khi cần học phong cách dựng từ các video trong thư mục "video tham khảo" và viết/cập nhật library/style-guide.md (nhịp cắt, hook, chuyển cảnh, kiểu chữ, hiệu ứng, nhạc/SFX, màu).
---

# Học phong cách từ video tham khảo

Video tham khảo chỉ để học **kỹ thuật** (nhịp, chuyển cảnh, kiểu chữ). Không sao chép, không trích hình, nhạc, giọng hay câu chữ nguyên văn của chúng vào output. Không sửa, xoá, di chuyển file trong `video tham khảo`.

## Bước 1. Đo

```
vf style
```
Ghi `work/style/<tên>/stats.json` (thời lượng, số lần cắt, giây/cảnh, thời điểm cắt), `frames/` (1 khung/giây), `transcript.json`.

Nếu số lần cắt có vẻ thấp so với những gì thấy trong khung hình (hai cảnh liền nhau cùng độ sáng), chạy lại với `vf style --threshold 0.2`. Ghi rõ ngưỡng đã dùng vào style guide.

## Bước 2. Xem từng video

Với MỖI video, đọc `stats.json`, xem (Read) các ảnh trong `frames/` (xem kỹ 3 giây đầu) và đọc `transcript.json`. Ghi chú:

- Hook giây 0–3: mở bằng gì (câu hỏi, nỗi đau, kết quả, hành động), chữ hook ở đâu, bao nhiêu chữ, cắt cảnh đầu tiên lúc mấy giây.
- Nhịp: giây/cảnh trung bình, đoạn nào nhanh/chậm, có jump cut trong cùng một cảnh nói không.
- Chuyển cảnh: cắt thẳng, zoom punch, flash trắng, whip, rung.
- Chữ: vị trí (trên/giữa/dưới), font (có chân/không chân, độ đậm), màu chữ/viền/nền, số từ mỗi dòng phụ đề, có tô màu từ đang nói không, chữ hiện từng từ không.
- Hiệu ứng lặp lại và vị trí (mở đầu, chuyển ý, CTA).
- Nhạc/SFX: có nhạc nền không, nhạc to hay nhỏ so với giọng, SFX ở đâu (chỉ mô tả kiểu, không dùng lại nhạc).
- Bảng màu chủ đạo, ánh sáng, khung quay (cận mặt, cầm tay, góc trên).
- CTA: ở giây thứ mấy, nói gì, có chữ không.

## Bước 3. Viết `library/style-guide.md`

Đầu file ghi: "Trạng thái: CHỜ DUYỆT", ngày, danh sách video đã xem, ngưỡng dò cắt cảnh. Sau đó các mục:

1. Nhịp cắt trung bình (số liệu từ stats.json, từng video và trung bình)
2. Kiểu hook (giây 0–3)
3. Kiểu chuyển cảnh, map sang `Effect.kind` của pipeline (`zoom_punch`, `flash`, `shake`, `highlight`, `sfx`)
4. Vị trí, kiểu, font chữ cho overlay và phụ đề; đề xuất chỉnh `templates/caption_style.ass` (cỡ chữ, màu, MarginV) nếu cần
5. Kiểu chữ chuyển động (để dành cho Task 10, Remotion)
6. Hiệu ứng lặp lại
7. Kiểu nhạc/SFX (mô tả, gợi ý loại nhạc có bản quyền cần mua/tải vào `library/brand/`)
8. Bảng màu
9. **Nên bắt chước / Không bắt chước**: phần bắt chước chỉ nói về kỹ thuật. Phần không bắt chước ghi rõ: hình, nhạc, giọng, câu nói của video gốc; mọi claim trong `forbidden.txt` và `claims_pending.txt` mà video tham khảo có dùng.

Viết bằng tiếng Việt, cụ thể thành số khi có thể ("cắt cảnh mỗi 1.2–1.8 s", "chữ hook 5–7 từ, chiếm 1/3 trên").

## Bước 4. Dừng chờ duyệt

Báo người dùng tóm tắt 5–8 dòng và nhờ đọc, sửa `library/style-guide.md`. Chỉ khi người dùng xác nhận mới đổi trạng thái thành "ĐÃ DUYỆT <ngày>". Skill `video-batch-edit` dùng style guide này khi viết edl.
