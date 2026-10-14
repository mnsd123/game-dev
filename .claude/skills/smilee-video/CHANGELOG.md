# Lịch sử skill smilee-video

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
