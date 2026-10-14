---
name: smilee-video
description: Use when có source gốc mới trong thư mục Drive EDIT/"source gốc" của Smilee, hoặc người dùng nói "có source mới", "dựng video mới", "edit lô mới", "làm video từ source mới", hoặc gõ /smilee-video.
---

# Dựng video Smilee từ source gốc mới (trọn quy trình) — v1

> **v1.2 (2026-10-14)** — dựng theo `library/style-guide.md` (ĐÃ DUYỆT, học từ `EDIT/video mẫu tham khảo/`): thẻ chữ hai dòng tím mận, nhãn TRƯỚC/SAU, thẻ đếm ngày, hàm răng vector minh hoạ đèn; cảnh ≥ 1.2 s.
> **v1 (2026-10-14)** — sau lô pilot lo-01. Mới so với bản đầu: tránh "vấp hình" ở điểm chuyển cảnh, chữ font Montserrat có nền + tự né mặt, hiệu ứng minh hoạ đèn xanh/đỏ và răng vàng → trắng, phiên âm GPU trên Windows. Lịch sử: `CHANGELOG.md` cùng thư mục.

Điểm vào duy nhất mỗi khi có video quay mới. Kết quả: N file MP4 9:16 trong `EDIT/out/<lô>/` (chữ động bằng Remotion + ffmpeg, không phụ đề toàn bộ lời, chỉ highlight hook, cam kết, lợi ích, CTA), kèm ảnh tổng quan, `qa.json`, `review.csv`.

Chạy mọi lệnh ở gốc repo (thư mục có `vf.toml`). Không bao giờ sửa, xoá, di chuyển file trong `source gốc` và `video tham khảo`.

## 0. Kiểm tra môi trường (chỉ dừng khi có LỖI)

```
vf doctor
```
- Lệnh `vf` nằm trong `.venv`: Windows gọi `.venv\Scripts\vf.exe`, Mac/Linux gọi `.venv/bin/vf`, nếu chưa activate venv.
- Chưa có `.venv` hoặc `vf.toml` trên Windows → chạy `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1` (tự cài ffmpeg, Python, Node, thư viện, Remotion, tự tìm thư mục EDIT), rồi chạy lại `vf doctor`.
- Dòng `LỖI` → sửa theo gợi ý trên dòng đó rồi chạy lại. Dòng `CẢNH BÁO` → báo người dùng một dòng và chạy tiếp.
- Repo phải ở **đường dẫn ngắn** (ví dụ `C:\dev\game-dev`). Đường dẫn dài (thư mục tạm của app, OneDrive lồng sâu) làm `pip install` lỗi `WinError 206` vì Windows giới hạn 260 ký tự.
- Vừa cài Node bằng setup mà `vf doctor` vẫn báo "chưa cài Remotion" → chỉ là PATH của phiên cũ; mở terminal mới (hoặc nạp lại PATH) rồi chạy lại.
- Đang ở phiên **cloud** và `drive_root` không tồn tại → dừng, báo người dùng mở phiên **Local** trên máy có Google Drive for Desktop (phiên cloud không đọc được Drive).

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
Lệnh cũng ghi `work/<nguồn>/scenes.json` (điểm chuyển cảnh). Nguồn thường là clip KOL **đã dựng sẵn** (nhiều cảnh ngắn, sticker) — xem ảnh ghép khung hình trước khi viết edl để biết nội dung thật, có thể khác brief (ví dụ lo-01 là clip quà 20/10): khi đó bám nội dung thật, giữ lợi ích sản phẩm bằng chữ, và báo người dùng.
**Nguồn đã có chữ in sẵn trên hình** (phụ đề nhấn, tiêu đề, sticker chữ) → thêm tên file vào `text_sources` trong brief. Sau đó xem khung hình từng giây của các đoạn định dùng và ghi khoảng không có chữ in sẵn vào `text_free`: chỉ ở đó mới thêm thẻ chữ theo style guide (người dùng chọn 2026-10-14). Ngoài các khoảng đó render tự bỏ chữ (kể cả cam kết tự động); hiệu ứng hình giữ nhưng bỏ nhãn. Nguồn đã có cảnh before/after thật (bảng so màu) thì dùng cảnh thật, không thêm icon răng minh hoạ. (Yêu cầu người dùng 2026-10-14.)

## 4. Viết kịch bản dựng

**REQUIRED SUB-SKILL:** Làm theo skill `video-batch-edit`, bước 2–3, để viết `jobs/lo-NN/edl.json`: đọc đủ ngữ cảnh, mỗi biến thể một kiểu hook, chữ động chỉ ở đoạn quan trọng, cắt theo điểm chuyển cảnh, có hiệu ứng minh hoạ ở đoạn nói về đèn/kết quả. 3 cam kết kết quả được tự phát hiện trong lời nói và tự highlight.

## 5. Render và tự kiểm tra

```
vf render lo-NN
```
- Có giới hạn thời lượng từ người dùng thì mọi biến thể phải ngắn hơn giới hạn đó; vượt thì cắt bớt đoạn trong edl và render lại.
- Xem từng `*_sheet.png` và `qa.json`. Biến thể lỗi thì sửa edl rồi chạy `vf render lo-NN --only <id>`.
- Dòng `· đoạn N: mẩu cảnh …` khi render: pipeline đã tự giữ khung hình kề bên cho mẩu cảnh < 0.5 s; nhiều dòng như vậy thì dời mép đoạn trong edl về đúng điểm chuyển cảnh cho gọn.
- Render một biến thể mất ~4 phút (Remotion); lệnh chạy lâu thì cho chạy nền.
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
| `cublas64_12.dll is not found` khi phân tích | Thiếu thư viện CUDA: `.venv\Scripts\python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"` (đã có trong `pyproject.toml`; `vf/transcribe.py` tự nạp DLL) |
| `pip install` lỗi `WinError 206` | Đường dẫn repo quá dài → clone lại vào thư mục ngắn như `C:\dev\game-dev` |
| Video "vấp", vài khung hình cảnh khác lóe lên | Mép đoạn rơi sát điểm chuyển cảnh; đã tự xử lý khi render, chỉnh edl theo `scenes.json` để gọn hơn |
| Chữ lỗi dấu tiếng Việt | Thiếu font trong `library/brand/` (mặc định `Montserrat-ExtraBold.ttf`, giấy phép OFL) |
| Phiên âm rỗng | Lần trước chạy `--no-transcribe`; chạy lại `vf analyze lo-NN` (tự phiên âm lại) |
| Video mẫu ở `EDIT/video mẫu tham khảo/` (không phải `video tham khảo`) | Thư mục mẫu người dùng đặt; chỉ học kỹ thuật, không lấy hình/nhạc/giọng |
| Chưa có `library/style-guide.md` đã duyệt | Vẫn dựng được, báo người dùng; muốn học phong cách thì chạy skill `video-style-learning` |
