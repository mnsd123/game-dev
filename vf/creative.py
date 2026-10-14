"""Luật dựng của skill v2 kiểm được bằng máy (giá trị trong library/brand/tokens.json):
- tự sửa: kéo dài thời gian giữ chữ cho đủ đọc;
- tự thêm: SFX theo sự kiện (tokens.auto_sfx), chuyển cảnh "paper" ở ranh giới chương (preset vox);
- ghi chú sáng tạo: hook, CTA, chương còn thiếu, cảnh protect, nhịp cắt, trộn hệ chữ, âm thanh, hook trùng.
Ghi chú KHÔNG chặn render — in ra (dòng `~`) và ghi vào qa.json (`creative`)."""
from __future__ import annotations

from pathlib import Path

from vf.edl import Effect, Graphic, Variant, output_duration
from vf.tokens import load_tokens, preset

SFX_EXTS = (".wav", ".mp3", ".m4a", ".ogg")
SFX_NEAR_S = 0.15  # đã có sfx gần đó (ghi tay hoặc cue khác) thì không thêm
CTA_SOFT_FROM, CTA_LATE = 0.6, 0.85  # CTA mềm trong 60–85 % thời lượng, ngoài CTA cuối
CTA_WORDS = ("giỏ", "bấm", "mua", "đặt", "link", "xem ngay", "săn")
MAX_WORDS_PER_S = 3.5
MAX_TEXT_AT_ONCE = 2
CHAPTER_ALIASES = {"problem": "pain", "solution": "benefit"}
# graphic → khoá trong tokens.auto_sfx
SFX_KEY_FOR_GRAPHIC = {"callout": "circle", "collage": "paper", "counter": "day_counter", "light_timer": "light_timer",
                       "whiten": "tooth_morph", "end_card": "end_card", "wipe": "wipe", "shade": "shade",
                       "teeth": "teeth", "paper_swipe": "paper"}


def _timing() -> dict:
    return load_tokens()["timing"]


def piece_spans(v: Variant) -> list[tuple[float, float, object, str | None]]:
    """(đầu, cuối theo timeline output, đoạn, chương) cho hook + segments. Hook không ghi chương = "hook";
    đoạn không ghi chương = cùng chương với đoạn trước."""
    out, t, prev = [], 0.0, None
    for i, p in enumerate(v.pieces()):
        ch = p.chapter or ("hook" if i == 0 else prev)
        ch = CHAPTER_ALIASES.get(ch, ch)
        out.append((t, t + p.duration, p, ch))
        t += p.duration
        prev = ch
    return out


def chapter_cuts(v: Variant) -> list[float]:
    """Thời điểm (output) đổi chương — nơi preset đặt chuyển cảnh."""
    spans = piece_spans(v)
    return [a for (a, _, _, ch), (_, _, _, prev) in zip(spans[1:], spans) if ch != prev]


def hold_needed(text: str, sub: str = "") -> float:
    t = _timing()
    words = len((text + " " + sub).replace("*", " ").replace("[", " ").replace("]", " ").split())
    return max(t["min_hold_s"], t["hold_base_s"] + t["hold_per_word_s"] * words)


def auto_fix(v: Variant) -> tuple[Variant, list[str]]:
    """Kéo dài chữ hiện quá ngắn cho đủ đọc: max(1,2 s; 0,6 + 0,25 × số từ), không quá hết video."""
    total = output_duration(v)
    fixes, overlays = [], []
    for o in v.overlays:
        need = hold_needed(o.text, o.sub)
        if o.end - o.start < need - 1e-6:
            new_end = min(total, o.start + need)
            if new_end > o.end + 1e-6:
                fixes.append(f"tự sửa: giữ chữ \"{o.text}\" {o.end - o.start:.1f} → {new_end - o.start:.1f} s")
                o = o.model_copy(update={"end": round(new_end, 3)})
        overlays.append(o)
    return v.model_copy(update={"overlays": overlays}), fixes


def transition_graphics(v: Variant) -> list[Graphic]:
    """Chuyển cảnh vẽ bằng Remotion ở ranh giới chương: preset vox → tờ giấy lướt ngang (0,3 s).
    whip làm bằng ffmpeg (vf/render.py), cut = không gì."""
    if preset(v.preset).get("transition") != "paper":
        return []
    return [Graphic(kind="paper_swipe", start=max(0.0, t - 0.12), end=t + 0.18) for t in chapter_cuts(v)]


def find_sfx(sfx_dir: Path, name: str) -> str | None:
    """Đường dẫn tương đối với library/brand (render.resolve_asset tìm theo brand dir)."""
    for ext in SFX_EXTS:
        p = Path(sfx_dir) / f"{name}{ext}"
        if p.exists():
            return f"{Path(sfx_dir).name}/{p.name}"
    return None


def auto_sfx(v: Variant, sfx_dir: Path) -> list[Effect]:
    """SFX tự thêm theo sự kiện (tokens.auto_sfx). Tắt khi `v.sfx_auto = False` hoặc preset có auto_sfx false (ugc)."""
    if not v.sfx_auto or not preset(v.preset).get("auto_sfx", True) or not Path(sfx_dir).is_dir():
        return []
    names = load_tokens()["auto_sfx"]
    cues: list[tuple[float, str]] = []
    cues += [(e.at, names["zoom"]) for e in v.effects if e.kind in ("zoom_to", "zoom_punch")]
    cues += [(t, names["chapter"]) for t in chapter_cuts(v)]
    for g in v.graphics:
        if g.kind == "kinetic" and g.words:
            per = (g.end - g.start) / len(g.words)
            cues += [(g.start + k * per, names["kinetic_word"]) for k in range(len(g.words))]
        elif g.kind in SFX_KEY_FOR_GRAPHIC:
            cues.append((g.start, names[SFX_KEY_FOR_GRAPHIC[g.kind]]))
            if g.kind == "light_timer":
                cues += [(g.start + r.at, names["light_timer"]) for r in g.rows if r.at > 0]
    cues += [(o.start, names["text_in"]) for o in v.overlays]
    taken = [e.at for e in v.effects if e.kind == "sfx"]
    out: list[Effect] = []
    for at, name in sorted(cues):
        asset = find_sfx(sfx_dir, name)
        if asset is None or any(abs(at - t) < SFX_NEAR_S for t in taken):
            continue
        out.append(Effect(kind="sfx", at=round(at, 3), asset=asset))
        taken.append(at)
    return out


def _is_cta(text: str, style: str) -> bool:
    return style == "cta" or any(w in text.lower() for w in CTA_WORDS)


def lint_variant(v: Variant) -> list[str]:
    """Ghi chú sáng tạo (sau khi đã gộp cam kết tự động, bỏ chữ ngoài text_free và tự sửa)."""
    tm = _timing()
    notes: list[str] = []
    dur = output_duration(v)
    spans = piece_spans(v)

    # hook: phần tử chữ/đồ hoạ đầu tiên
    firsts = [o.start for o in v.overlays] + [g.start for g in v.graphics if g.kind != "paper_swipe"]
    if not firsts or min(firsts) > tm["first_element_by_s"] + 1e-6:
        notes.append(f"hook: chưa có chữ/đồ hoạ trong {tm['first_element_by_s']} s đầu "
                     "(bỏ qua nếu nguồn đã có chữ in sẵn ở hook)")

    # CTA: có CTA, có CTA mềm giữa video, có CTA trong mấy giây cuối
    ctas = [o.start for o in v.overlays if _is_cta(o.text, o.style)] + [g.start for g in v.graphics if g.kind == "end_card"]
    ends = [o.end for o in v.overlays if _is_cta(o.text, o.style)] + [g.end for g in v.graphics if g.kind == "end_card"]
    if not ctas:
        notes.append("CTA: chưa có thẻ CTA nào")
    else:
        if dur > 15 and not any(CTA_SOFT_FROM * dur <= t <= CTA_LATE * dur for t in ctas):
            notes.append(f"CTA: chỉ ở cuối — thêm một CTA mềm trong khoảng {CTA_SOFT_FROM * dur:.0f}–{CTA_LATE * dur:.0f} s")
        if not any(e >= dur - tm["end_cta_window_s"] for e in ends):
            notes.append(f"CTA: {tm['end_cta_window_s']:.0f} s cuối chưa có CTA/end_card")

    # đọc kịp, số khối chữ cùng lúc
    for o in v.overlays:
        words = len((o.text + " " + o.sub).split())
        if words / max(0.1, o.end - o.start) > MAX_WORDS_PER_S:
            notes.append(f"đọc không kịp: \"{o.text}\" {words} từ trong {o.end - o.start:.1f} s")
    for o in v.overlays:
        at_once = sum(1 for p in v.overlays if p.start <= o.start < p.end)
        if at_once > MAX_TEXT_AT_ONCE:
            notes.append(f"quá nhiều chữ cùng lúc ({at_once}) ở {o.start:.1f} s")
            break

    # nhịp cắt: cảnh ngắn, cảnh protect, cắt ngay sau khi chữ hiện
    for a, b, p, _ in spans:
        if not p.rapid and b - a < tm["scene_min_s"] - 1e-6:
            notes.append(f"nhịp: đoạn {a:.1f}–{b:.1f} s ngắn hơn {tm['scene_min_s']} s (ghi rapid nếu cố ý)")
        if p.protect and b - a < tm["protect_min_s"] - 1e-6:
            notes.append(f"cảnh protect {a:.1f}–{b:.1f} s ngắn hơn {tm['protect_min_s']} s — để cảnh gốc chạy trọn")
        if p.protect and any(o.position == "center" and o.start < b and a < o.end for o in v.overlays):
            notes.append(f"chữ giữa khung đè cảnh protect {a:.1f}–{b:.1f} s (miệng/răng) — dời lên trên/xuống dưới")
    cuts = [a for a, _, _, _ in spans[1:]]
    for o in v.overlays:
        if any(o.start < c < o.start + tm["no_cut_after_text_s"] for c in cuts):
            notes.append(f"cắt cảnh ngay sau khi chữ \"{o.text}\" hiện (< {tm['no_cut_after_text_s']} s)")
    events = sorted({0.0, dur, *cuts, *(e.at for e in v.effects if e.kind != "sfx"),
                     *(g.start for g in v.graphics), *(o.start for o in v.overlays)})
    protected = [(a, b) for a, b, p, _ in spans if p.protect]  # cảnh tiền được chạy trọn: miễn luật đổi nhịp
    gaps = [(a, b) for a, b in zip(events, events[1:]) if b - a > tm["pace_change_max_s"] + 1e-6
            and not any(pa - 1e-6 <= a and b <= pb + 1e-6 for pa, pb in protected)]
    if gaps:
        txt = ", ".join(f"{a:.1f}–{b:.1f} s" for a, b in gaps[:4])
        notes.append(f"nhịp: không đổi gì (cắt/zoom/đồ hoạ/chữ) quá {tm['pace_change_max_s']:.0f} s ở {txt}")

    # đủ ý: chương còn thiếu
    check = load_tokens()["content_checklist"]
    chapters = {"hook"} | {ch for _, _, p, ch in spans if p.chapter}  # đoạn mở đầu luôn là hook
    if not any(p.chapter for _, _, p, _ in spans):
        notes.append("đủ ý: chưa ghi `chapter` cho đoạn nào — không kiểm được nỗi đau/lợi ích/hiệu quả/bằng chứng/nhanh/tiết kiệm")
    else:
        missing = [check["labels"][c] for c in check["required"] if c not in chapters]
        if missing:
            notes.append(f"đủ ý: còn thiếu {', '.join(missing)}")

    # độ dài mặc định (brief có target thì CLI kiểm ±10%)
    if not v.cutdown_of and not (tm["length_min_s"] * (1 - tm["length_tolerance"]) <= dur
                                 <= tm["length_max_s"] * (1 + tm["length_tolerance"])):
        notes.append(f"độ dài {dur:.0f} s ngoài khoảng ưu tiên {tm['length_min_s']}–{tm['length_max_s']} s")

    # một hệ chữ theo preset
    name = v.preset or "pink"
    body = [o for o in v.overlays if not _is_cta(o.text, o.style)]  # thẻ CTA được dùng kiểu riêng
    mixed = {o.style for o in body if (o.style == "vox") != (name == "vox") and o.style in ("vox", "lower")}
    if name == "ugc":
        mixed |= {o.style for o in body if o.style in ("lower", "vox")}
    if mixed:
        notes.append(f"trộn hệ chữ: preset {name} nhưng có chữ kiểu {', '.join(sorted(mixed))}")

    if not v.music and not any(e.kind == "sfx" for e in v.effects):
        notes.append("âm thanh: không có nhạc nền và SFX (chạy `vf make-sfx` hoặc thêm file vào library/brand/sfx/)")
    return notes


def lint_batch(variants: list[Variant]) -> dict[str, list[str]]:
    """Biến thể render cùng lúc mà trùng đoạn hook → không phải phương án test khác nhau."""
    out: dict[str, list[str]] = {}
    for i, a in enumerate(variants):
        for b in variants[:i]:
            if a.hook.source != b.hook.source:
                continue
            inter = min(a.hook.end, b.hook.end) - max(a.hook.start, b.hook.start)
            if inter > 0.5 * min(a.hook.duration, b.hook.duration):
                out.setdefault(a.id, []).append(f"hook trùng với {b.id} — đổi câu/khung hình mở đầu")
    return out
