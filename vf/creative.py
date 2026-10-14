"""Phần "chất" của quảng cáo TikTok có thể kiểm bằng máy: tự gắn SFX theo hiệu ứng, và các ghi chú sáng tạo
(hook có chữ sớm, CTA trước đoạn cuối, tốc độ đọc, có âm thanh dựng, hook không trùng trong một lần render).
Ghi chú sáng tạo KHÔNG chặn render — chỉ in ra và ghi vào qa.json (`creative`)."""
from __future__ import annotations

from pathlib import Path

from vf.edl import Effect, Variant, output_duration

SFX_EXTS = (".wav", ".mp3", ".m4a", ".ogg")
# hiệu ứng / graphic / kiểu chữ → tên file SFX trong library/brand/sfx/ (thiếu file thì bỏ qua)
SFX_FOR_EFFECT = {"zoom_to": "whoosh", "zoom_punch": "whoosh"}
SFX_FOR_GRAPHIC = {"callout": "marker", "collage": "paper", "counter": "tick", "wipe": "swipe", "shade": "tick",
                   "teeth": "shimmer", "whiten": "shimmer"}
SFX_FOR_STYLE = {"tag": "pop", "cta": "pop", "commit": "pop"}
SFX_NEAR_S = 0.15  # đã có sfx gần đó (ghi tay) thì không thêm

HOOK_TEXT_BY_S = 0.5
CTA_SOFT_FROM, CTA_LATE = 0.6, 0.85  # CTA nên xuất hiện trong 60–85 % thời lượng, không chỉ ở cuối
CTA_WORDS = ("giỏ", "bấm", "mua", "đặt", "link", "xem ngay", "săn")
MAX_WORDS_PER_S = 3.5
MAX_TEXT_AT_ONCE = 2


def find_sfx(sfx_dir: Path, name: str) -> str | None:
    """Đường dẫn tương đối với library/brand (render.resolve_asset tìm theo brand dir)."""
    for ext in SFX_EXTS:
        p = Path(sfx_dir) / f"{name}{ext}"
        if p.exists():
            return f"{Path(sfx_dir).name}/{p.name}"
    return None


def auto_sfx(v: Variant, sfx_dir: Path) -> list[Effect]:
    """SFX tự thêm khớp từng hiệu ứng/graphic/thẻ chữ (style guide mục 7). `v.sfx_auto = False` để tắt."""
    if not v.sfx_auto or not Path(sfx_dir).is_dir():
        return []
    cues: list[tuple[float, str]] = []
    cues += [(e.at, SFX_FOR_EFFECT[e.kind]) for e in v.effects if e.kind in SFX_FOR_EFFECT]
    cues += [(g.start, SFX_FOR_GRAPHIC[g.kind]) for g in v.graphics if g.kind in SFX_FOR_GRAPHIC]
    cues += [(o.start, SFX_FOR_STYLE[o.style]) for o in v.overlays if o.style in SFX_FOR_STYLE]
    taken = [e.at for e in v.effects if e.kind == "sfx"]
    out: list[Effect] = []
    for at, name in sorted(cues):
        asset = find_sfx(sfx_dir, name)
        if asset is None or any(abs(at - t) < SFX_NEAR_S for t in taken):
            continue
        out.append(Effect(kind="sfx", at=at, asset=asset))
        taken.append(at)
    return out


def _is_cta(text: str, style: str) -> bool:
    return style == "cta" or any(w in text.lower() for w in CTA_WORDS)


def lint_variant(v: Variant) -> list[str]:
    """Ghi chú sáng tạo cho một biến thể (theo overlay sau khi đã gộp cam kết tự động)."""
    notes: list[str] = []
    dur = output_duration(v)
    if not any(o.start <= HOOK_TEXT_BY_S for o in v.overlays):
        notes.append(f"hook: chưa có chữ nào trong {HOOK_TEXT_BY_S} s đầu (bỏ qua nếu nguồn đã có chữ in sẵn ở hook)")
    ctas = [o.start for o in v.overlays if _is_cta(o.text, o.style)]
    if not ctas:
        notes.append("CTA: chưa có thẻ CTA nào")
    elif dur > 15 and not any(CTA_SOFT_FROM * dur <= t <= CTA_LATE * dur for t in ctas):
        notes.append(f"CTA: chỉ ở cuối — thêm một CTA mềm trong khoảng {CTA_SOFT_FROM * dur:.0f}–{CTA_LATE * dur:.0f} s")
    for o in v.overlays:
        words = len((o.text + " " + o.sub).split())
        if words / max(0.1, o.end - o.start) > MAX_WORDS_PER_S:
            notes.append(f"đọc không kịp: \"{o.text}\" {words} từ trong {o.end - o.start:.1f} s")
    for o in v.overlays:
        at_once = sum(1 for p in v.overlays if p.start <= o.start < p.end)
        if at_once > MAX_TEXT_AT_ONCE:
            notes.append(f"quá nhiều chữ cùng lúc ({at_once}) ở {o.start:.1f} s")
            break
    if not v.music and not any(e.kind == "sfx" for e in v.effects):
        notes.append("âm thanh: không có nhạc nền và SFX (thêm file vào library/brand/sfx/ hoặc gắn nhạc CML trên TikTok)")
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
