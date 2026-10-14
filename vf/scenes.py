"""Điểm chuyển cảnh trong nguồn (đã dựng sẵn) → tránh mẩu cảnh vài khung hình ở mép đoạn và cắt nhảy trong cùng cảnh."""
from __future__ import annotations

import bisect
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vf.edl import Segment

SCENE_THRESHOLD = 10.0  # scdet (0–100); nguồn TikTok đã dựng: 10 bắt được cắt cứng, bỏ qua chuyển động tay/máy
MIN_SHOT_S = 0.5  # mẩu cảnh ngắn hơn thế ở mép đoạn = "vấp hình"
JUMP_ZOOM = 1.12  # cắt nhảy trong cùng cảnh: phóng to xen kẽ để cú cắt có chủ ý

_TIME = re.compile(r"lavfi\.scd\.time:\s*([0-9.]+)")


def detect_cuts(path: Path, threshold: float = SCENE_THRESHOLD) -> list[float]:
    """Thời điểm (s) bắt đầu cảnh mới, tăng dần."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-an", "-vf", f"scale=270:-2,scdet=threshold={threshold}",
         "-f", "null", "-"],
        capture_output=True, encoding="utf-8", errors="replace",
    )
    return sorted({round(float(m), 3) for m in _TIME.findall(proc.stderr)})


@dataclass(frozen=True)
class PieceVideo:
    """Cách lấy hình cho một đoạn (giờ tương đối trong đoạn). Tiếng luôn lấy đủ [0, duration].
    Hình lấy [head, duration - tail]; phần head/tail giữ khung hình kề bên (không lộ mẩu cảnh khác)."""
    head: float = 0.0
    tail: float = 0.0
    zoom: float = 1.0


def shot_id(cuts: list[float], t: float) -> int:
    return bisect.bisect_right(cuts, t)


def plan_piece_video(pieces: list[Segment], cuts_by_source: dict[str, list[float]]) -> list[PieceVideo]:
    out: list[PieceVideo] = []
    prev_zoom = 1.0
    for i, p in enumerate(pieces):
        cuts = cuts_by_source.get(p.source, [])
        inner = [c for c in cuts if p.start < c < p.end]
        head = tail = 0.0
        if inner and inner[0] - p.start < MIN_SHOT_S and p.end - inner[0] > MIN_SHOT_S:
            head = inner[0] - p.start
        if inner and p.end - inner[-1] < MIN_SHOT_S and inner[-1] - p.start > MIN_SHOT_S:
            tail = p.end - inner[-1]
        zoom = 1.0
        prev = pieces[i - 1] if i > 0 else None
        if prev and prev.source == p.source and abs(p.start - prev.end) > 0.05:  # liền mạch thì không phải cắt
            prev_last = shot_id(cuts, prev.end - out[-1].tail - 1e-3)
            first = shot_id(cuts, p.start + head + 1e-3)
            if prev_last == first:  # cắt nhảy trong cùng cảnh
                zoom = 1.0 if prev_zoom != 1.0 else JUMP_ZOOM
        prev_zoom = zoom
        out.append(PieceVideo(round(head, 3), round(tail, 3), zoom))
    return out


def micro_shots(pieces: list[Segment], cuts_by_source: dict[str, list[float]]) -> list[str]:
    """Cảnh báo cho QA: mẩu cảnh ngắn ở mép đoạn (sẽ được giữ khung hình kề bên)."""
    notes = []
    for i, (p, pv) in enumerate(zip(pieces, plan_piece_video(pieces, cuts_by_source))):
        if pv.head:
            notes.append(f"đoạn {i}: mẩu cảnh {pv.head:.2f} s ở đầu ({p.start:.2f} s nguồn) → giữ khung cảnh sau")
        if pv.tail:
            notes.append(f"đoạn {i}: mẩu cảnh {pv.tail:.2f} s ở cuối ({p.end:.2f} s nguồn) → giữ khung cảnh trước")
    return notes
