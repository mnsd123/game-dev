---
name: video-batch-edit
description: Dùng khi người dùng nói "Edit lô <lô>" hoặc muốn dựng hàng loạt video Smilee từ video gốc trong Drive — phân tích nguồn, viết edl.json nhiều biến thể khác kiểu hook/preset, render 9:16, QA, báo kết quả.
---

# Edit video hàng loạt cho Smilee (EDL v2)

Mỗi lô ở `jobs/<lô>/` (brief.yaml, edl.json). Nguồn ở `<drive_root>/source gốc/`, output ở `<drive_root>/out/<lô>/`. Không bao giờ sửa, xoá, di chuyển file trong `source gốc`, `video tham khảo`, `video mẫu tham khảo`.

## Bước 1. Phân tích

```
vf analyze <lô>
vf sheet "work/<nguồn>/normalized.mp4" --every 0.5
```
Chưa có `jobs/<lô>/brief.yaml` → `vf new <lô>`, DỪNG, nhờ người dùng điền brief. Nguồn chỉ có hình (b-roll) vẫn chạy được (transcript rỗng).

## Bước 2. Đọc đủ ngữ cảnh trước khi viết edl

Đọc hết, không lướt:
1. `jobs/<lô>/brief.yaml`
2. `library/style-guide.md` (luật v2) và `library/brand/tokens.json` (thông số, preset)
3. `library/product.md` (nỗi đau, lợi ích, cách dùng, cam kết)
4. `library/hooks.md`, `library/learnings.md`, `library/learnings-stats.md`: ưu tiên kiểu hook/preset đang thắng, tránh điều bị chấm thấp
5. `work/<nguồn>/transcript.json`, `keep.json`, `info.json`, `scenes.json` của MỌI nguồn
6. MỌI trang `*_sheet_NNN.png` của `vf sheet`: chữ in sẵn ở đâu/lúc nào, cảnh tiền, chương, vị trí răng

## Bước 3. Viết `jobs/<lô>/edl.json`

Schema: `vf/edl.py`, mẫu `templates/edl.example.json`. Mọi thời gian `overlays`/`graphics`/`effects` theo **timeline output** (giây, 0 = đầu video).

### Biến thể
- Đúng `brief.variants` biến thể (mặc định 6 = 3 kiểu hook × 2 preset), **khác nhau rõ về kiểu hook hoặc preset** — không chỉ khác chữ. Render ghi `hook trùng với …` khi hai bản cùng lần render dùng chung đoạn hook.
- `hook_type`: `pain` | `question` | `result_first` | `contrarian` | `cost_compare`. Không mở đầu bằng giá.
- `preset` (đúng 1): `pink` | `vox` | `kinetic` | `proof` | `ugc` | `gift` | `routine` | `reply` — chọn theo style guide mục 6 và `learnings-stats.md`.
- `rationale`: 1–2 câu vì sao biến thể có thể thắng (+ lý do nếu để lại ghi chú `~`).
- Bản cắt ngắn (brief có `cutdown_seconds`): thêm `"cutdown_of": "<id>"`, id `<id>-ngan`, giữ hook + bằng chứng mạnh nhất + CTA.

### Đoạn (hook + segments)
- Hook ≤ 3 s, **khung đầu là hình mạnh nhất** (cận răng/kết quả, đèn đang sáng, hộp mở); câu có lực nhất cho kiểu hook đó, lấy từ đâu trong nguồn cũng được.
- Mỗi đoạn ghi `chapter`: `pain`, `benefit`, `result`, `proof`, `speed`, `saving`, `cta` (hook tự là `hook`; đoạn không ghi = chương của đoạn trước). **Đủ ý**: có cả nỗi đau/lợi ích, hiệu quả, bằng chứng trước/sau, nhanh chóng, tiết kiệm, CTA — lint báo chương còn thiếu.
- Tổng thời lượng: `target_seconds ± 10%`; mặc định 45 s – 1 phút 40 tuỳ nguồn — nguồn dài, đủ thông tin thì giữ đủ ý thay vì cắt ngắn.
- Chỉ lấy đoạn trong `keep.json`, cắt ở ranh giới từ. Mép đoạn cách điểm chuyển cảnh (`scenes.json`) ≥ 0,5 s hoặc trùng đúng điểm đó.
- Mỗi cảnh ≥ 1,2 s (nhắm 2–4 s); bỏ chuỗi dựng nhanh của nguồn (thay bằng một cảnh dài + `counter`), hoặc ghi `rapid: true` nếu cố ý.
- Cảnh tiền (trước/sau, bật đèn, mở hộp, cận răng): `protect: true`, ≥ 2,5 s, để cảnh gốc chạy trọn rồi mới thêm đồ hoạ.
- Không lấy đoạn có clip người sáng tạo/người nổi tiếng khác chèn trong nguồn, đoạn mời livestream của KOL.
- `source` là tên file nguồn (kèm đuôi); `a_roll` mang lời nói, `b_roll` chèn minh hoạ. Tôn trọng `must_keep`, `must_cut` của brief.

### Chữ (`overlays`)
- `style` theo preset: `lower` (thẻ 2 tầng: `text` 2–6 từ viết hoa + `sub` ≤ 8 từ) cho pink/kinetic/proof/gift/routine/reply; `vox` cho vox; `plain` cho ugc; dùng chung: `tag` (TRƯỚC/SAU ✓), `cta`, `hook`, `commit`. Lint báo trộn hệ chữ (thẻ CTA được miễn).
- Nhấn màu: `*từ*` = accent, `[từ]` = accent2 (xanh), tối đa 2 cụm. Số luôn nhấn: `*10 PHÚT*` / `[10 PHÚT]` (đèn xanh), `*5 PHÚT*`, `*NGÀY 7*`, `*3–4 TONE*`.
- `animation`: `pop`, `word_by_word` (hook), `highlight` + `emphasis`, `slide`, `none`.
- Chữ đầu tiên ≤ 0,3 s. ≤ 3,5 từ/giây; tối đa 2 khối chữ cùng lúc; render tự kéo dài chữ hiện quá ngắn (`max(1,2; 0,6 + 0,25 × số từ)`).
- Không cắt cảnh trong 0,4 s sau khi chữ hiện. Không đặt chữ `center` trên đoạn `protect` (đè miệng/răng).
- **Nguồn trong `brief.text_sources`**: chỉ đặt chữ trong các khoảng `brief.text_free` (giờ nguồn không có chữ in sẵn); render tự bỏ chữ ngoài các khoảng đó. Không có `text_free` = không thêm chữ cho nguồn đó.
- **Vùng an toàn** (chỉ phần thêm vào): đừng ghi `y` — render tự đặt `y`, `xc` (nửa dưới lệch trái), bề rộng, né mặt và vùng nhiều chi tiết. Ghi `y` chỉ khi buộc phải cố định, trong 0,125–0,6.
- **Cam kết càng nổi bật càng tốt**: 3 cam kết ("trắng sau 5–7 ngày", "bật 3–4 tone", "trắng như sứ") tự highlight khi người nói nói ra (`library/commitments.txt`); ưu tiên giữ các đoạn đó, được đưa lên hook. Không có kiểm tra claim, không disclaimer (người dùng chốt 2026-10-14) — trừ cụm brief của lô ghi trong `forbidden`.
- Không phụ đề toàn bộ lời (`captions: false`), trừ khi brief yêu cầu.
- CTA: một CTA mềm trong 60–85 % thời lượng + `end_card` (hoặc thẻ `cta`) trong 3 s cuối.

### Đồ hoạ (`graphics`) và hiệu ứng (`effects`)
Chỉ thêm ở đoạn nguồn "trơn"; đoạn nguồn đã tự minh hoạ cùng ý (đèn sáng, bảng màu, khoanh sẵn, chữ "ÁNH SÁNG XANH") thì để nguyên. Mọi graphic tự nằm trong vùng an toàn.

| Ý | Cú pháp |
|---|---|
| Đèn xanh/đỏ | `{"kind": "light_timer", "start", "end", "rows": [{"min": 10, "title": "ÁNH SÁNG XANH", "sub": "kích hoạt gel", "color": "blue", "at": 0}, {"min": 5, "title": "ÁNH SÁNG ĐỎ", "sub": "làm dịu nướu", "color": "red", "at": 3.2}]}` (`at` = giây từ đầu thẻ, đúng lúc chuyển đèn); thêm `{"kind": "light", "color": "blue"}` nếu muốn vầng sáng |
| Răng vàng → trắng | `{"kind": "teeth", "start", "end", "split": 0.56}` (hàm răng vector, đèn quét) hoặc `{"kind": "whiten", ...}` (icon, ghi "Hình minh họa") — 1,5–2 s ngay sau cảnh dùng máy |
| Chỉ vào răng vàng | `effects` `{"kind": "zoom_to", "at", "duration", "zoom": 1.6, "track": "teeth"}` + `graphics` `{"kind": "callout", "label": "răng *ố vàng*", "cx": 0.5, "cy": 0.5, "rx": 0.3, "ry": 0.085}` cùng lúc |
| Trước/sau | sau cảnh gốc: `{"kind": "wipe", "stills": [{"source", "t", "crop": [x0,y0,x1,y1], "label": "Trước"}, {..., "label": "Sau 7 ngày"}]}` hoặc `collage` (giấy, preset vox) |
| Thang màu | `{"kind": "shade", "from_shade": 10, "to_shade": 5, "label": "theo trải nghiệm của Giao"}` — chỉ số mức người nói nói ra |
| Đếm ngày | `{"kind": "counter", "label": "dùng đều mỗi ngày"}` 1–1,5 s giữa cảnh trước và sau |
| Kinetic hook (preset kinetic) | `{"kind": "kinetic", "start": 0, "end": 1.4, "words": ["RĂNG", "*VÀNG*", "HƠN NGÔ"]}` |
| CTA cuối | `{"kind": "end_card", "label": "BẤM GIỎ HÀNG", "sub": "xem kit Smilee", "live": true}` 2,5–3 s cuối |
| Nhấn nhịp | `effects` `zoom_punch` ở chỗ nhấn; mỗi ≤ 4 s phải có một thay đổi (cắt/zoom/đồ hoạ/chữ). Không `flash`, hạn chế `shake` |

Chuyển cảnh ở ranh giới chương do preset quyết định, render tự làm (whip/paper/cut) — không khai tay.

### Âm thanh
Render tự gắn SFX theo sự kiện (`tokens.auto_sfx`, file `library/brand/sfx/`, `vf make-sfx` tạo bản tạm). Khai tay `{"kind": "sfx", "at", "asset": "sfx/ding.wav"}` khi cần âm khác; `"sfx_auto": false` để tắt. `music`: nhạc có giấy phép trong `library/brand/` (tự hạ khi có giọng); nhạc trend thì để trống và ghi "gắn nhạc CML trên TikTok" trong `rationale`. Giữ tiếng ASMR thật.

### Ma trận GMV Max (tuỳ chọn)
Khối `"matrix": {"presets": ["ugc", "pink"], "hooks": [{"id", "hook_type", "hook": {...}, "overlays": [...]}], "bodies": [{"id", "segments": [...], "overlays", "graphics", "effects"}], "ctas": [...]}` — thời gian trong mỗi phần tính từ đầu phần đó. `vf expand <lô>` thêm biến thể `<lô>_<hook>_<body>_<cta>_<preset>` (không ghi đè id có sẵn).

### Không bao giờ
Tự bịa before/after, review, số liệu; chỉnh màu răng thật; dùng hình, nhạc, giọng, câu chữ nguyên văn của video tham khảo; nêu tên phòng khám/đối thủ.

## Bước 4. Render

```
vf render <lô>              # --only <id> để render lại riêng
```
Chữ/đồ hoạ render bằng Remotion (nền trong suốt) rồi ffmpeg chồng lên video. Chưa cài Remotion thì chữ tĩnh bằng ffmpeg. Lệnh ffmpeg lỗi → agent `ffmpeg-expert`.

## Bước 5. Tự kiểm tra

- Mở từng `<id>_sheet.png`: chữ không đè chữ nguồn, không bị cắt, trong viền đỏ (vùng an toàn), khoanh đúng răng, một hệ chữ, nguồn ngang có nền blur đúng.
- `qa.json`: `duration_ok`, `size_ok`, `loudness_ok` True, `notes` rỗng. `vùng an toàn: …` → sửa edl, render lại; không báo xong khi còn ghi chú này.
- `creative` (dòng `~`): hook, CTA, đủ ý, protect, nhịp cắt, trộn hệ chữ, âm thanh, hook trùng, `tự sửa: …` — sửa nếu được, không thì ghi lý do vào `rationale`.

## Bước 6. Báo người dùng

Liệt kê file trong `<drive_root>/out/<lô>/`, mỗi biến thể một dòng: `id — preset — kiểu hook — câu hook — thời lượng — ý tưởng`. Nhắc điền `score` (1–5) + `notes` riêng từng biến thể trong `review.csv`, số liệu TikTok sau khi đăng, rồi gõ "Chạy video-learnings".
