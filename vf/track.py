"""Dò vị trí hàm răng trong cảnh cận để zoom ống kính bám theo (Vox: khoanh đúng chỗ răng vàng)."""
from __future__ import annotations

from pathlib import Path

SMALL_W, SMALL_H = 270, 480


def teeth_center(frame) -> tuple[float, float] | None:
    """Tâm vùng răng (tỉ lệ khung): điểm ảnh sáng, ít bão hoà, sắc vàng–trắng, ở giữa khung theo chiều dọc."""
    import cv2
    import numpy as np

    small = cv2.resize(frame, (SMALL_W, SMALL_H))
    h, s, v = cv2.split(cv2.cvtColor(small, cv2.COLOR_BGR2HSV))
    m = ((v > 120) & (s < 140) & (h > 12) & (h < 40)).astype(np.uint8)
    m[: int(SMALL_H * 0.3)] = 0
    m[int(SMALL_H * 0.75):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, hh, area = st[k]
    if area < 400:
        return None
    return (x + w / 2) / SMALL_W, (y + hh / 2) / SMALL_H


def track_teeth(path: Path, start: float, end: float, step: float = 0.1) -> list[tuple[float, float, float]]:
    """[(giây tính từ start, cx, cy)], làm mượt trung bình trượt 3 điểm; khung không thấy răng thì giữ điểm trước."""
    import cv2

    cap = cv2.VideoCapture(str(path))
    raw: list[tuple[float, float, float]] = []
    t, last = start, (0.5, 0.5)
    try:
        while t <= end + 1e-6:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ok, frame = cap.read()
            c = teeth_center(frame) if ok else None
            last = c or last
            raw.append((round(t - start, 3), *last))
            t += step
    finally:
        cap.release()
    out = []
    for i, (rt, _, _) in enumerate(raw):
        win = raw[max(0, i - 1): i + 2]
        out.append((rt, round(sum(p[1] for p in win) / len(win), 3), round(sum(p[2] for p in win) / len(win), 3)))
    return out
