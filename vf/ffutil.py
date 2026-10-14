"""Hàm tiện ích gọi ffmpeg/ffprobe."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Chạy lệnh, raise RuntimeError kèm stderr nếu lỗi."""
    # UTF-8 cố định: Windows mặc định cp1252 sẽ lỗi với tên file có dấu ("source gốc")
    proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"Lệnh lỗi ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return proc


def ffprobe_json(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]).stdout
    return json.loads(out)


def ffprobe_duration(path: Path) -> float:
    return float(ffprobe_json(path)["format"]["duration"])
