---
name: video-learnings
description: Dùng khi người dùng nói "Chạy video-learnings" hoặc đã chấm điểm review.csv của một hay nhiều lô — tổng hợp điểm theo kiểu hook, cập nhật library/hooks.md và library/learnings.md để lô sau dựng tốt hơn.
---

# Học từ điểm chấm

## Bước 1. Lấy số liệu

```
vf learn
```
Lệnh đọc mọi `<drive_root>/out/*/review.csv` (gọi `vf.learn.summarize_reviews`) và in bảng: kiểu hook, số lần chấm, điểm TB, giữ chân 3 s TB. Dòng chưa có `score` bị bỏ qua.

Sau đó đọc trực tiếp từng `review.csv` để xem cột `notes`, `hook_text`, `views`, và `jobs/<lô>/edl.json` để biết biến thể đó được dựng thế nào (hook, nhịp, overlay, hiệu ứng).

## Bước 2. Cập nhật `library/hooks.md`

- Thay bảng xếp hạng bằng bảng `vf learn` vừa in, thêm cột "Ví dụ thắng": `hook_text` của biến thể điểm cao nhất mỗi kiểu (ghi kèm `lô/id`).
- Ghi ngày cập nhật ở đầu file.
- Dưới 3 lần chấm cho một kiểu hook thì ghi rõ "chưa đủ dữ liệu", không kết luận.

## Bước 3. Cập nhật `library/learnings.md`

- Mỗi bài học một dòng: `YYYY-MM-DD — bài học — bằng chứng (lô/id, điểm, notes hoặc retention)`.
- Chỉ ghi điều có bằng chứng trong review.csv. Không suy diễn từ một biến thể đơn lẻ trừ khi notes của người dùng nói thẳng.
- Retention 3 s (khi có) quan trọng hơn điểm cảm tính khi hai thứ mâu thuẫn; ghi rõ mâu thuẫn đó.
- Mốc tham khảo (blog ngành 2026, chỉ là định hướng): retention 3 s ≥ 55 % là hook mạnh, < 40 % là phải làm lại hook. Ưu tiên so các biến thể với nhau trong cùng tài khoản hơn là so với mốc này.
- Ghi bài học theo `preset` (cột trong edl) bên cạnh kiểu hook, để biết phong cách dựng nào thắng.
- **Không xoá bài học cũ**, trừ khi dữ liệu mới bác bỏ nó. Khi đó gạch ngang dòng cũ (`~~…~~`) và thêm dòng mới nêu bằng chứng bác bỏ.
- Không ghi bài học nào khuyến khích dùng cụm trong `forbidden.txt` hoặc `claims_pending.txt`, dù biến thể đó điểm cao.

## Bước 4. Báo người dùng

Tóm tắt 3–5 dòng: kiểu hook đang thắng, điều sẽ làm khác ở lô sau, và chỗ còn thiếu dữ liệu (ví dụ chưa nhập views/retention).
