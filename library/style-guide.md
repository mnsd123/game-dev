# Style guide Smilee

Trạng thái: ĐÃ DUYỆT 2026-10-14 — cập nhật Vox 2026-10-14 (theo feedback người dùng lô lo-02)

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

**Thẻ chữ dưới (A, kiểu chính):** hộp bo góc nền tím mận đậm mờ (~#3A1230, 85 %), dòng 1 viết hoa đậm màu hồng (~#FF8DBA), dòng 2 chữ thường trắng nhỏ (~45 % cỡ dòng 1). Đặt khoảng 55–70 % chiều cao, không che miệng/răng. 2–5 từ dòng 1, ≤ 7 từ dòng 2.
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

Chưa phân tích. Khi dùng nhạc: chỉ nhạc có bản quyền đặt trong `library/brand/`.

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
- Không còn: hàm răng vector / vầng sáng đèn / thẻ đếm ngày đè lên cảnh nguồn đã minh hoạ.
