---
name: video-batch-edit
description: Dùng khi người dùng nói "Edit lô <lô>" hoặc muốn dựng hàng loạt video Smilee từ video gốc trong Drive — phân tích nguồn, viết edl.json nhiều biến thể khác kiểu hook, render 9:16, QA, báo kết quả.
---

# Edit video hàng loạt cho Smilee

Mỗi lô nằm ở `jobs/<lô>/` (brief.yaml, edl.json). Video nguồn ở `<drive_root>/source gốc/`, output ở `<drive_root>/out/<lô>/`. Không bao giờ sửa, xoá hay di chuyển file trong `source gốc` và `video tham khảo`.

## Bước 1. Phân tích

```
vf analyze <lô>
```
Nếu `jobs/<lô>/brief.yaml` chưa có thì chạy `vf new <lô>`, rồi DỪNG và nhờ người dùng điền brief.
Nguồn chỉ có hình (b-roll) vẫn chạy được: transcript rỗng, biến thể dùng nguồn đó tự bỏ phụ đề.

## Bước 2. Đọc đủ ngữ cảnh trước khi viết edl

Đọc hết, không đọc lướt:
1. `jobs/<lô>/brief.yaml`
2. `library/product.md`, đặc biệt mục 6 "Những điều KHÔNG được nói" và mọi dòng còn `[CẦN XÁC NHẬN]`
3. `library/style-guide.md` (nhịp cắt, kiểu chữ, hiệu ứng). Nếu file còn ghi "chưa duyệt" thì báo người dùng rằng lô này dựng theo mặc định.
4. `library/hooks.md` và `library/learnings.md`: ưu tiên kiểu hook đang thắng, tránh điều đã bị chấm thấp
5. `library/forbidden.txt` và `library/claims_pending.txt`
6. `work/<tên nguồn>/transcript.json`, `keep.json`, `info.json` của MỌI nguồn

## Bước 3. Viết `jobs/<lô>/edl.json`

Định dạng: xem `templates/edl.example.json` và `vf/edl.py`. Quy tắc:

- Đúng `brief.variants` biến thể, **mỗi biến thể một kiểu hook khác nhau**, chọn trong: `pain` (nỗi đau), `question` (câu hỏi), `result_first` (kết quả trước), `contrarian` (phản đề), `cost_compare` (so sánh chi phí). Ghi `hook_type` đúng tên đó.
- Hook ≤ 3 s, phải là câu có lực nhất cho kiểu hook đó; có thể lấy từ giữa video gốc.
- Tổng thời lượng mỗi biến thể trong `target_seconds ± 10%`.
- Chỉ lấy đoạn nằm trong `keep.json` (đã bỏ khoảng lặng), cắt ở ranh giới từ trong transcript, không cắt giữa từ.
- `segments[].source` là tên file nguồn (kèm đuôi). Dùng nguồn theo `source_roles`: `a_roll` mang lời nói, `b_roll` chèn minh hoạ.
- Tôn trọng `must_keep`, `must_cut`, `forbidden` của brief.
- **Không chọn đoạn mà người nói nói ra claim trong `claims_pending.txt`** (5–7 ngày, 3–4 tone, như sứ, 4.8 sao, lượt bán, sinh hoạt bình thường…) hoặc cụm trong `forbidden.txt`. Phụ đề sẽ hiện đúng chữ đó và render bị chặn. Cắt bỏ đoạn đó, không né bằng cách tắt phụ đề.
- Overlay ngắn (≤ 7 từ), không chứa giá/ưu đãi trong 3 s đầu nếu `goal` là `awareness`. So sánh với nha khoa chỉ nói chi phí và sự tiện lợi, không dìm nha khoa, không nêu tên phòng khám/đối thủ.
- Không tự bịa before/after, review, số liệu. Chỉ dùng tư liệu có thật trong `library/assets/`.
- `music` và `effects[].asset` chỉ trỏ tới file có bản quyền trong `library/brand/` hoặc `library/assets/`. Không dùng hình, nhạc, giọng của video tham khảo.
- `rationale`: một câu nói vì sao biến thể này có thể thắng.

## Bước 4. Render

```
vf render <lô>
```
Mã thoát ≠ 0 nghĩa là có biến thể bị chặn (`CHẶN … ClaimViolation`) hoặc lỗi ffmpeg. Với ClaimViolation: **sửa chữ/đoạn trong edl, không sửa `forbidden.txt` hay `claims_pending.txt`.** Lệnh ffmpeg lỗi thì dùng agent `ffmpeg-expert`.

## Bước 5. Tự kiểm tra

- Xem từng `<variant>_sheet.png` (Read ảnh): bố cục, chữ có bị che mặt không, chữ đủ dấu không, nguồn ngang có nền blur đúng không.
- Đọc `qa.json`: mọi `duration_ok`, `size_ok`, `loudness_ok` phải True và `notes` rỗng.
- Biến thể nào lỗi thì sửa edl rồi chạy lại riêng nó: `vf render <lô> --only <id>`.

## Bước 6. Báo người dùng

Liệt kê file trong `<drive_root>/out/<lô>/`, mỗi biến thể một dòng: `id — kiểu hook — câu hook — thời lượng — ý tưởng`. Nhắc người dùng điền cột `score` (1–5) và `notes` trong `review.csv`, sau đó gõ "Chạy video-learnings cho các lô đã chấm".
