# Quy trình Edit Video Hàng Loạt cho Smilee bằng Claude Code — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Từ một hoặc nhiều video gốc + `brief.yaml` + hồ sơ sản phẩm, Claude Code tự cắt khoảng lặng, dựng hook, ghép đoạn từ nhiều nguồn, chèn phụ đề/text/hiệu ứng theo phong cách của video tham khảo, xuất N biến thể 9:16 sẵn đăng, rồi học từ điểm chấm của người dùng.

**Architecture:** Pipeline Python: (1) *Phân tích* — faster-whisper lấy transcript từng từ, ffmpeg tìm khoảng lặng, đo cảnh cắt của video tham khảo; (2) *Lên kịch bản dựng* — Claude đọc transcript + brief + sản phẩm + style-guide + bài học, viết `edl.json` (mỗi biến thể là danh sách đoạn, mỗi đoạn tự khai nguồn); (3) *Render* — ffmpeg dựng từ `edl.json`; giai đoạn 2 thêm lớp motion graphic bằng Remotion; (4) *QA + học* — kiểm tra kỹ thuật, kiểm tra claim cấm, người dùng chấm điểm, Claude ghi bài học. Phần "não" nằm trong skill `video-batch-edit` để cải tiến mà không đụng code.

**Tech Stack:** Python 3.11, ffmpeg ≥ 6, faster-whisper (`large-v3`, tiếng Việt), pydantic v2, typer, pytest. Giai đoạn 2: Node 20 + Remotion.

**Spec:** Yêu cầu của người dùng ngày 2026-10-13: input là video tự quay (một hoặc nhiều nguồn, có thể ghép chung một video); AI edit theo hook, text, hiệu ứng, cắt âm thanh thừa, nhiều mẫu thử; học phong cách từ video tham khảo (ngôn ngữ dựng, chuyển cảnh, motion graphic, motion text, hướng "Vox style"); sản phẩm: Kit trắng răng Smilee (xem `library/product.md`).

## Global Constraints

- Ngôn ngữ transcript mặc định: `vi`. Font phụ đề phải hiển thị đủ dấu tiếng Việt.
- Xuất mặc định: 1080x1920, 30 fps CFR, H.264 `-crf 20`, AAC 192k, loudness -14 LUFS ±1.
- Không bao giờ ghi đè hay xoá file nguồn; mọi output vào `<drive_root>/out/<lô>/`.
- Mã nguồn ở ổ đĩa máy; chỉ video (nguồn, tham khảo, output) nằm trong Drive. Đường dẫn đọc từ `vf.toml` (`drive_root`).
- Mỗi biến thể có hook ≤ 3 giây đầu; tổng thời lượng trong `target_seconds ± 10%`.
- Khoảng lặng bị cắt: ngưỡng -35 dB, dài ≥ 0.4 s, chừa đệm 0.08 s mỗi bên.
- Mọi chữ hiển thị (overlay, phụ đề) không được chứa cụm trong `library/forbidden.txt`; vi phạm thì render bị chặn.
- Không tự tạo ảnh/clip before-after, review khách hay số liệu; chỉ dùng tư liệu người dùng cung cấp trong `library/assets/`.
- Video tham khảo chỉ để học phong cách (nhịp, chuyển cảnh, kiểu chữ); không dùng lại hình, nhạc hay giọng của chúng trong output.

## Review Focus

1. Video iPhone `.mov` thường là HEVC + khung hình biến thiên (VFR) → cắt ghép lệch tiếng/hình. Chuẩn hoá về 30 fps CFR H.264 trước khi phân tích (Task 2).
2. Video không có lời nói (chỉ cảnh sản phẩm) → transcript rỗng; pipeline vẫn chạy, bỏ phụ đề, không crash (Task 2, 5).
3. Nhiều nguồn khác độ phân giải, hướng xoay, độ to → ghép không méo hình, không nhảy âm lượng ở chỗ nối (Task 5).
4. `edl.json` có đoạn vượt độ dài nguồn của chính nó hoặc nguồn không tồn tại → báo lỗi rõ tên biến thể + đoạn (Task 3).
5. Phụ đề lệch thời gian sau khi cắt/ghép nhiều nguồn → ánh xạ lại theo timeline output (Task 4).

---

### Task 0: Khung dự án, cấu hình và môi trường

**Files:**
- Create: `pyproject.toml`, `vf/__init__.py`, `vf/config.py`, `vf.toml.example`, `tests/conftest.py`, `library/{brand,assets,references}/.gitkeep`, `library/hooks.md`, `library/learnings.md`, `library/style-guide.md`
- Test: `tests/test_env.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `load_config(path: Path = Path("vf.toml")) -> Config(drive_root: Path, sources_dir: Path, references_dir: Path, out_dir: Path)` — `sources_dir = drive_root/"source gốc"`, `references_dir = drive_root/"video tham khảo"`, `out_dir = drive_root/"out"`; fixture `sample_video` (5 s: 1 s im lặng, 2 s tone 440 Hz, 1 s im lặng, 1 s tone, hình 3 màu đổi ở 1.7 s và 3.4 s) và `sample_video_b` (3 s, 1920x1080, tone 880 Hz) dùng cho mọi task sau.

- [ ] **Step 1:** Test `test_ffmpeg_available` (ffmpeg ≥ 6), `test_sample_video_fixture` (ffprobe duration ≈ 5.0 ±0.1), `test_config_resolves_drive_paths` (drive_root `G:/My Drive/EDIT` → `sources_dir` kết thúc bằng `source gốc`).
- [ ] **Step 2:** Run `pytest tests/test_env.py tests/test_config.py -v` → FAIL.
- [ ] **Step 3:** Implement pyproject (faster-whisper, pydantic>=2, typer, pyyaml, pytest), config (đọc TOML bằng `tomllib`), fixtures bằng `ffmpeg -f lavfi`.
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** `git init && git commit -m "chore: scaffold video-factory"`

### Task 1: Brief schema và hồ sơ sản phẩm

**Files:** Create `vf/brief.py`, `templates/brief.yaml`, `library/product.md` (chuyển từ `Thông tin sản phẩm smilee.docx` trong Drive), `library/forbidden.txt`; Test `tests/test_brief.py`

**Interfaces:**
- Produces:
  - `class Brief(BaseModel)`: `platform: Literal["tiktok","reels","shorts"]`, `aspect: Literal["9:16","1:1","16:9"]="9:16"`, `target_seconds: int`, `variants: int = 3` (1–20), `goal: Literal["awareness","education","conversion"]`, `message: str`, `cta: str`, `audience: str = ""`, `source_roles: dict[str, str] = {}` (tên file nguồn → vai trò, vd `"a_roll"`, `"b_roll"`), `must_keep: list[str] = []`, `must_cut: list[str] = []`, `hook_ideas: list[str] = []`, `tone: str = ""`, `forbidden: list[str] = []`, `style: str = "default"`
  - `load_brief(path: Path, forbidden_path: Path = Path("library/forbidden.txt")) -> Brief` — gộp `forbidden` của brief với từng dòng của `forbidden.txt`, bỏ trùng.
- `library/forbidden.txt` (mỗi dòng một cụm, lấy từ mục "Những điều KHÔNG được nói" của hồ sơ sản phẩm): `điều trị`, `chữa`, `loại bỏ vi khuẩn`, `tái tạo men răng`, `thay thế nha sĩ`, `100% an toàn`, `không bao giờ ê buốt`, `thần kỳ`, `đảm bảo`, `cấp tốc`.
- `library/product.md`: giữ nguyên các mục và các dấu `[CẦN XÁC NHẬN]` của hồ sơ gốc; không tự điền thay chỗ thiếu.

- [ ] **Step 1:** Test: `templates/brief.yaml` load OK; `variants: 0` raise `ValidationError`; thiếu `message` raise; `load_brief` trả `forbidden` chứa `"thần kỳ"` dù brief không khai; hai nguồn trùng cụm chỉ xuất hiện một lần.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; chuyển docx sang markdown bằng pandoc hoặc python-docx. **Step 4:** Run → PASS. **Step 5:** Commit.

### Task 2: Phân tích — chuẩn hoá, transcript, khoảng lặng

**Files:** Create `vf/probe.py`, `vf/transcribe.py`, `vf/silence.py`; Test `tests/test_analyze.py`

**Interfaces:**
- Produces:
  - `normalize(src: Path, dst: Path) -> Path` (H.264, 30 fps CFR, áp dụng hướng xoay vào hình)
  - `probe(path: Path) -> MediaInfo(duration: float, width: int, height: int, fps: float, has_audio: bool, codec: str)`
  - `@dataclass Word(text: str, start: float, end: float)`; `transcribe(path: Path, lang: str = "vi") -> list[Word]` (faster-whisper, `word_timestamps=True`)
  - `@dataclass Range(start: float, end: float)`; `detect_silences(path: Path, noise_db: float = -35, min_dur: float = 0.4) -> list[Range]`; `keep_ranges(duration: float, silences: list[Range], pad: float = 0.08) -> list[Range]`
  - Ghi `work/<tên-nguồn>/{normalized.mp4, transcript.json, silences.json, keep.json}`; `analyze_all(sources_dir: Path, work_dir: Path) -> dict[str, MediaInfo]` chạy cho mọi file nguồn.

- [ ] **Step 1:** Tests: `detect_silences(sample_video)` ≈ [0,1] và [3,4] (±0.1); `keep_ranges(5.0, …)` ≈ [[0.92,3.08],[3.92,5.0]]; `normalize` ra fps == 30 và codec h264 (kể cả khi đầu vào HEVC); video không audio → `detect_silences` và `transcribe` đều trả `[]`; `analyze_all` với hai nguồn trả hai khoá.
- [ ] **Step 2:** FAIL. **Step 3:** Implement (`silencedetect` parse stderr; test `transcribe` thật gắn `@pytest.mark.slow`). **Step 4:** PASS. **Step 5:** Commit.

### Task 3: EDL — định dạng kịch bản dựng, nhiều nguồn

**Files:** Create `vf/edl.py`, `templates/edl.example.json`; Test `tests/test_edl.py`

**Interfaces:**
- Consumes: `MediaInfo`.
- Produces:
  - `Segment(source: str, start: float, end: float)` — `source` là tên file trong `sources_dir`; thời gian theo timeline của chính nguồn đó.
  - `TextOverlay(text: str, start: float, end: float, position: Literal["top","center","bottom"]="top", style: str = "hook")` — thời gian theo timeline output.
  - `Effect(kind: Literal["zoom_punch","shake","flash","sfx","highlight"], at: float, duration: float = 0.3, asset: str | None = None)`
  - `Variant(id: str, hook_type: str, hook: Segment, segments: list[Segment], overlays: list[TextOverlay] = [], effects: list[Effect] = [], captions: bool = True, music: str | None = None, rationale: str)` — output = `hook` rồi tới `segments`; các đoạn có thể thuộc nguồn khác nhau.
  - `EDL(job: str, variants: list[Variant])`; `load_edl(path: Path, infos: dict[str, MediaInfo]) -> EDL`; `output_duration(v: Variant) -> float`.

- [ ] **Step 1:** Tests: example load OK với hai nguồn; segment có `end` > duration **của nguồn nó** → `ValueError` nêu variant id + segment; `source` không có trong `infos` → lỗi nêu tên nguồn; `start >= end` → lỗi; hook dài > 3 s → lỗi; `output_duration` = tổng độ dài hook + segments.
- [ ] **Step 2–5:** FAIL → implement (pydantic validators) → PASS → commit.

### Task 4: Phụ đề ASS theo timeline mới

**Files:** Create `vf/captions.py`, `templates/caption_style.ass`; Test `tests/test_captions.py`

**Interfaces:**
- Consumes: `Word`, `Segment`.
- Produces: `remap_words(words_by_source: dict[str, list[Word]], pieces: list[Segment]) -> list[Word]` (với từng đoạn theo thứ tự, giữ từ nằm trọn trong đoạn của đúng nguồn, dịch sang timeline output; từ bị cắt ngang mép thì bỏ); `words_to_ass(words: list[Word], style_path: Path, max_words: int = 4) -> str` (3–4 từ/dòng, từ đang nói đổi màu bằng `\k`).

- [ ] **Step 1:** Tests: nguồn A có từ ở 1.0–1.2, nguồn B có từ ở 0.5–0.7; pieces [A 0.9–1.5, B 0.4–0.9] → output [0.1–0.3] và [0.7–0.9]; `words_to_ass` giữ nguyên dấu tiếng Việt ("Răng trắng sáng"); danh sách rỗng → ASS hợp lệ không có `Dialogue`.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit.

### Task 5: Render một biến thể

**Files:** Create `vf/render.py`; Test `tests/test_render.py`

**Interfaces:**
- Consumes: `Variant`, `MediaInfo`, `words_to_ass`, `remap_words`, `measure_lufs` (Task 6).
- Produces: `build_ffmpeg_cmd(sources: dict[str, Path], infos: dict[str, MediaInfo], v: Variant, ass: Path | None, brand: Path, out: Path) -> list[str]`; `render_variant(...) -> Path`.
- Quyết định: mỗi đoạn `trim/atrim` từ nguồn của nó, đưa về 1080x1920 trước khi `concat` (nguồn dọc: `scale`; nguồn ngang: nền blur + video giữa, không crop mất người nói); cân gain từng nguồn về -16 LUFS bằng `volume` (đo một lần cho cả file nguồn), sau `concat` mới `loudnorm=I=-14:TP=-1.5:LRA=11`; chỗ nối giữa hai nguồn khác nhau chèn `acrossfade` 0.08 s; `zoom_punch` = scale 1.0→1.08 trong `duration`; overlay = `drawtext` với font brand; nhạc nền `amix` ở -18 dB dưới giọng.

- [ ] **Step 1:** Tests: variant từ `sample_video` + `sample_video_b` → output 1080x1920, duration == `output_duration ±0.15`, tỉ lệ pixel không méo; `captions=False` hoặc transcript rỗng → lệnh không có filter `subtitles`; hai nguồn lệch -10 dB → chênh loudness giữa hai nửa output ≤ 2 LU.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit. Lệnh ffmpeg lỗi → dùng agent `ffmpeg-expert`.

### Task 6: QA tự động, đo loudness, chặn claim cấm

**Files:** Create `vf/qa.py`; Test `tests/test_qa.py`

**Interfaces:**
- Produces: `measure_lufs(path: Path) -> float`; `QAReport(path, duration_ok: bool, size_ok: bool, loudness_lufs: float, loudness_ok: bool, claim_violations: list[str], notes: list[str])`; `check_output(path: Path, expected: float, size=(1080,1920)) -> QAReport`; `check_claims(texts: list[str], forbidden: list[str]) -> list[str]` (không phân biệt hoa thường và dấu cách thừa; trả về các cụm bị vi phạm); `contact_sheet(path: Path, out_png: Path, cols: int = 6) -> Path`.
- `render_variant` gọi `check_claims` trên mọi `overlays[].text` và chữ phụ đề **trước khi** render; có vi phạm thì raise `ClaimViolation` nêu variant id và cụm.

- [ ] **Step 1:** Tests: output hợp lệ → mọi `_ok` True; file -30 LUFS → `loudness_ok` False kèm note; `check_claims(["Trắng THẦN  KỲ"], ["thần kỳ"])` == `["thần kỳ"]`; `check_claims(["Trắng 3–4 tone"], [...])` == `[]`.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit.

### Task 7: CLI điều phối và skill `video-batch-edit`

**Files:** Create `vf/cli.py`, `.claude/skills/video-batch-edit/SKILL.md`; Test `tests/test_cli.py`

**Interfaces:**
- Produces CLI:
  - `vf analyze <lô>` → Task 2 cho mọi file trong `sources_dir`
  - `vf render <lô>` → đọc `jobs/<lô>/edl.json`, render từng biến thể, QA, ghi `<out_dir>/<lô>/<variant>.mp4`, `<variant>_sheet.png`, `qa.json`, và `review.csv` (cột: variant, hook_type, hook_text, score, notes, views, retention_3s)
- SKILL.md bắt Claude: (1) `vf analyze`; (2) đọc `brief.yaml`, `library/product.md`, `library/style-guide.md`, `library/hooks.md`, `library/learnings.md`, transcript của mọi nguồn; (3) viết `edl.json` có `brief.variants` biến thể **khác nhau về kiểu hook** (nỗi đau / câu hỏi / kết quả trước / phản đề / so sánh chi phí), dùng nguồn theo `source_roles`, tôn trọng `must_keep`, `must_cut`, `forbidden`, mục "Những điều KHÔNG được nói" và mọi dòng còn `[CẦN XÁC NHẬN]` (không đưa claim chưa có bằng chứng vào chữ trên màn hình); (4) `vf render`; (5) xem contact sheet, sửa edl, render lại biến thể lỗi; (6) báo người dùng danh sách file + một dòng mô tả mỗi biến thể.

- [ ] **Step 1:** Test: `vf analyze` + `vf render` trên job mẫu (hai nguồn + brief + edl example) → 3 mp4, `qa.json` hợp lệ, `review.csv` 3 dòng; edl chứa "thần kỳ" trong overlay → lệnh thoát mã ≠ 0 và không có file mp4 của biến thể đó.
- [ ] **Step 2–5:** FAIL → implement (typer) → PASS → commit.

### Task 8: Vòng học — skill `video-learnings`

**Files:** Create `.claude/skills/video-learnings/SKILL.md`, `vf/learn.py`; Test `tests/test_learn.py`

**Interfaces:**
- Produces: `summarize_reviews(csv_paths: list[Path]) -> list[HookStat(hook_type: str, n: int, avg_score: float, avg_retention: float | None)]`.
- SKILL.md: đọc mọi `review.csv`, gọi `summarize_reviews`, cập nhật `library/hooks.md` (xếp hạng kiểu hook + ví dụ thắng) và `library/learnings.md` (mỗi dòng có ngày + bằng chứng); không xoá bài học cũ trừ khi dữ liệu mới bác bỏ.

- [ ] **Step 1:** Test: hai csv giả → `HookStat` đúng trung bình; csv thiếu cột `views` → `avg_retention` là None, không crash.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit.

### Task 9: Học phong cách từ video tham khảo

**Files:** Create `vf/style.py`, `.claude/skills/video-style-learning/SKILL.md`; Test `tests/test_style.py`

**Interfaces:**
- Produces: `shot_stats(path: Path, threshold: float = 0.3) -> ShotStats(duration: float, n_cuts: int, avg_shot_s: float)` (ffmpeg `select='gt(scene,threshold)'`); `reference_frames(path: Path, out_dir: Path, every_s: float = 1.0) -> list[Path]`; CLI `vf style` chạy cho mọi file trong `references_dir`, ghi `work/style/<tên>/{stats.json, frames/, transcript.json}`.
- SKILL.md: đọc số đo + xem khung hình + transcript của từng video tham khảo, rồi viết `library/style-guide.md` gồm: nhịp cắt trung bình, kiểu hook (giây 0–3), kiểu chuyển cảnh, vị trí/kiểu/font chữ, kiểu chữ chuyển động, hiệu ứng lặp lại, kiểu nhạc/SFX, bảng màu, và mục "nên bắt chước / không bắt chước". Phần bắt chước chỉ nói về kỹ thuật, không sao chép hình, nhạc, giọng của video gốc.

- [ ] **Step 1:** Test: `shot_stats(sample_video)` có `n_cuts == 2` (ba màu); `reference_frames` ra đúng số ảnh ≈ duration / every_s.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit.
- [ ] **Step 6:** Chạy trên 4 video trong `video tham khảo`, người dùng duyệt `style-guide.md` trước khi dựng pilot.

### Task 10 (giai đoạn 2, sau khi pilot được duyệt): Lớp motion graphic bằng Remotion

**Files:** Create `remotion/` (project Remotion), `remotion/src/{HighlightText,LowerThird,KaraokeCaption}.tsx`, `vf/overlay.py`; Test `tests/test_overlay.py`

**Interfaces:**
- Produces: `render_overlay(v: Variant, style_guide: Path, out: Path) -> Path` (video nền trong suốt cùng độ dài `output_duration(v)`, 1080x1920, 30 fps); `build_ffmpeg_cmd` nhận thêm `overlay: Path | None` và chồng lên bằng filter `overlay`. Dùng skill `remotion:remotion-best-practices` và `remotion:remotion-captions`.
- Yêu cầu: preset "vox" gồm vệt highlight chạy trên chữ, nhãn chú thích + mũi tên, chữ xuất hiện từng từ, nền giấy; màu và font lấy từ `library/brand/`.

- [ ] **Step 1:** Test: `render_overlay` cho biến thể mẫu → ffprobe thấy pix_fmt có kênh alpha (`yuva`) và duration == `output_duration ±0.1`.
- [ ] **Step 2–5:** FAIL → implement → PASS → commit.
