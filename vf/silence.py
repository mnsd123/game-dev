"""Tìm khoảng lặng bằng ffmpeg silencedetect."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from vf.ffutil import ffprobe_json, run


@dataclass(frozen=True)
class Range:
    start: float
    end: float


_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_END = re.compile(r"silence_end:\s*(-?[\d.]+)")


def detect_silences(path: Path, noise_db: float = -35, min_dur: float = 0.4) -> list[Range]:
    data = ffprobe_json(path)
    if not any(s["codec_type"] == "audio" for s in data["streams"]):
        return []
    duration = float(data["format"]["duration"])
    proc = run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
        "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-",
    ])
    out: list[Range] = []
    start: float | None = None
    for line in proc.stderr.splitlines():
        if m := _START.search(line):
            start = max(0.0, float(m.group(1)))
        elif (m := _END.search(line)) and start is not None:
            out.append(Range(start, min(duration, float(m.group(1)))))
            start = None
    if start is not None:  # im lặng kéo tới hết file
        out.append(Range(start, duration))
    return out


def keep_ranges(duration: float, silences: list[Range], pad: float = 0.08) -> list[Range]:
    """Phần bù của khoảng lặng, chừa đệm `pad` mỗi bên (đệm lấn vào khoảng lặng)."""
    keep: list[Range] = []
    cursor = 0.0
    for s in sorted(silences, key=lambda r: r.start):
        end = min(duration, s.start + pad) if s.start > 0 else 0.0
        if end > cursor:
            keep.append(Range(round(cursor, 3), round(end, 3)))
        cursor = max(cursor, s.end - pad if s.end < duration else duration)
    if cursor < duration:
        keep.append(Range(round(cursor, 3), round(duration, 3)))
    return [r for r in keep if r.end - r.start > 1e-3]
