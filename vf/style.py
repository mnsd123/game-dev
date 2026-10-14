"""Đo nhịp dựng và lấy khung hình của video tham khảo."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from vf.ffutil import ffprobe_duration, run

_PTS = re.compile(r"pts_time:\s*([\d.]+)")


@dataclass
class ShotStats:
    duration: float
    n_cuts: int
    avg_shot_s: float
    cuts: list[float] = field(default_factory=list)  # thời điểm cắt cảnh (s)


def shot_stats(path: Path, threshold: float = 0.3) -> ShotStats:
    duration = ffprobe_duration(path)
    proc = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:v:0",
                "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    cuts = [round(float(m.group(1)), 3) for line in proc.stderr.splitlines()
            if "Parsed_showinfo" in line and (m := _PTS.search(line))]
    return ShotStats(round(duration, 3), len(cuts), round(duration / (len(cuts) + 1), 3), cuts)


def reference_frames(path: Path, out_dir: Path, every_s: float = 1.0) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.jpg"):
        old.unlink()
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf", f"fps=1/{every_s},scale=540:-2",
         "-q:v", "3", str(out_dir / "frame_%04d.jpg")])
    return sorted(out_dir.glob("frame_*.jpg"))
