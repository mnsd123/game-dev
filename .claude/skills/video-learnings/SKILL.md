---
name: video-learnings
description: Dùng khi người dùng nói "Chạy video-learnings" hoặc đã chấm điểm / nhập số liệu TikTok vào review.csv của một hay nhiều lô — tổng hợp theo preset, kiểu hook, độ dài, cập nhật library/learnings-stats.md, hooks.md, learnings.md để lô sau dựng tốt hơn.
---

# Học từ điểm chấm

## Bước 1. Lấy số liệu

```
vf learn --write
```
Lệnh đọc mọi `<drive_root>/out/*/review.csv`, in bảng theo kiểu hook và ghi `library/learnings-stats.md`: điểm TB, giữ chân 3 s, số liệu TikTok (`view_2s`, `view_6s`, `avg_watch_s`, `ctr`, `cvr`, `cost_per_order`) theo **kiểu hook, preset, preset × kiểu hook, nhóm độ dài** (≤45 s, 46–75 s, >75 s) + top 3 biến thể. Dòng chưa có `score` bị bỏ qua; thiếu cột số liệu → "—".

Sau đó đọc trực tiếp từng `review.csv` (cột `notes`, `hook_text`, `preset`, `length_s`) và `jobs/<lô>/edl.json` để biết biến thể được dựng thế nào (hook, chương, nhịp, overlay, đồ hoạ, SFX).

## Bước 2. Cập nhật `library/hooks.md`

- Thay bảng xếp hạng bằng bảng `vf learn` vừa in, thêm cột "Ví dụ thắng": `hook_text` của biến thể điểm cao nhất mỗi kiểu (ghi kèm `lô/id`).
- Ghi ngày cập nhật ở đầu file.
- Dưới 3 lần chấm cho một kiểu hook thì ghi rõ "chưa đủ dữ liệu", không kết luận.

## Bước 3. Cập nhật `library/learnings.md`

- Mỗi bài học một dòng: `YYYY-MM-DD — bài học — bằng chứng (lô/id, điểm, notes hoặc retention)`.
- Chỉ ghi điều có bằng chứng trong review.csv. Không suy diễn từ một biến thể đơn lẻ trừ khi notes của người dùng nói thẳng.
- Retention 3 s (khi có) quan trọng hơn điểm cảm tính khi hai thứ mâu thuẫn; ghi rõ mâu thuẫn đó.
- Mốc tham khảo (blog ngành 2026, chỉ là định hướng): retention 3 s ≥ 55 % là hook mạnh, < 40 % là phải làm lại hook. Ưu tiên so các biến thể với nhau trong cùng tài khoản hơn là so với mốc này.
- Ghi bài học theo `preset` bên cạnh kiểu hook và độ dài, để biết phong cách dựng nào thắng. Preset/kiểu hook thắng rõ (≥ 3 lần chấm) → đề xuất dùng nhiều hơn ở lô sau; thua rõ → ghi điều cần sửa trong preset đó (chữ, nhịp, đồ hoạ) để cập nhật `library/style-guide.md` mục 6 — hỏi người dùng trước khi sửa style guide.
- **Không xoá bài học cũ**, trừ khi dữ liệu mới bác bỏ nó. Khi đó gạch ngang dòng cũ (`~~…~~`) và thêm dòng mới nêu bằng chứng bác bỏ.

## Bước 4. Báo người dùng

Tóm tắt 3–5 dòng: preset và kiểu hook đang thắng, độ dài hiệu quả, điều sẽ làm khác ở lô sau, và chỗ còn thiếu dữ liệu (ví dụ chưa nhập số liệu TikTok, notes chung cho cả lô thay vì riêng từng biến thể).
