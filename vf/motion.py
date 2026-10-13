"""Lớp chữ động: tự highlight cam kết khi người nói nói ra, render overlay trong suốt bằng Remotion."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vf.edl import TextOverlay, Variant, output_duration
from vf.paths import BRAND_DIR, LIBRARY, ROOT
from vf.qa import _norm, _pattern, _strip
from vf.transcribe import Word

REMOTION_DIR = ROOT / "remotion"
COMMITMENTS_PATH = LIBRARY / "commitments.txt"
MAX_WINDOW_WORDS = 7
LEAD_S = 0.1  # hiện chữ sớm hơn lời nói một chút
MIN_SHOW_S = 1.8
HOLD_AFTER_S = 1.0
MIN_VISIBLE_S = 0.6


@dataclass(frozen=True)
class Commitment:
    phrase: str
    display: str
    emphasis: str = ""


def load_commitments(path: Path = COMMITMENTS_PATH) -> list[Commitment]:
    out = []
    if not Path(path).exists():
        return out
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        parts = [x.strip() for x in line.split("|")]
        out.append(Commitment(parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return out


def _matches(text: str, phrase: str) -> bool:
    t, p = _norm(text), _norm(phrase)
    return bool(_pattern(p).search(t) or _pattern(_strip(p)).search(_strip(t)))


def find_commitments(words: list[Word], commitments: list[Commitment], total: float) -> list[TextOverlay]:
    """Tìm cam kết trong lời nói (đã ở timeline output) → overlay highlight. Mỗi chữ hiển thị lấy một lần
    cho mỗi lần được nói; nếu hai cụm cùng chữ hiển thị trùng thời gian thì chỉ giữ một."""
    found: list[TextOverlay] = []
    i = 0
    while i < len(words):
        hit = None
        for j in range(i + 1, min(len(words), i + MAX_WINDOW_WORDS) + 1):
            window = " ".join(w.text for w in words[i:j])
            for c in commitments:
                if _matches(window, c.phrase):
                    hit = (j, c)
                    break
            if hit:
                break
        if not hit:
            i += 1
            continue
        j, c = hit
        # thu hẹp mép trái: bỏ từ đầu cửa sổ nếu vẫn khớp (để chữ hiện đúng lúc nói)
        k = i
        while k + 1 < j and _matches(" ".join(w.text for w in words[k + 1:j]), c.phrase):
            k += 1
        start = max(0.0, words[k].start - LEAD_S)
        end = min(total, max(words[j - 1].end + HOLD_AFTER_S, start + MIN_SHOW_S))
        if not any(o.text == c.display and o.start < end and start < o.end for o in found):
            found.append(TextOverlay(text=c.display, start=round(start, 3), end=round(end, 3),
                                     position="center", style="commit", animation="highlight",
                                     emphasis=[c.emphasis] if c.emphasis else []))
        i = j
    return found


def plan_overlays(v: Variant, words_by_source: dict[str, list[Word]]) -> list[TextOverlay]:
    """Overlay của edl + cam kết tự phát hiện (bỏ cái đã được edl phủ cùng chữ, cùng thời gian)."""
    from vf.captions import remap_words

    words = remap_words(words_by_source or {}, v.pieces())
    auto = find_commitments(words, load_commitments(), output_duration(v))
    planned = list(v.overlays)
    for o in auto:
        if not any(p.text == o.text and p.start < o.end and o.start < p.end for p in planned):
            planned.append(o)
    return _no_overlap(sorted(planned, key=lambda o: o.start))


def _no_overlap(overlays: list[TextOverlay]) -> list[TextOverlay]:
    """Hai chữ cùng vị trí không hiện chồng nhau: chữ trước kết thúc khi chữ sau bắt đầu."""
    out: list[TextOverlay] = []
    last_at: dict[str, int] = {}
    for o in overlays:
        k = last_at.get(o.position)
        if k is not None and out[k].end > o.start:
            prev = out[k]
            if o.start - prev.start >= MIN_VISIBLE_S:
                out[k] = prev.model_copy(update={"end": o.start})
            else:  # chữ trước quá ngắn nếu cắt → lùi chữ sau
                o = o.model_copy(update={"start": prev.end})
                if o.end - o.start < MIN_VISIBLE_S:
                    continue
        last_at[o.position] = len(out)
        out.append(o)
    return out


def remotion_available() -> bool:
    return (REMOTION_DIR / "node_modules" / "remotion").exists() and shutil.which("npx") is not None


def _brand_props(brand: Path) -> dict:
    props: dict = {}
    cfg = Path(brand) / "brand.json"
    if cfg.exists():
        props.update(json.loads(cfg.read_text(encoding="utf-8")))
    fonts = sorted(p for p in Path(brand).glob("*") if p.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"))
    if fonts:
        dst = REMOTION_DIR / "public" / f"brand-font{fonts[0].suffix.lower()}"
        if not dst.exists() or dst.stat().st_mtime < fonts[0].stat().st_mtime:
            shutil.copy(fonts[0], dst)
        props["fontFile"] = dst.name
    return props


def render_overlay(
    v: Variant,
    style_guide: Path,
    out: Path,
    *,
    overlays: list[TextOverlay] | None = None,
    brand: Path = BRAND_DIR,
    props_path: Path | None = None,
) -> Path:
    """Video nền trong suốt (ProRes 4444, yuva444p10le), 1080x1920, 30 fps, dài đúng output_duration(v).
    `style_guide` để dành cho tham số phong cách; màu/font lấy từ library/brand/brand.json và file font."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ovs = v.overlays if overlays is None else overlays
    props = {
        "durationInFrames": max(1, round(output_duration(v) * 30)),
        "overlays": [o.model_dump() for o in ovs],
        **_brand_props(brand),
    }
    props_path = Path(props_path) if props_path else out.with_suffix(".json")
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    npx = shutil.which("npx")
    if npx is None or not remotion_available():
        raise RuntimeError("Chưa cài Remotion: chạy `cd remotion && npm install` (cần Node 20+)")
    partial = out.with_name(out.stem + ".partial" + out.suffix)
    cmd = [npx, "remotion", "render", "src/index.ts", "Overlay", str(partial.resolve()),
           f"--props={props_path.resolve()}", "--codec=prores", "--prores-profile=4444",
           "--pixel-format=yuva444p10le", "--image-format=png", "--log=error"]
    browser = os.environ.get("VF_BROWSER_EXECUTABLE")
    if browser:
        cmd.append(f"--browser-executable={browser}")
    proc = subprocess.run(cmd, cwd=REMOTION_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"Remotion render lỗi:\n{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}")
    partial.replace(out)
    return out
