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
3. `library/style-guide.md` (nhịp cắt, kiểu chữ, hiệu ứng). Nếu file chưa có dòng "ĐÃ DUYỆT" thì báo người dùng rằng lô này dựng theo mặc định.
4. `library/hooks.md` và `library/learnings.md`: ưu tiên kiểu hook đang thắng, tránh điều đã bị chấm thấp
5. `library/forbidden.txt` và `library/claims_pending.txt`
6. `work/<tên nguồn>/transcript.json`, `keep.json`, `info.json`, `scenes.json` của MỌI nguồn
7. Ảnh ghép khung hình của nguồn (ví dụ `ffmpeg -i work/<nguồn>/normalized.mp4 -vf "fps=1/5,scale=216:384,tile=9x3" -frames:v 1 sheet.jpg`, rồi Read ảnh) để biết cảnh nào có mặt, sản phẩm, đèn

## Bước 3. Viết `jobs/<lô>/edl.json`

Định dạng: xem `templates/edl.example.json` và `vf/edl.py`. Quy tắc:

- Đúng `brief.variants` biến thể, **mỗi biến thể một kiểu hook khác nhau**, chọn trong: `pain` (nỗi đau), `question` (câu hỏi), `result_first` (kết quả trước), `contrarian` (phản đề), `cost_compare` (so sánh chi phí). Ghi `hook_type` đúng tên đó.
- Hook ≤ 3 s, phải là câu có lực nhất cho kiểu hook đó; có thể lấy từ giữa video gốc.
- Tổng thời lượng mỗi biến thể trong `target_seconds ± 10%`.
- Chỉ lấy đoạn nằm trong `keep.json` (đã bỏ khoảng lặng), cắt ở ranh giới từ trong transcript, không cắt giữa từ.
- **Cắt theo cảnh (chống "vấp hình")**: đối chiếu mép mỗi đoạn với `scenes.json`. Không để mép đoạn cách điểm chuyển cảnh < 0.5 s (sẽ lộ vài khung hình của cảnh khác). Ưu tiên chọn mép đoạn trùng điểm chuyển cảnh hoặc khoảng lặng giữa hai từ gần đó. Render tự giữ khung hình kề bên cho mẩu còn sót và tự phóng to xen kẽ (×1.12) khi hai đoạn liên tiếp cắt nhảy trong cùng một cảnh.
- **Không lấy đoạn người nói nói ra cụm cấm** dù không đặt chữ lên (lo-01: hai câu "đảm bảo", câu "top 1 thị trường 3 năm liên tục" chưa có bằng chứng, đoạn mời livestream của KOL).
- `segments[].source` là tên file nguồn (kèm đuôi). Dùng nguồn theo `source_roles`: `a_roll` mang lời nói, `b_roll` chèn minh hoạ.
- Tôn trọng `must_keep`, `must_cut`, `forbidden` của brief.
- **Không lấy đoạn có ô chèn/trích clip của người sáng tạo, người nổi tiếng khác** (clip KOL hay chèn video reaction): hồ sơ sản phẩm mục 6 cấm dùng hình ảnh của họ. Xem ảnh ghép khung hình để phát hiện (lo-02: đoạn 22.98–29.36 s).
- **Nguồn trong `brief.text_sources` (đã có chữ in sẵn)**: xem khung hình từng giây của các đoạn định dùng, ghi các khoảng KHÔNG có chữ in sẵn vào `brief.text_free` (giờ nguồn). Chỉ đặt chữ trong các khoảng đó; render tự bỏ chữ nằm ngoài. Không có `text_free` = không thêm chữ nào cho nguồn đó.
- **Nhịp cắt (style guide mục 1)**: mỗi cảnh trong output ≥ 1.2 s, nhắm 2–4 s. Bỏ các chuỗi dựng nhanh của nguồn (cảnh < 1 s, ví dụ nhật ký 7 ngày) — thay bằng một cảnh dài + thẻ đếm ngày.
- **Thẻ chữ theo style guide (mục 4–5)**: `style: "lower"` = thẻ hai dòng nền tím mận (`text` dòng chính hồng viết hoa 2–5 từ, `sub` dòng phụ trắng ≤ 7 từ) — kiểu chính, dùng cho nỗi đau/lợi ích/CTA; `style: "tag"` = nhãn hồng nghiêng ngắn ("TRƯỚC", "SAU ✓").
- **Phong cách Vox (style guide mục 10) — ưu tiên**: chỉ thêm đồ hoạ ở đoạn nguồn trơn; đoạn nguồn đã có chữ, sticker, khoanh hay hình minh hoạ sẵn thì để nguyên. Cận cảnh răng vàng: `effects` `{"kind": "zoom_to", "at", "duration", "zoom": 1.6, "track": "teeth"}` + `graphics` `{"kind": "callout", "label": "Răng ố vàng", "cx": 0.5, "cy": 0.5, "rx": 0.36, "ry": 0.085}` cùng khoảng thời gian (ống kính bám răng nên vòng khoanh để giữa khung). Cảnh trước/sau gốc để trọn; sau đó `{"kind": "collage", "stills": [{"source", "t", "crop": [x0,y0,x1,y1], "label": "Trước"}, {..., "label": "Sau 7 ngày"}]}` trên đoạn nói chuyện trơn 3–4 s. Chữ bổ sung dùng `style: "vox"`.
- **Motion graphic minh hoạ đèn** (chỉ khi nguồn KHÔNG có cảnh đèn/chữ về đèn): `{"kind": "teeth", "start", "end", "split"}` = hàm răng vector, đèn xanh quét làm răng vàng → trắng rồi đèn đỏ dịu nướu (split = tỉ lệ thời lượng pha xanh), đặt đúng lúc người nói nói về đèn, kèm `light` xanh/đỏ để có vầng sáng. `{"kind": "counter", "label": "dùng đều mỗi ngày"}` = thẻ toàn màn hình đếm NGÀY 1 → 7, 1–1.5 s, đặt giữa cảnh before và after.
- **Không phụ đề toàn bộ lời nói** (`captions` mặc định `false`). Chỉ đặt chữ động ở đoạn quan trọng: hook (giây 0–3), cam kết, lợi ích chính (15 phút, tại nhà, không cần hẹn lịch, ~800k so với ~8 triệu), CTA. Khoảng 3–6 overlay mỗi biến thể là đủ.
- **3 cam kết kết quả** ("trắng sau 5–7 ngày", "bật 3–4 tone", "trắng như sứ") được pipeline **tự phát hiện trong lời nói và tự thêm thẻ highlight** (`library/commitments.txt`). Theo quyết định của người dùng ngày 2026-10-13, chúng KHÔNG bị chặn. Nên ưu tiên giữ các đoạn người nói nói ra cam kết này. Không cần tự thêm overlay cho chúng, trừ khi muốn đổi vị trí/chữ (overlay trong edl cùng chữ, trùng thời gian sẽ thay cho bản tự động).
- **Không chọn đoạn mà người nói nói ra claim còn trong `claims_pending.txt`** (4.8 sao, lượt bán, sinh hoạt bình thường…) nếu định đặt chữ lên đoạn đó, và không đưa cụm trong `forbidden.txt` lên chữ. Render sẽ bị chặn.
- Overlay ngắn (≤ 7 từ), không chứa giá/ưu đãi trong 3 s đầu nếu `goal` là `awareness`.
- Mỗi overlay chọn `style` và `animation`:
  - `style`: `hook` (chữ trắng viền đen, to), `commit` (thẻ trắng + vệt highlight), `label` (nhãn màu nhỏ), `cta` (nút màu, đập nhẹ), `plain`.
  - `animation`: `word_by_word` (hiện từng từ, hợp hook), `pop` (bật lên), `highlight` (vệt bút dạ quét qua `emphasis`, rỗng = cả câu), `slide` (trượt vào, hợp nhãn), `none`.
  - Ví dụ: `{"text": "15 phút tại nhà", "start": 4.0, "end": 5.2, "position": "top", "style": "label", "animation": "slide"}`.
  - `position` chỉ là gợi ý: render dùng OpenCV tìm mặt + vùng nhiều chi tiết (sản phẩm, tay) rồi tự đặt `y` để chữ không che mặt/sản phẩm, không đè chữ khác, chừa 20 % đáy cho giao diện TikTok. Muốn cố định thì ghi `"y": 0.1` (mép trên, tỉ lệ chiều cao).
  - Font: file đầu tiên trong `library/brand/` (mặc định Montserrat ExtraBold, đủ dấu tiếng Việt). Chữ hook/plain có viền đen + nền tối mờ; nhãn/CTA nền hồng Smilee; thẻ cam kết nền trắng.
- **Hiệu ứng minh hoạ** (`graphics`, timeline output) — đặt đúng lúc người nói nói tới:
  - Đèn: `{"kind": "light", "color": "blue", "label": "Đèn xanh · 10 phút", "start": …, "end": …}` → viền sáng xanh/đỏ nhịp thở quanh khung, hạt sáng, thẻ đồng hồ chạy vòng. Dùng `"red"` cho đèn đỏ (dịu nướu). Nhãn ≤ 4 từ.
  - Răng: `{"kind": "whiten", "start": …, "end": …}` → icon răng vàng → trắng, "Trước"/"Sau", thanh màu răng, ghi **"Hình minh họa"**. Đây là đồ hoạ minh hoạ, KHÔNG thay before/after thật; không bỏ dòng "Hình minh họa", không thêm số tone/số ngày lên icon. Before/after thật chỉ dùng tư liệu trong `library/assets/`.
  - Nhãn của `graphics` cũng bị kiểm tra cụm cấm như chữ.
- Chuyển cảnh cơ bản bằng `effects`: `zoom_punch` ở chỗ nhấn, `shake` hiếm khi dùng. **Không dùng `flash`** (khung trắng trông như lỗi hình — feedback lo-01). So sánh với nha khoa chỉ nói chi phí và sự tiện lợi, không dìm nha khoa, không nêu tên phòng khám/đối thủ.
- Không tự bịa before/after, review, số liệu. Chỉ dùng tư liệu có thật trong `library/assets/`.
- `music` và `effects[].asset` chỉ trỏ tới file có bản quyền trong `library/brand/` hoặc `library/assets/`. Không dùng hình, nhạc, giọng của video tham khảo.
- `rationale`: một câu nói vì sao biến thể này có thể thắng.

## Bước 4. Render

```
vf render <lô>
```
Chữ động render bằng Remotion (thư mục `remotion/`, nền trong suốt) rồi ffmpeg chồng lên video. Nếu chưa cài Remotion, lệnh tự vẽ chữ tĩnh bằng ffmpeg (`--static-text` để ép kiểu này).
Mã thoát ≠ 0 nghĩa là có biến thể bị chặn (`CHẶN … ClaimViolation`) hoặc lỗi ffmpeg. Với ClaimViolation: **sửa chữ/đoạn trong edl, không sửa `forbidden.txt` hay `claims_pending.txt`.** Lệnh ffmpeg lỗi thì dùng agent `ffmpeg-expert`.

## Bước 5. Tự kiểm tra

- Xem từng `<variant>_sheet.png` (Read ảnh): bố cục, chữ có bị che mặt không, chữ đủ dấu không, nguồn ngang có nền blur đúng không.
- Đọc `qa.json`: mọi `duration_ok`, `size_ok`, `loudness_ok` phải True và `notes` rỗng.
- Biến thể nào lỗi thì sửa edl rồi chạy lại riêng nó: `vf render <lô> --only <id>`.

## Bước 6. Báo người dùng

Liệt kê file trong `<drive_root>/out/<lô>/`, mỗi biến thể một dòng: `id — kiểu hook — câu hook — thời lượng — ý tưởng`. Nhắc người dùng điền cột `score` (1–5) và `notes` trong `review.csv`, sau đó gõ "Chạy video-learnings cho các lô đã chấm".
