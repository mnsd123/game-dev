"""QA tự động: đo loudness, kiểm tra output, chặn claim cấm, contact sheet."""
from __future__ import annotations

import math
import re
import subprocess
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from vf.ffutil import ffprobe_json, run

_I = re.compile(r"I:\s+(-?[\d.]+|-inf)\s+LUFS")


def measure_lufs(path: Path) -> float:
    """Loudness tích hợp (EBU R128). File không có tiếng → -inf."""
    if not any(s["codec_type"] == "audio" for s in ffprobe_json(path)["streams"]):
        return -math.inf
    proc = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
                "-af", "ebur128", "-f", "null", "-"])
    found = _I.findall(proc.stderr)
    if not found:
        raise RuntimeError(f"Không đọc được loudness của {path}")
    return float(found[-1])


# ---------------------------------------------------------------- claim check

class ClaimViolation(Exception):
    """Chữ hiển thị chứa cụm cấm hoặc claim chưa có bằng chứng."""


_ZERO_WIDTH = re.compile(r"[\u200b-\u200d\u2060\ufeff]")
_NUM_WORDS = {
    "một": 1, "mot": 1, "hai": 2, "ba": 3, "bốn": 4, "bon": 4, "năm": 5, "nam": 5, "sáu": 6, "sau": 6,
    "bảy": 7, "bay": 7, "tám": 8, "tam": 8, "chín": 9, "chin": 9, "mười": 10, "muoi": 10,
}
_NUM = r"(\d+|" + "|".join(sorted(_NUM_WORDS, key=len, reverse=True)) + r")"
_DECIMAL = re.compile(r"(?<!\w)" + _NUM + r"\s*(?:[.,]|chấm|phẩy|cham|phay)\s*" + _NUM + r"(?!\w)")
_RANGE = re.compile(r"(?<!\w)" + _NUM + r"\s*(?:-|đến|tới|den|toi)\s*" + _NUM + r"(?!\w)")


def _num(token: str) -> str:
    return str(_NUM_WORDS.get(token, token))


def _norm(text: str) -> str:
    """Chuẩn hoá để so khớp: thường hoá, gộp khoảng trắng, '5 - 7'/'5 đến 7'/'năm đến bảy' → '5-7',
    '4,8'/'bốn chấm tám' → '4.8', '100 %' → '100%', gạch nối giữa chữ ('điều-trị') → khoảng trắng, bỏ ký tự vô hình."""
    text = unicodedata.normalize("NFC", text).casefold()
    text = _ZERO_WIDTH.sub(" ", text)
    text = re.sub(r"[‐-―−]", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = _DECIMAL.sub(lambda m: f"{_num(m.group(1))}.{_num(m.group(2))}", text)
    text = _RANGE.sub(lambda m: f"{_num(m.group(1))}-{_num(m.group(2))}", text)
    text = re.sub(r"(?<!\d)-|-(?!\d)", " ", text)
    text = re.sub(r"\s+%", "%", text)
    return re.sub(r"\s+", " ", text).strip()


def _base_char(c: str) -> str:
    if c == "đ":
        return "d"
    return unicodedata.normalize("NFD", c)[0]


def _strip(text: str) -> str:
    """Bỏ dấu, giữ nguyên độ dài (mỗi ký tự NFC → một ký tự gốc)."""
    return "".join(_base_char(c) for c in text)


def _pattern(phrase: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")


def check_claims(texts: list[str], forbidden: list[str]) -> list[str]:
    """Trả về các cụm bị vi phạm. Không phân biệt hoa thường / dấu cách thừa.
    Viết không dấu ("dieu tri") cũng bị bắt, nhưng chữ có dấu khác ("chưa") không bị nhầm với "chữa"."""
    joined = [_norm(t) for t in texts if t]
    hits: list[str] = []
    for phrase in forbidden:
        p = _norm(phrase)
        if not p:
            continue
        exact = _pattern(p)
        loose = _pattern(_strip(p))
        for t in joined:
            if exact.search(t) or any(
                all(ord(c) < 128 for c in t[m.start():m.end()]) for m in loose.finditer(_strip(t))
            ):
                hits.append(phrase)
                break
    return hits


# ---------------------------------------------------------------- output QA

TARGET_LUFS = -14.0
LUFS_TOL = 1.0
DURATION_TOL_S = 0.2


@dataclass
class QAReport:
    path: Path
    duration_ok: bool
    size_ok: bool
    loudness_lufs: float
    loudness_ok: bool
    claim_violations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["path"] = str(self.path)
        d["loudness_lufs"] = None if math.isinf(self.loudness_lufs) else round(self.loudness_lufs, 2)
        return d


def check_output(path: Path, expected: float, size: tuple[int, int] = (1080, 1920)) -> QAReport:
    from vf.probe import probe

    info = probe(path)
    notes: list[str] = []
    duration_ok = abs(info.duration - expected) <= DURATION_TOL_S
    if not duration_ok:
        notes.append(f"Thời lượng {info.duration:.2f} s, mong đợi {expected:.2f} s")
    size_ok = (info.width, info.height) == tuple(size)
    if not size_ok:
        notes.append(f"Kích thước {info.width}x{info.height}, mong đợi {size[0]}x{size[1]}")
    lufs = measure_lufs(path)
    loudness_ok = abs(lufs - TARGET_LUFS) <= LUFS_TOL
    if not loudness_ok:
        notes.append(f"Loudness {lufs:.1f} LUFS, mong đợi {TARGET_LUFS} ±{LUFS_TOL} LUFS")
    return QAReport(Path(path), duration_ok, size_ok, lufs, loudness_ok, [], notes)


def contact_sheet(path: Path, out_png: Path, cols: int = 6, rows: int = 3, thumb_w: int = 180) -> Path:
    """Ảnh tổng quan: cols x rows khung hình rải đều theo thời lượng; viền đỏ = vùng an toàn TikTok."""
    from vf.probe import probe

    dur = max(probe(path).duration, 0.1)
    n = cols * rows
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf",
         f"fps={n / dur:.5f},{contact_sheet_filter()},scale={thumb_w}:-2,tile={cols}x{rows}", "-frames:v", "1", str(out_png)])
    return out_png


# ---------------------------------------------------------------- vùng an toàn

SAFE_CHECK_FPS = 4
SAFE_GRID = (108, 192)  # khung 1080x1920 thu nhỏ 10 lần
SAFE_ALPHA = 217  # ~85 %: chữ, thẻ, hình đặc; vầng sáng/bóng mờ (< 85 %) được phép tràn mép
SAFE_MIN_CELLS = 3  # bỏ qua nhiễu vài ô


def _unsafe_regions(safe) -> dict[str, list[tuple[int, int, int, int]]]:
    """Các vùng cấm trên lưới thu nhỏ: (x0, y0, x1, y1) theo ô."""
    gw, gh = SAFE_GRID
    sx, sy = gw / 1080, gh / 1920
    top, bot = round(safe.top * sy), round((1920 - safe.bottom) * sy)
    side = round(safe.side * sx)
    rail_x, rail_y = round((1080 - safe.rail_w) * sx), round(safe.rail_top * sy)
    return {
        "trên": [(0, 0, gw, top)],
        "dưới": [(0, bot, gw, gh)],
        "trái": [(0, top, side, bot)],
        "phải": [(gw - side, top, gw, rail_y)],
        "phải (cột nút)": [(rail_x, rail_y, gw, bot)],
    }


def check_safe_zone(overlay: Path, skip: list[tuple[float, float]] | None = None, safe=None) -> list[str]:
    """Đọc kênh alpha của lớp chữ/hình (video nền trong suốt) và báo các khoảng thời gian có chữ/hình đặc
    nằm ngoài vùng an toàn. `skip`: khoảng thời gian của thẻ toàn màn hình (nền phủ kín, tự bố cục)."""
    import numpy as np

    from vf.safezone import SAFE

    safe = safe or SAFE
    gw, gh = SAFE_GRID
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(overlay), "-vf",
         f"fps={SAFE_CHECK_FPS},alphaextract,scale={gw}:{gh}:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True,
    )
    if proc.returncode != 0:
        return [f"vùng an toàn: không đọc được kênh alpha của {Path(overlay).name}"]
    frames = np.frombuffer(proc.stdout, dtype=np.uint8)
    frames = frames[: len(frames) // (gw * gh) * gw * gh].reshape(-1, gh, gw)
    regions = _unsafe_regions(safe)
    hits: list[tuple[float, str]] = []
    for k, fr in enumerate(frames):
        t = k / SAFE_CHECK_FPS
        if any(a <= t <= b for a, b in (skip or [])):
            continue
        solid = fr >= SAFE_ALPHA
        for name, boxes in regions.items():
            if sum(int(solid[y0:y1, x0:x1].sum()) for x0, y0, x1, y1 in boxes) >= SAFE_MIN_CELLS:
                hits.append((t, name))
    # gộp thành khoảng liên tục theo vùng
    notes = []
    for name in regions:
        ts = [t for t, n in hits if n == name]
        if not ts:
            continue
        spans, a, b = [], ts[0], ts[0]
        for t in ts[1:]:
            if t - b > 1.5 / SAFE_CHECK_FPS:
                spans.append((a, b))
                a = t
            b = t
        spans.append((a, b))
        txt = ", ".join(f"{a:.1f}–{b + 1 / SAFE_CHECK_FPS:.1f} s" for a, b in spans)
        notes.append(f"vùng an toàn: chữ/hình lấn vùng {name} lúc {txt}")
    return notes


def contact_sheet_filter(safe=None) -> str:
    """Kẻ viền đỏ quanh vùng an toàn trên ảnh tổng quan: chữ/hình nằm ngoài viền là bị giao diện TikTok che."""
    from vf.safezone import SAFE

    s = safe or SAFE
    c = "red@0.9:t=6"
    upper_h = (s.rail_top - s.top) / 1920
    lower_h = (1920 - s.bottom - s.rail_top) / 1920
    return ",".join([
        f"drawbox=x=iw*{s.side / 1080:.4f}:y=ih*{s.top / 1920:.4f}:w=iw*{1 - 2 * s.side / 1080:.4f}:h=ih*{upper_h:.4f}:color={c}",
        f"drawbox=x=iw*{s.side / 1080:.4f}:y=ih*{s.rail_top / 1920:.4f}:w=iw*{1 - (s.side + s.rail_w) / 1080:.4f}"
        f":h=ih*{lower_h:.4f}:color={c}",
    ])


def timeline_sheet(video: Path, out_dir: Path, every: float = 0.5, cols: int = 8, rows: int = 6,
                   thumb_w: int = 216) -> list[Path]:
    """Ảnh tổng quan có mốc giờ (giờ nguồn) mỗi `every` giây, viền đỏ vùng an toàn; nhiều trang nếu video dài.
    Dùng khi phân tích nguồn: tìm khoảng có chữ in sẵn (text_free), cảnh tiền (protect), toạ độ răng."""
    from vf.probe import probe
    from vf.render import _filter_path, find_font
    from vf.paths import BRAND_DIR

    dur = probe(video).duration
    per_page = cols * rows
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    font = _filter_path(find_font(BRAND_DIR))
    pages = []
    page_s = per_page * every
    k = 0
    while k * page_s < dur:
        out = out_dir / f"{Path(video).stem}_sheet_{k + 1:03d}.png"
        start = k * page_s
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{page_s:.3f}", "-i", str(video), "-vf",
             f"setpts=PTS-STARTPTS+{start:.3f}/TB,fps=1/{every},{contact_sheet_filter()},"
             f"drawtext=fontfile={font}:text='%{{pts\\:hms}}':x=12:y=12:fontsize=64:fontcolor=white:"
             f"box=1:boxcolor=black@0.65:boxborderw=8,scale={thumb_w}:-2,tile={cols}x{rows}",
             "-frames:v", "1", str(out)])
        pages.append(out)
        k += 1
    return pages
