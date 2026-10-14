# Lịch sử skill smilee-video

## v1.4 — 2026-10-14 (nghiên cứu xu hướng quảng cáo TikTok 2026 + yêu cầu vùng an toàn)

| Vấn đề / gợi ý | Thay đổi |
|---|---|
| Chữ/hình **thêm vào** có thể bị giao diện TikTok che (vùng an toàn chỉ áp cho phần Claude thêm; nội dung source gốc giữ nguyên) (placement cũ chỉ chừa 6 % trên, 20 % đáy, không tính cột nút phải) | `vf/safezone.py` (trên 240 px, dưới 660 px, hai bên 120 px, cột nút 180 px từ y 840): placement chỉ đặt trong vùng an toàn, hộp chữ thu hẹp ở hàng cột nút (`max_w`), `y` ghi tay và `callout` bị kéo vào; Remotion nhận `safe` (thẻ đếm ngày, ảnh ghép, nhãn khoanh, chữ Vox xuống dòng); chữ tĩnh và phụ đề ASS cũng theo vùng an toàn. QA đọc kênh alpha lớp chữ → `vùng an toàn: …` + CẦN XEM; `*_sheet.png` kẻ viền đỏ vùng an toàn. |
| lo-02 không có nhạc lẫn SFX dù pipeline hỗ trợ | SFX tự động theo hiệu ứng từ `library/brand/sfx/` (`vf/creative.py`), −8 dB; `vf doctor` cảnh báo khi thiếu SFX; style guide mục 7. |
| Trộn nhiều ngôn ngữ đồ hoạ trong một bản; biến thể khó thành phương án test khác nhau | `preset` mỗi biến thể (ugc, result_rewind, vox, routine, reply, beat — style guide mục 11); QA nhắc hook trùng trong cùng lần render. |
| CTA chỉ ở ~94 % thời lượng; người xem rời mạnh sau ~25 s | CTA mềm ở 60–85 % + CTA cuối; bản cắt ngắn `cutdown_seconds` / `cutdown_of`. |
| Typography: chỉ một font, không quy tắc đọc | Style guide mục 12: tối đa 2–3 kiểu chữ, phân màu theo vai trò, chỉ từ khoá chuyển động, hook có chữ trước 0.5 s, ≤ 3.5 từ/giây — QA nhắc (`creative`). |
| Motion graphic mới theo xu hướng beauty | `shade` (thang màu răng, chỉ dùng số người nói nói ra) và `wipe` (thanh gạt trước/sau từ cảnh thật). Các hiệu ứng chưa làm ghi ở style guide mục 14. |
| Vòng học chỉ có điểm cảm tính | Nhắc điền `views`, `retention_3s`; video-learnings có mốc retention 3 s và học theo preset. |

## v1.3.1 — 2026-10-14 (lo-02 v7–v9: 3đ)

- Vox giữ nguyên. Người dùng nhắc: **không bỏ** motion graphic răng vàng → trắng khi đèn xanh/đỏ, vầng sáng, thẻ đếm ngày — dùng tiếp khi hợp bối cảnh (style guide mục 10, video-batch-edit).

## v1.3 — 2026-10-14 (feedback lo-02 v4–v6: 2.5đ)

| Feedback | Thay đổi |
|---|---|
| Đoạn nguồn đã có hình/video minh hoạ thì không cần thêm | Bỏ hàm răng vector, vầng sáng, thẻ đếm ngày trên cảnh đèn/bảng màu; chỉ thêm đồ hoạ ở đoạn trơn. |
| Đoạn có chữ in sẵn thì không thêm chữ | Giữ `text_free`; bỏ thẻ đè lên đoạn có sticker. |
| Chuyển cảnh nhanh; để trọn cảnh trước/sau gốc rồi mới thêm graphic | Cảnh BEFORE → AFTER gốc chạy trọn (54.48–59.15); ảnh ghép TRƯỚC/SAU đặt ngay sau. Cách dùng chỉ lấy phần đèn (bỏ chuỗi 0.8 s). |
| Phong cách Vox | `zoom_to` (ống kính bám răng, `vf/track.py`), `callout` (khoanh tay → mũi tên → bút dạ), `collage` (giấy, băng keo, ảnh cắt từ nguồn), chữ `vox`. Style guide mục 10. |
| Răng vàng: zoom vào răng hoặc chỉ vào rồi mới ghi chú | Zoom 1.6 bám răng + khoanh + mũi tên + nhãn "RĂNG Ố VÀNG", đúng thứ tự. |

## v1.2 — 2026-10-14 (feedback lo-02: v1 3đ, v2 3đ, v3 2đ)

| Feedback | Thay đổi |
|---|---|
| Chuyển cảnh nhanh làm xém chữ/hình | Nguyên nhân: chuỗi dựng nhanh 0.6 s có sẵn trong nguồn (nhật ký 7 ngày). Quy tắc cảnh ≥ 1.2 s; bỏ chuỗi đó, thay bằng cảnh before/after dài + thẻ đếm ngày. |
| Cần motion graphic đèn xanh/đỏ làm răng vàng → trắng | `graphics.kind = "teeth"`: hàm răng vector, thanh LED xanh quét → răng trắng dần, pha đỏ dịu nướu, ghi "Minh họa". |
| Không mở đầu bằng chi phí; tập trung nỗi đau răng vàng, làm trắng nhanh, biến đổi vàng → trắng, gel tiết kiệm | lo-02 v4–v6 viết lại theo hướng này; "gel tiết kiệm" đặt gần cuối. ("cấp tốc" là cụm cấm → không đưa lên chữ.) |
| Tham khảo phong cách 2 video mẫu | `library/style-guide.md` (ĐÃ DUYỆT): thẻ `lower` hai dòng tím mận/hồng, nhãn `tag`, thẻ `counter` toàn màn hình, bảng màu. |
| Nguồn có chữ in sẵn: chỉ thêm chữ ở cảnh không có chữ | Brief `text_free` (khoảng giờ nguồn không có chữ); `strip_text` chỉ giữ chữ nằm trong các khoảng đó. |

## v1.1 — 2026-10-14 (lô lo-02)

- Yêu cầu người dùng: nguồn đã có chữ in sẵn trên hình thì không thêm chữ minh hoạ. Brief có trường `text_sources`; `vf/motion.py: strip_text` bỏ mọi chữ chồng lên đoạn của các nguồn đó (cả cam kết tự động), hiệu ứng hình giữ nhưng bỏ nhãn.

## v1 — 2026-10-14 (sau lô pilot lo-01)

Feedback người dùng sau lo-01 và cách xử lý:

| Feedback | Thay đổi |
|---|---|
| Video bị vấp, díu hình; vài khung hình cắt lỗi, chuyển cảnh không dứt khoát | `vf analyze` ghi `scenes.json` (điểm chuyển cảnh, `vf/scenes.py`). Render bỏ mẩu cảnh < 0.5 s ở mép đoạn, giữ khung hình kề bên (tiếng không đổi); cắt nhảy trong cùng cảnh thì phóng to xen kẽ ×1.12. Bỏ hiệu ứng `flash`. Skill yêu cầu cắt theo `scenes.json`. |
| Font lỗi tiếng Việt; chữ cần viền, nền dễ nhìn, không che vật thể/mặt | Font Montserrat ExtraBold trong `library/brand/`. Chữ hook có viền + nền tối mờ, thẻ nhãn/CTA hồng Smilee. `vf/placement.py` dùng OpenCV (nhận diện mặt + mật độ chi tiết) tự chọn vị trí dọc cho từng chữ. |
| Chưa có hiệu ứng minh hoạ đèn xanh/đỏ và before/after răng | `graphics` trong edl: `light` (viền sáng + đồng hồ đếm phút) và `whiten` (icon răng vàng → trắng, ghi "Hình minh họa" vì hồ sơ sản phẩm cấm tự bịa before/after). Remotion: `remotion/src/Graphics.tsx`. |

Sửa lỗi cài đặt trên Windows:
- Repo ở đường dẫn dài → `pip` lỗi `WinError 206`: clone vào đường dẫn ngắn (`C:\dev\game-dev`).
- faster-whisper GPU thiếu `cublas64_12.dll`: thêm `nvidia-cublas-cu12`, `nvidia-cudnn-cu12` vào phụ thuộc, `vf/transcribe.py` tự nạp DLL.
- OpenCV giữ bản 4.x (bản 5 bỏ file Haar cascade).

## v0 — 2026-10-13

Quy trình đầu tiên: doctor → status → brief → analyze → edl → render → QA → review.csv.
