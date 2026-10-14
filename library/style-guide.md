# Style guide Smilee — v2

Trạng thái: ĐÃ DUYỆT 2026-10-14 — v2 gộp từ bản đóng gói `smilee-video-SKILL.md` (Claude chat) và v1.4 trong repo, theo các quyết định của người dùng ngày 2026-10-14.
Nguồn: đánh giá lô 01–02 (điểm 2–3/5), video mẫu trong `EDIT/video mẫu tham khảo/` (chỉ học kỹ thuật), nghiên cứu xu hướng quảng cáo TikTok 2026.
Thông số máy đọc: `library/brand/tokens.json` (một nguồn duy nhất). File này là luật để viết `edl.json`.

## 1. Nguyên tắc gốc

1. **Một hệ chữ cho cả video.** Mỗi biến thể đúng 1 `preset` (mục 6). Không trộn hộp tím, chữ Vox bút dạ và sticker trong cùng một video.
2. **Đủ ý trước, đẹp sau.** Video phải có đủ: nỗi đau/lợi ích, hiệu quả, bằng chứng trước/sau, nhanh chóng, tiết kiệm, CTA (mục 2). Thiếu ý thì kéo dài video, không cắt cho ngắn.
3. **Thật hơn bóng bẩy.** Giữ cảnh thật, giọng thật. Đồ hoạ để giải thích, không để làm đẹp kết quả.
4. **Không bao giờ chỉnh màu răng thật** trong footage. Hiệu ứng "vàng → trắng" chỉ dùng hình minh hoạ (`whiten`, `teeth`). Không bịa before/after, review, số liệu không có trong tư liệu.
5. **Cam kết và lợi ích càng nổi bật càng tốt.** Không chặn claim, không thêm disclaimer/nhãn quảng cáo (người dùng chốt 2026-10-14). 3 cam kết (trắng sau 5–7 ngày, bật 3–4 tone, trắng như sứ) tự highlight khi người nói nói ra.
6. **Nội dung có sẵn trong source gốc giữ nguyên** (chữ in sẵn, sticker, phụ đề KOL): không dời, không cắt, không né đoạn vì nó.

## 2. Cấu trúc và độ dài

- Độ dài ưu tiên **45 s – 1 phút 40** tuỳ source; source dài, đủ thông tin thì được ±10 %. Brief/lệnh của người dùng ghi đè.
- Bản cắt ngắn (tuỳ chọn): brief `cutdown_seconds` + `"cutdown_of"` trong edl.
- Chương (`chapter` trên mỗi đoạn): `hook → pain → benefit → result → proof → speed → saving → cta` (thứ tự linh hoạt; `problem` = pain, `solution` = benefit). Lint nhắc chương còn thiếu.
- **Khung hình đầu là hình mạnh nhất** (cận răng, đèn đang sáng, hộp quà mở). Chữ/đồ hoạ đầu tiên ≤ 0,3 s (trừ khi nguồn đã có chữ in sẵn ở hook). Hook ≤ 3 s. Không mở đầu bằng giá (lo-02 v3: 2đ).
- CTA hai lần: CTA mềm ở 60–85 % thời lượng + CTA/`end_card` trong 3 s cuối.

## 3. Ngữ pháp cắt dựng

| Luật | Giá trị |
|---|---|
| Cảnh ngắn nhất | **1,2 s**, nhắm 2–4 s (feedback lo-02). Chuỗi cắt nhanh có chủ đích: `rapid: true` |
| Giữ chữ tối thiểu | `max(1,2 s; 0,6 + 0,25 × số từ)` — render tự kéo dài |
| Không cắt cảnh trong | 0,4 s sau khi chữ vừa hiện |
| Cảnh "tiền" (trước/sau, bật đèn, mở hộp) | `protect: true`, ≥ 2,5 s, để cảnh gốc chạy trọn; không đặt chữ giữa khung đè miệng/răng |
| Đổi nhịp | mỗi ≤ 4 s một lần: cắt, zoom, đồ hoạ, chữ |
| Chuyển cảnh | chỉ ở ranh giới chương, theo preset: `whip` (zoom 1.12 → 1 + mờ 0,1 s), `paper` (tờ giấy lướt ngang), `cut`. **Không flash trắng** (lo-01: "trông như lỗi hình"). Trong chương: cắt thẳng |
| Chữ có sẵn trong nguồn | nguồn vào `text_sources`; chỉ thêm chữ trong các khoảng `text_free` (giờ nguồn không có chữ in sẵn). Nguồn đã giải thích đủ thì **không thêm** |
| Đoạn nguồn đã tự minh hoạ (đèn sáng, bảng màu, khoanh sẵn) | để nguyên, không chồng đồ hoạ cùng ý |
| Zoom vào chi tiết | zoom (`zoom_to`, bám răng) → khoanh → mũi tên → nhãn, đúng thứ tự |
| Không dùng | đoạn có clip của người sáng tạo/người nổi tiếng khác chèn trong nguồn |

## 4. Typography

- Font chính theo `tokens.fonts.main`: **Be Vietnam Pro** (Black/ExtraBold, thiết kế cho tiếng Việt) khi có file trong `library/brand/fonts/`, chưa có thì Montserrat ExtraBold. Chừa ~22 % cỡ chữ phía trên dòng cho dấu chồng (Ề, Ẫ, Ỗ).
- Thang cỡ chữ (px, 1080×1920): hook 92 · claim 84 · cta 76 · label 64 · dòng phụ 38–44 · note 32 · kinetic 150.
- Nhãn tối đa 2 tầng: dòng chính ≤ 6 từ, dòng phụ ≤ 8 từ, tối đa 3 dòng. ≤ 3,5 từ/giây, tối đa 2 khối chữ cùng lúc.
- Nhấn màu trong chữ: `*từ*` = accent (hồng/đỏ marker theo preset), `[từ]` = accent2 (xanh). Tối đa 2 cụm nhấn mỗi nhãn. Không có dấu nhấn → cả dòng chính màu accent (thẻ `lower`).
- Số luôn được nhấn: **10 PHÚT** (xanh – đèn xanh), **5 PHÚT** (đỏ – đèn đỏ), **NGÀY 7**, **3–4 TONE**.
- Chỉ từ khoá chuyển động (`highlight` + `emphasis`, `pop`); đặt đúng lúc người nói nói ra từ đó.

## 5. Vùng an toàn (chỉ cho phần thêm vào)

Khung 1080×1920 (`tokens.safe_zone`, `vf/safezone.py`): chừa **trên 240 px, dưới 660 px, trái/phải 120 px, và phải 300 px khi y > 840** (cột nút avatar/tim/bình luận/chia sẻ).

- Pipeline tự đặt `y` và tâm ngang `xc`: nửa trên căn giữa, nửa dưới lệch trái trong x 120–780; hộp chữ tự hẹp lại. `y` ghi tay ngoài vùng an toàn và vòng khoanh bị kéo vào trong (QA ghi chú).
- Remotion nhận `safe`: thẻ đếm ngày, ảnh ghép, thanh gạt, kinetic hook, nhãn khoanh đều bố cục trong vùng an toàn.
- QA đọc kênh alpha lớp thêm vào: chỗ đặc (≥ 85 %) lấn vùng cấm → `vùng an toàn: …`, biến thể **CẦN XEM**. `*_sheet.png` kẻ viền đỏ vùng an toàn. Được tràn mép: vầng sáng, bóng đổ, hạt sáng mờ, nền phủ kín của thẻ toàn màn hình.

## 6. Preset (8)

Mỗi biến thể đúng 1 preset; các biến thể trong lô khác nhau rõ về **kiểu hook hoặc preset** (không chỉ khác chữ). Bảng màu, chuyển cảnh, auto SFX của từng preset ở `tokens.presets`.

| Preset | Khi dùng | Chữ | Chuyển cảnh | Âm thanh |
|---|---|---|---|---|
| `pink` (mặc định) | mọi bản thương hiệu | thẻ `lower` tím mận 2 tầng, accent hồng/xanh | whip | pop, whoosh, click |
| `vox` | giải thích, nỗi đau, "vì sao" | chữ `vox` đen trên bút dạ vàng, khoanh đỏ, ảnh ghép giấy | paper | giấy, bút dạ |
| `kinetic` | hook mạnh | như pink + `kinetic` 1–1,5 s đầu | whip | slam theo từng cụm |
| `proof` | kết quả trước | `wipe`/`collage` trước/sau, `counter`, `shade` | whip | tick, ding |
| `ugc` | bản số lượng GMV Max | chữ `plain` trắng viền đen, không hộp | cut | không auto SFX |
| `gift` | 20.10, Tết, Valentine | thẻ hồng đậm | whip | pop, ding |
| `routine` | quy trình 15 phút: gel → đèn xanh → đèn đỏ | thẻ `lower` accent xanh, `light_timer`, `teeth` | cut | click, giữ tiếng ASMR thật |
| `reply` | trả lời câu hỏi khán giả (xử lý phản đối) | thẻ trắng chữ mực, câu hỏi ở hook | cut | pop |

Preset cũ của v1.4: `result_rewind` → `proof`, `beat` → `kinetic` (edl tự đổi). Preset nào thắng được học dần qua `vf learn --write` (theo preset × hook × độ dài) — điều chỉnh bảng này khi có bằng chứng.

## 7. Thư viện đồ hoạ

| Thành phần (skill v2) | Trong edl | Ghi chú |
|---|---|---|
| label | `overlays` (`lower`, `tag`, `hook`, `plain`, `cta`, `commit`, `vox`) | chữ theo preset |
| light_timer | `graphics.kind = "light_timer"`, `rows` | 2 hàng 10′ xanh / 5′ đỏ, hàng 2 `at` đúng lúc chuyển đèn. Kèm `light` nếu muốn vầng sáng |
| tooth_morph | `whiten` | icon răng vàng → trắng, ghi "Hình minh họa" |
| (hàm răng vector) | `teeth` | đèn xanh quét làm răng trắng dần, đèn đỏ dịu nướu — người dùng muốn giữ |
| draw_circle | `effects.zoom_to` (track teeth) + `graphics.callout` | zoom → khoanh → mũi tên → nhãn |
| polaroid | `collage` | 1–2 ảnh thật cắt từ nguồn, băng keo, nền giấy |
| day_counter | `counter` | NGÀY 1 → 7, 1–1,5 s |
| kinetic_hook | `kinetic`, `words` | cụm `*như này*` tô màu nhấn |
| end_card | `end_card`, `label`, `sub`, `live` | CTA cuối trong vùng an toàn |
| (thang màu) | `shade` | chỉ dùng số mức người nói nói ra |
| (thanh gạt trước/sau) | `wipe`, 2 `stills` | từ cảnh trước/sau thật |
| (chuyển cảnh giấy) | `paper_swipe` | render tự thêm ở ranh giới chương cho preset vox |

Gợi ý ghép:
- Cảnh đèn xanh/đỏ → `light_timer` (hoặc `teeth` + `light`). Không chồng nếu nguồn đã có chữ "ÁNH SÁNG XANH".
- Nỗi đau răng vàng → `zoom_to` bám răng → `callout` → nhãn.
- Kết quả → `wipe` hoặc `collage` sau khi cảnh trước/sau gốc chạy trọn; `shade` khi người nói nói số mức.
- Ngay sau cảnh dùng máy → `whiten`/`teeth` 1,5–2 s.

**Chưa có (cần làm thêm code):** chữ nằm sau người (tách nền), dừng hình + viền trắng cut-out, sản phẩm tách nền bay vào ở CTA, cột so sánh 8 triệu vs 800k, phụ đề từng từ đổi màu theo preset, chữ có chân nghiêng (Lora) cho dòng dẫn Vox.

## 8. Âm thanh

- Giọng −14 LUFS (loudnorm cuối). Nhạc nền dưới giọng 20 dB và tự hạ thêm khi có giọng (sidechain). Nhạc trend: để trống `music`, gắn nhạc Commercial Music Library trên TikTok.
- SFX tự gắn theo sự kiện (`tokens.auto_sfx`): chữ hiện → pop, ranh giới chương/zoom → whoosh, khoanh → marker, ảnh ghép/giấy → paper, đếm ngày/thang màu → tick, light_timer → click, tooth_morph → ding, kinetic → slam, thanh gạt → swipe, hàm răng → shimmer, end_card → pop. Preset `ugc` không auto SFX.
- File trong `library/brand/sfx/`; `vf make-sfx` tạo bản tạm bằng numpy — nên thay bằng SFX có bản quyền cùng tên.
- Giữ tiếng ASMR thật của nguồn (bấm máy, bôi gel, mở hộp).

## 9. Nên / không nên

**Nên:** một hệ chữ; đủ ý theo chương; giữ trọn cảnh trước/sau; zoom rồi mới chú thích; cam kết nổi bật; CTA giữa video + cuối, trong vùng an toàn; 3–6 biến thể khác nhau rõ.

**Không:** chữ đè chữ có sẵn; meme/sticker trong preset pink/vox/proof; mở đầu bằng giá; flash trắng; cảnh < 1,2 s; chỉnh màu răng thật; bịa before/after/số liệu; dùng hình, nhạc, giọng, câu chữ nguyên văn của video tham khảo.

## Phụ lục — video mẫu đã học (chỉ kỹ thuật)

- **A** `snaptik.vn_7690505641718271284.mp4` (33,4 s): bản dựng lại clip KOL hộp quà 20/10. Cảnh ~3,3 s, thẻ chữ tím mận 2 tầng gần mỗi cảnh, thẻ toàn màn hình khi chuyển ý, thanh đèn có tiến độ, nhãn TRƯỚC/SAU, polaroid.
- **B** `snaptik.vn_7694846295957081365.mp4` (45 s): motion graphic giải thích; câu dẫn nghiêng nhỏ + ô từ khoá viết hoa, bộ đếm số chạy.
