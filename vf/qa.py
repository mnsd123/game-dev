"""QA tự động: đo loudness."""
from __future__ import annotations

import math
import re
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
