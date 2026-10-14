---
name: smilee-video
description: Use when có source gốc mới trong thư mục Drive EDIT/"source gốc" của Smilee, hoặc người dùng nói "có source mới", "dựng video mới", "edit lô mới", "edit lô ...", "làm video từ source mới", đưa video gốc Smilee cần dựng, hoặc gõ /smilee-video.
---

# /smilee-video — v2 (2026-10-14)

Bạn là editor quảng cáo TikTok cho kit trắng răng Smilee. Kết quả: N file MP4 9:16 trong `EDIT/out/<lô>/` (Remotion + ffmpeg), kèm `*_sheet.png` (viền vùng an toàn), `qa.json`, `review.csv`.

> **v2** gộp bản đóng gói từ Claude chat (`smilee-video-SKILL.md`) với v1.4 của repo, theo quyết định của người dùng 2026-10-14: không chặn claim, không disclaimer, chữ chỉ ở khoảng không có chữ in sẵn, cảnh ≥ 1,2 s và không flash, 45 s – 1 phút 40 đủ ý, 8 preset. Lịch sử: `CHANGELOG.md`.

Chạy mọi lệnh ở gốc repo (thư mục có `vf.toml`; `vf` = `.venv\Scripts\vf.exe` nếu chưa activate venv). Không bao giờ sửa, xoá, di chuyển file trong `source gốc`, `video tham khảo`, `video mẫu tham khảo`.

## Đọc trước khi làm (bắt buộc, mỗi lô)

1. `library/style-guide.md` — luật dựng, preset, typography, vùng an toàn. **Ưu tiên cao nhất.**
2. `library/brand/tokens.json` — màu, cỡ chữ, thời gian, vùng an toàn, preset, auto SFX (máy đọc).
3. `library/product.md` — hồ sơ sản phẩm, nỗi đau, lợi ích, cách dùng (giữ nguyên các mục `[CẦN XÁC NHẬN]`).
4. `library/hooks.md`, `library/learnings.md`, `library/learnings-stats.md` (nếu có) — điều đã học.
5. `jobs/<lô>/brief.yaml`.

## Quy trình

### 0. Môi trường — `vf doctor`
Dòng `LỖI` → sửa theo gợi ý rồi chạy lại; `CẢNH BÁO` → báo một dòng, chạy tiếp. Thiếu SFX → chạy `vf make-sfx` (SFX tạm). Chưa có `.venv`/`vf.toml` trên Windows → `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1`. Phiên cloud không đọc được Drive → báo người dùng mở phiên Local.

### 1. Có gì mới — `vf status`
Không có nguồn `MỚI` → hỏi dựng lại nguồn cũ hay chờ. Có lô đã chấm mà chưa học → chạy skill `video-learnings` TRƯỚC.

### 2. Lô và brief — `vf new auto`
Yêu cầu gõ kèm lệnh là ràng buộc cứng, ghi vào brief trước khi hỏi ("dưới X giây" → `target_seconds` = X ÷ 1,1 làm tròn xuống). Hỏi người dùng MỘT lần, gộp một tin nhắn, mỗi mục có mặc định để trả lời "ok":
- thời lượng (mặc định theo source, 45 s – 1 phút 40, đủ ý), số biến thể (mặc định 6 = 3 kiểu hook × 2 preset), bản cắt ngắn `cutdown_seconds` (mặc định không)
- preset từng biến thể (style guide mục 6), thông điệp một câu, CTA
- vai trò từng nguồn (a_roll / b_roll), ý hook nếu có

"Tự quyết" → tự điền từ `product.md`, `hooks.md`, `learnings-stats.md`.

### 3. Phân tích nguồn
```
vf analyze lo-NN
vf sheet "work/<nguồn>/normalized.mp4" --every 0.5
```
`analyze` chuẩn hoá, phiên âm từng từ, dò điểm chuyển cảnh (`scenes.json`). `sheet` tạo ảnh tổng quan có mốc giờ nguồn + viền vùng an toàn. Đọc hết các trang sheet và ghi:
- **Chữ in sẵn**: nguồn vào `text_sources`; khoảng giờ KHÔNG có chữ in sẵn vào `text_free` — chỉ thêm chữ ở đó.
- **Cảnh tiền** (cận răng, trước/sau, bật đèn, mở hộp) → `protect: true` khi dùng.
- **Chương** của từng đoạn định dùng (nỗi đau, lợi ích, hiệu quả, bằng chứng, nhanh, tiết kiệm, CTA).
- Toạ độ răng cho `callout` (hoặc dùng `zoom_to` + `track: "teeth"` để ống kính bám răng rồi khoanh giữa khung).
- Nguồn là clip KOL đã dựng sẵn, nội dung có thể khác brief → bám nội dung thật, báo người dùng. Không dùng đoạn có clip người sáng tạo khác chèn vào.

Nội dung có sẵn trong source (chữ, sticker, phụ đề KOL) giữ nguyên; vùng an toàn chỉ áp cho phần Claude thêm vào.

### 4. Viết `jobs/lo-NN/edl.json`
**REQUIRED SUB-SKILL:** skill `video-batch-edit` (bước 2–3) — schema, luật từng trường, ví dụ.
Tóm tắt: mỗi biến thể đúng 1 `preset`, khác nhau rõ về kiểu hook hoặc preset; mọi đoạn có `chapter`, đủ ý; hook ≤ 3 s, khung đầu là hình mạnh nhất, chữ đầu tiên ≤ 0,3 s; cảnh ≥ 1,2 s; CTA giữa video + `end_card` cuối; cam kết càng nổi bật càng tốt; `rationale` 1–2 câu. Bản số lượng GMV Max: khối `matrix` rồi `vf expand lo-NN`.

### 5. Render và tự kiểm tra
```
vf render lo-NN            # hoặc --only <id> để render lại riêng
```
- Render tự: kéo dài chữ cho đủ đọc, đặt chữ/đồ hoạ trong vùng an toàn và né mặt, chuyển cảnh theo preset ở ranh giới chương, SFX theo sự kiện, nhạc tự hạ khi có giọng.
- `qa.json`: `duration_ok`, `size_ok`, `loudness_ok` True và `notes` rỗng. Dòng `vùng an toàn: …` là lỗi phải sửa.
- Dòng `~ …` (`creative` trong qa.json): hook, CTA, đủ ý, protect, nhịp cắt, trộn hệ chữ, âm thanh, hook trùng, `tự sửa: …` — sửa nếu được, không thì ghi lý do vào `rationale`.
- **Mở từng `*_sheet.png`**: chữ không đè chữ nguồn, không bị cắt, trong viền đỏ, khoanh đúng răng, một hệ chữ.
- Render một biến thể ~4 phút (Remotion) — lô nhiều biến thể thì cho chạy nền.

### 6. Báo người dùng
Đường dẫn `EDIT/out/lo-NN/`; mỗi biến thể một dòng `id — preset — kiểu hook — câu hook — thời lượng — ý tưởng`; ghi chú sáng tạo còn để lại. Nhắc chấm `score` + `notes` **riêng từng biến thể** trong `review.csv`, và sau khi đăng điền số liệu TikTok (`views`, `retention_3s`, `view_2s`, `view_6s`, `avg_watch_s`, `ctr`, `cvr`, `cost_per_order`).

## Học từ kết quả
Người dùng nói "chạy video-learnings" hoặc đã điền `review.csv` → skill `video-learnings` (`vf learn --write` → `library/learnings-stats.md` theo preset × kiểu hook × độ dài; cập nhật `learnings.md`, `hooks.md`). Dùng kết quả để chọn preset/hook cho lô sau — preset nào thắng thì dùng nhiều hơn, thua thì sửa hoặc bỏ.

## Không bao giờ
- Chỉnh màu/làm trắng răng thật trong footage; tạo before/after, review, số liệu không có trong tư liệu.
- Dùng lại hình, nhạc, giọng, câu chữ nguyên văn của video tham khảo.
- Trộn nhiều preset trong một biến thể; meme/sticker trong preset pink/vox/proof.
- Flash trắng; chữ đè chữ có sẵn trong nguồn.

## Lỗi thường gặp

| Triệu chứng | Cách xử lý |
|---|---|
| `vf status` không thấy file vừa bỏ vào Drive | Drive chưa đồng bộ / chưa bật *Available offline*; kiểm tra `drive_root` trong `vf.toml` |
| Tiếng và hình lệch | Xoá `work/<nguồn>/normalized.mp4` rồi chạy lại `vf analyze` |
| Chữ không động | Chưa `npm install` trong `remotion/`; hoặc `--static-text` để chủ ý dùng chữ tĩnh |
| `cublas64_12.dll is not found` | `.venv\Scripts\python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"` |
| `pip install` lỗi `WinError 206` | Repo ở đường dẫn quá dài → clone vào thư mục ngắn như `C:\dev\game-dev` |
| Video "vấp", vài khung cảnh khác lóe lên | Mép đoạn sát điểm chuyển cảnh; render tự xử lý, chỉnh edl theo `scenes.json` cho gọn |
| Chữ lỗi dấu tiếng Việt | Thiếu font: `library/brand/fonts/BeVietnamPro-*.ttf` hoặc `library/brand/Montserrat-ExtraBold.ttf` |
| `vùng an toàn: chữ/hình lấn vùng …` | Rút chữ, bỏ `y` ghi tay, dời graphic. Số liệu: `tokens.json` → `vf/safezone.py` |
| Không có tiếng SFX | `vf make-sfx`; preset `ugc` hoặc `"sfx_auto": false` thì cố ý không có |
| `ClaimViolation` | Chỉ còn chặn cụm do chính brief của lô ghi trong `forbidden` — sửa chữ hoặc bỏ cụm khỏi brief |
| Phiên âm rỗng | Lần trước chạy `--no-transcribe`; chạy lại `vf analyze lo-NN` |
