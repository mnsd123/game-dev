"""QA tự động: đo loudness, kiểm tra output, chặn claim cấm, contact sheet."""
from __future__ import annotations

import math
import re
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
_RANGE = re.compile(r"(?<!\w)" + _NUM + r"\s*(?:-|đến|tới|den|toi)\s*" + _NUM + r"(?!\w)")


def _num(token: str) -> str:
    return str(_NUM_WORDS.get(token, token))


def _norm(text: str) -> str:
    """Chuẩn hoá để so khớp: thường hoá, gộp khoảng trắng, '5 - 7'/'5 đến 7'/'năm đến bảy' → '5-7',
    '100 %' → '100%', gạch nối giữa chữ ('điều-trị') → khoảng trắng, bỏ ký tự vô hình."""
    text = unicodedata.normalize("NFC", text).casefold()
    text = _ZERO_WIDTH.sub(" ", text)
    text = re.sub(r"[‐-―−]", "-", text)
    text = re.sub(r"\s+", " ", text)
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
    """Ảnh tổng quan: cols x rows khung hình rải đều theo thời lượng."""
    from vf.probe import probe

    dur = max(probe(path).duration, 0.1)
    n = cols * rows
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf",
         f"fps={n / dur:.5f},scale={thumb_w}:-2,tile={cols}x{rows}", "-frames:v", "1", str(out_png)])
    return out_png
