# Style guide Smilee

Trạng thái: ĐÃ DUYỆT 2026-10-14 — cập nhật Vox 2026-10-14 (feedback lô lo-02); v1.4 2026-10-14: vùng an toàn, âm thanh, preset, typography theo xu hướng TikTok 2026 (mục 7, 11–14)

Video đã xem (thư mục `EDIT/video mẫu tham khảo/`, chỉ học kỹ thuật):
- **A** `snaptik.vn_7690505641718271284.mp4` — 33.4 s, 576x1024. Bản dựng lại clip KOL hộp quà 20/10 (cùng nguồn với lo-01).
- **B** `snaptik.vn_7694846295957081365.mp4` — 45.0 s, 576x1024. Video giải thích dạng motion graphic (dựng video bằng AI).

Dò cắt cảnh: ffmpeg `scdet`, ngưỡng 10. Nhạc/SFX: chưa phân tích.

## 1. Nhịp cắt

| Video | Số lần cắt | Giây/cảnh | Ghi chú |
|---|---|---|---|
| A | 9 | ~3.3 s (2.3–3.8 s) | Không cảnh nào < 1.3 s |
| B | 2 | ~15 s | Cảnh dài, chuyển động nằm ở motion graphic |
| Nguồn KOL lo-02 | 67 | ~2.6 s, nhiều đoạn 0.6 s | Nhanh hơn mẫu nhiều → phải bỏ các chuỗi dựng nhanh |

Quy tắc: mỗi cảnh trong output **≥ 1.2 s, nhắm 2–4 s**. Không giữ chuỗi cảnh < 1 s của nguồn (ví dụ nhật ký 7 ngày); thay bằng một cảnh dài + motion graphic đếm ngày.

## 2. Hook (giây 0–3)

- A: mở bằng hành động (mở hộp quà) + cảnh cận răng/sản phẩm, chữ chưa xuất hiện ngay.
- B: mở bằng câu ngắn chữ nghiêng nhỏ ở trên + **cụm then chốt viết hoa trong ô màu** ("MẤT CẢ BUỔI", "CHỈ CẦN NÓI"), xuất hiện ở giây 1.
- Áp dụng: hook = 1 dòng nhỏ dẫn + 2–4 từ viết hoa trong ô màu, ở 1/4 trên khung.

## 3. Chuyển cảnh

- Chủ yếu **cắt thẳng**; chữ/thẻ đổi theo cảnh (A).
- **Thẻ toàn màn hình** 1–1.5 s để chuyển ý (A giây 11: nền tím mận + hình răng + "NGẢ VÀNG → TỰ TIN KHOE RĂNG"; B: nền đen/đỏ đô + tiêu đề).
- Không flash trắng, không rung. `zoom_punch` nhẹ ở chỗ nhấn là đủ.

## 4. Chữ trên hình

**Thẻ chữ dưới (A, kiểu chính):** hộp bo góc nền tím mận đậm mờ (~#3A1230, 85 %), dòng 1 viết hoa đậm màu hồng (~#FF8DBA), dòng 2 chữ thường trắng nhỏ (~45 % cỡ dòng 1). Đặt khoảng 45–60 % chiều cao, mép dưới thẻ **không quá 65.6 %** (vùng an toàn, mục 13), không che miệng/răng. 2–5 từ dòng 1, ≤ 7 từ dòng 2.
Ví dụ cấu trúc: "MẢNG BÁM NGẢ VÀNG / thấy rõ luôn", "SAU 7 NGÀY / lên tông thấy rõ luôn".

**Ô nhấn từ khoá (B):** 2–4 từ viết hoa chữ trắng trên ô đỏ/hồng đặc, nằm ngay dưới một dòng dẫn chữ nghiêng nhỏ.

**Phụ đề động (B):** 2–4 từ một lúc, chữ trắng đậm ở 1/5 dưới, **một từ khoá trong ô màu**. Chỉ dùng khi nguồn không có phụ đề in sẵn.

Font: không chân, rất đậm (Montserrat ExtraBold đang dùng là hợp). B có dùng chữ có chân cho tiêu đề — không bắt buộc.

## 5. Motion graphic / minh hoạ

- **Thanh đèn (A 13–17 s):** hai thẻ xếp chồng: "10 PHÚT" chữ xanh + "ánh sáng xanh / làm trắng răng"; "5 PHÚT" chữ đỏ + "ánh sáng đỏ / làm dịu nướu"; **thanh tiến độ** chạy xanh rồi đỏ bên dưới.
- **Ảnh chèn nghiêng kiểu polaroid (A 7–8 s):** 1–2 ảnh nhỏ nghiêng ±6°, viền trắng, chú thích hồng ("MẢNG BÁM · NGẢ VÀNG"). Chỉ dùng ảnh thật lấy từ chính nguồn.
- **Nhãn trước/sau (A 18–21 s):** viên thuốc hồng "TRƯỚC" / "SAU ✓" + ô hình nhỏ góc trên (picture-in-picture) cảnh trước, cảnh chính là sau.
- **Bộ đếm (B 7–11 s):** số chạy tăng kèm icon ("0,4 giờ → 4,0 giờ"). Áp dụng: "Ngày 1 → Ngày 7".
- **Thẻ minh hoạ toàn màn hình (A 11 s):** nền tím mận, hình vector răng, chữ hồng.
- Hàm răng vector (đèn xanh quét làm răng vàng → trắng, đèn đỏ dịu nướu) — pipeline đã có (`graphics.kind = "teeth"`), cần đổi màu sang bảng màu dưới.

## 6. Hiệu ứng lặp lại

Thẻ chữ dưới xuất hiện gần như mỗi cảnh ở A (cùng một kiểu, đổi nội dung). Thẻ toàn màn hình ở chỗ chuyển ý và kết (CTA).

## 7. Nhạc / SFX

TikTok là nền tảng **bật tiếng**: âm thanh là thứ giữ chân đầu tiên, không phải lớp thêm sau cùng. Video không nhạc, không SFX là lỗi (QA ghi `âm thanh:`).

- **SFX tự động** (`vf/creative.py`, tắt bằng `"sfx_auto": false`): file trong `library/brand/sfx/`, đặt tên đúng vai trò. Thiếu file nào thì bỏ qua cue đó. Mức −8 dB, nằm dưới giọng.

| File | Gắn vào |
|---|---|
| `whoosh` | `zoom_to`, `zoom_punch` |
| `marker` | `callout` (tiếng bút dạ) |
| `paper` | `collage` |
| `tick` | `counter`, `shade` |
| `swipe` | `wipe` |
| `shimmer` | `teeth`, `whiten` (lấp lánh khi răng trắng) |
| `pop` | thẻ `tag`, `cta`, `commit` |

- **Nhạc nền**: chỉ nhạc có giấy phép trong `library/brand/` (render tự hạ −18 dB dưới giọng). Nhạc trend/nhạc thương mại thì để trống `music` và gắn nhạc từ **Commercial Music Library** ngay trong TikTok/Ads Manager — không lấy "âm thanh gốc" của người khác.
- **ASMR sản phẩm**: giữ tiếng thật của nguồn khi bấm máy, bôi gel, mở hộp (đừng cắt mất).

## 8. Bảng màu

| Vai trò | Màu |
|---|---|
| Nền thẻ, thẻ toàn màn hình | tím mận #3A1230 (A) / đỏ đô #6B1A26 (B) |
| Chữ nhấn | hồng #FF8DBA |
| Ô từ khoá | đỏ hồng #E0245E, chữ trắng |
| Đèn xanh / đèn đỏ | #2F7BFF / #FF3B4E |
| Chữ phụ | trắng |

## 9. Nên bắt chước / Không bắt chước

**Nên:** nhịp 2–4 s/cảnh; thẻ chữ hai dòng nền tím mận; ô từ khoá; thanh đèn có tiến độ; nhãn TRƯỚC/SAU; bộ đếm; thẻ toàn màn hình khi chuyển ý.

**Không:** hình, nhạc, giọng, câu chữ nguyên văn của A và B; thương hiệu/giao diện phần mềm trong B; "SĂN SALE / VÀO LIVE" (A) khi `goal` là awareness; mọi cụm trong `forbidden.txt` và `claims_pending.txt` (ví dụ "cấp tốc", "đảm bảo").

## 10. Phong cách Vox (bổ sung 2026-10-14, feedback lo-02)

Nguyên tắc: **chỉ thêm đồ hoạ ở đoạn nguồn "trơn"** (không có chữ in sẵn, không có sticker/khoanh/hình minh hoạ sẵn). Đoạn nguồn đã tự minh hoạ (đèn sáng, bảng màu, khoanh đỏ có sẵn) → để nguyên.

- **Zoom ống kính** (`effects.kind = "zoom_to"`, `zoom` 1.4–1.7, `track: "teeth"` để bám theo răng): đẩy chậm 0.35 s vào chi tiết cần nói (răng vàng), giữ tới hết cảnh.
- **Khoanh tay → mũi tên → ghi chú** (`graphics.kind = "callout"`): vòng đỏ vẽ tay quanh răng, mũi tên, rồi mới hiện nhãn chữ đen trên **vệt bút dạ vàng** (#FFE14D). Thứ tự bắt buộc: zoom → khoanh → mũi tên → chữ.
- **Ảnh ghép giấy** (`graphics.kind = "collage"`): nền giấy kem có hạt, 1–2 ảnh cắt từ chính nguồn, viền trắng, băng keo, nghiêng ±4–5°, nhãn bút dạ ("TRƯỚC" / "SAU 7 NGÀY"). Đặt **sau** cảnh trước/sau gốc (để cảnh gốc chạy trọn), trên một đoạn nói chuyện trơn.
- **Chữ Vox** (`style: "vox"`): dòng chính viết hoa đen trên vệt bút dạ vàng quét trái → phải, dòng phụ trên dải giấy trắng. Dùng cho ý bổ sung (gel tiết kiệm, đắp mặt nạ). CTA cuối vẫn dùng thẻ tím mận `lower`.
- **Không bỏ** hàm răng vector (`teeth`), vầng sáng đèn (`light`), thẻ đếm ngày (`counter`) — người dùng muốn giữ (2026-10-14). Dùng khi hợp bối cảnh: đoạn nói về đèn xanh/đỏ mà còn chỗ trống không che mặt, không đè chữ/hình minh hoạ có sẵn (ví dụ phía trên đầu trong cảnh trung, hoặc nguồn không quay cảnh đèn). Chỉ tránh đặt chúng chồng lên phần nguồn đã tự minh hoạ cùng ý đó.


## 11. Preset dựng (v1.4) — mỗi biến thể MỘT preset, không trộn

Ghi `"preset"` trong edl. Các biến thể trong một lô nên khác preset hoặc khác hook hình, để mỗi bản là một phương án test thật.

| Preset | Dựng thế nào | Đồ hoạ dùng | Hợp với |
|---|---|---|---|
| `ugc` | Gần như nguồn gốc, cắt gọn, cận sản phẩm ở giữa video | 2–3 ô từ khoá, `cta` | Spark Ads, chuyển đổi |
| `result_rewind` | 0–2 s: cận nụ cười "sau" → `wipe` hoặc chữ "7 ngày trước…" → hành trình | `wipe`, `shade`, `counter` | hook `result_first` |
| `vox` | Zoom bám răng, khoanh, ảnh ghép giấy, nhịp chậm | `zoom_to`, `callout`, `collage`, chữ `vox` | giáo dục, nhận diện |
| `routine` | Quy trình 15 phút: gel → đèn xanh → đèn đỏ, giữ tiếng ASMR | `teeth`, `light`, `counter` | lợi ích "tại nhà, 15 phút" |
| `reply` | Mở bằng câu hỏi khán giả ("Dùng có ê buốt không?") rồi KOL trả lời | chữ `hook` dạng câu hỏi | xử lý phản đối |
| `beat` | Bản ngắn 15–20 s, chữ đập theo nhịp nhạc | ô từ khoá `pop` | test hook nhanh |

`reply`: chỉ dùng câu hỏi/bình luận thật (khách đồng ý) hoặc ghi "Nhiều bạn hỏi:"; không bịa bình luận (hồ sơ sản phẩm cấm review tự bịa).

**Thời lượng**: bản chính theo brief; khi brief có `cutdown_seconds` (gợi ý 20–25 s) thì thêm bản ngắn với `"cutdown_of": "<id bản chính>"`. **CTA**: một CTA mềm ở 60–85 % thời lượng + CTA cuối (QA nhắc nếu chỉ có ở cuối).

## 12. Hệ chữ (typography)

- **Tối đa 2–3 kiểu chữ**: Montserrat ExtraBold (chữ chính) + chữ Vox (bút dạ). Font viết tay cho ghi chú Vox: chưa có — cần người dùng duyệt file OFL có đủ dấu tiếng Việt.
- **Phân màu theo vai trò, không trộn trong một cảnh**: tím mận/hồng = lợi ích, CTA; vàng bút dạ/đỏ mực = chú thích Vox; ô đỏ hồng = từ khoá.
- **Chỉ từ khoá chuyển động** (`highlight` có `emphasis`, `pop`); cả câu đứng yên. Đặt từ khoá đúng lúc người nói nói ra từ đó (mốc từ trong transcript).
- **Hook có chữ trước 0.5 s**, 1 dòng ≤ 6 từ (trừ khi nguồn đã có chữ in sẵn ở hook).
- **Đọc kịp**: ≤ 3.5 từ/giây mỗi overlay; tối đa 2 khối chữ cùng lúc.

## 13. Vùng an toàn TikTok (bắt buộc)

**Chỉ áp dụng cho phần thêm vào** (chữ, thẻ, nhãn, graphic, phụ đề do pipeline tạo). Nội dung có sẵn trong source gốc (chữ in sẵn, sticker, phụ đề KOL) giữ nguyên, không dời, không cắt, không né đoạn vì nó (người dùng chốt 2026-10-14).

Khung 1080×1920. Chữ, nhãn, thẻ, hình minh hoạ thêm vào **không được** nằm trong:

| Vùng | Kích thước | Bị che bởi |
|---|---|---|
| Trên | 240 px (12.5 %) | thanh tab, nhãn "Được tài trợ" |
| Dưới | 660 px (từ 65.6 % xuống) | tên tài khoản, caption, nhạc, nút CTA quảng cáo |
| Hai bên | 120 px mỗi bên | mép màn hình |
| Cột nút phải | rộng 180 px, từ y = 840 px (43.75 %) xuống | avatar, tim, bình luận, lưu, chia sẻ |

Số liệu từ file template safe zone của TikTok (theo Socialync), lấy bộ chặt nhất. Một nguồn số liệu duy nhất: `vf/safezone.py`.

Pipeline tự đảm bảo:
- `vf/placement.py` chỉ chọn `y` trong vùng an toàn; hộp chữ thu hẹp (tối đa ~696 px) khi chạm hàng cột nút; `y` ghi tay trong edl bị kéo vào trong (QA ghi chú); vòng khoanh `callout` bị kéo vào trong.
- Remotion nhận `safe`: thẻ đếm ngày căn giữa vùng an toàn, ảnh ghép/`wipe` bố cục trong vùng an toàn, nhãn khoanh tự lên trên vòng khi dưới không đủ chỗ, chữ Vox tự xuống dòng.
- QA đọc kênh alpha **lớp chữ/hình thêm vào** (không đọc hình gốc): chỗ nào đặc (≥ 85 %) lấn vùng cấm → ghi `vùng an toàn: …` và biến thể thành **CẦN XEM**. Ảnh `*_sheet.png` kẻ viền đỏ quanh vùng an toàn.
- Được phép tràn mép: vầng sáng đèn, bóng đổ, hạt sáng mờ (< 85 %), nền phủ kín của thẻ toàn màn hình.

## 14. Motion graphic theo xu hướng 2026

**Đã có trong pipeline (v1.4):**
- `shade` — thang màu răng, con trỏ trượt `from_shade` → `to_shade`. Chỉ dùng số người nói nói ra (lo-02: "tầng 9–10 xuống 6–5"); `label` ghi nguồn ("theo trải nghiệm của Giao").
- `wipe` — thanh gạt trước/sau toàn màn hình, 2 `stills` cắt từ cảnh trước/sau **thật** của nguồn (cùng điều kiện ánh sáng). Đặt sau cảnh trước/sau gốc, như `collage`.

**Chưa có (đề xuất, cần làm thêm code):** chữ nằm sau người (tách nền MediaPipe), dừng hình + viền trắng cut-out ở hook, sản phẩm tách nền bay vào ở CTA (cần ảnh PNG sản phẩm, hồ sơ mục 8), cột so sánh 8 triệu vs 800k ở nửa sau video, thanh tiến độ video. Không tự dựng hiệu ứng thay thế bằng chữ cho các mục này.
