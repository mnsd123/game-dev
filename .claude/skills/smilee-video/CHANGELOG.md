# Lịch sử skill smilee-video

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
