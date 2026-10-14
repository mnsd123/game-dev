"""Chọn vị trí dọc cho chữ/hiệu ứng: không che mặt (OpenCV Haar), tránh vùng nhiều chi tiết (sản phẩm, tay),
không đè lên chữ khác cùng lúc, chừa vùng giao diện TikTok ở đáy."""
from __future__ import annotations

import math
from pathlib import Path

from vf.edl import Graphic, Segment, TextOverlay
from vf.scenes import PieceVideo

FRAME_H = 1920
# cỡ chữ + đệm dọc (px) — khớp với remotion/src/Overlay.tsx
FONT_PX = {"hook": 80, "commit": 72, "label": 54, "cta": 58, "plain": 60}
PAD_PX = {"hook": 18, "commit": 22, "label": 16, "cta": 20, "plain": 14}
MAX_TEXT_W = 900
GRAPHIC_H_PX = {"light": 150, "whiten": 520}
GRAPHIC_W_PX = {"light": 640, "whiten": 520}
TOP_MIN, BOTTOM_MAX = 0.06, 0.80  # dưới 80 %: nút/caption của TikTok
PREFERRED = {"top": 0.10, "center": 0.42, "bottom": 0.66}
FACE_WEIGHT, BUSY_WEIGHT, PREF_WEIGHT, COLLIDE_WEIGHT = 6.0, 1.0, 0.25, 10.0
SMALL_W, SMALL_H = 270, 480


def text_box(o: TextOverlay) -> tuple[float, float]:
    """(rộng, cao) ước lượng theo tỉ lệ khung."""
    fs = FONT_PX[o.style]
    per_line = max(1, int(MAX_TEXT_W / (fs * 0.62)))
    lines = 0
    for_line = 0
    for w in o.text.split():
        if for_line and for_line + 1 + len(w) > per_line:
            lines += 1
            for_line = len(w)
        else:
            for_line += (1 if for_line else 0) + len(w)
    lines += 1
    longest = min(len(o.text), per_line)
    w = min(1000, longest * fs * 0.62 + 2 * 36)
    return w / 1080, (lines * fs * 1.18 + 2 * PAD_PX[o.style]) / FRAME_H


def graphic_box(g: Graphic) -> tuple[float, float]:
    return GRAPHIC_W_PX[g.kind] / 1080, GRAPHIC_H_PX[g.kind] / FRAME_H


def source_time(pieces: list[Segment], videos: list[PieceVideo], t: float) -> tuple[str, float]:
    """Giờ output → (nguồn, giờ nguồn của khung hình THẬT đang hiện), tính cả phần giữ khung."""
    acc = 0.0
    for p, pv in zip(pieces, videos):
        if t < acc + p.duration or p is pieces[-1]:
            rel = min(max(t - acc, pv.head), p.duration - pv.tail - 1e-3)
            return p.source, p.start + max(0.0, rel)
        acc += p.duration
    raise ValueError(t)


class _Frames:
    def __init__(self, sources: dict[str, Path]):
        import cv2

        self.cv2 = cv2
        self.sources = sources
        self.caps: dict[str, object] = {}
        self.front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.profile = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
        self.cache: dict[tuple[str, int], tuple] = {}

    def analyse(self, source: str, t: float):
        """→ (mặt: list[(x0,y0,x1,y1)] theo tỉ lệ, mật độ cạnh theo hàng/cột: ma trận nhỏ)."""
        key = (source, int(t * 10))
        if key in self.cache:
            return self.cache[key]
        cv2 = self.cv2
        cap = self.caps.get(source)
        if cap is None:
            cap = self.caps[source] = cv2.VideoCapture(str(self.sources[source]))
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            self.cache[key] = ([], None)
            return self.cache[key]
        gray = cv2.cvtColor(cv2.resize(frame, (SMALL_W, SMALL_H)), cv2.COLOR_BGR2GRAY)
        faces = []
        for casc, flip in ((self.front, False), (self.profile, False), (self.profile, True)):
            img = cv2.flip(gray, 1) if flip else gray
            for (x, y, w, h) in casc.detectMultiScale(img, 1.1, 5, minSize=(28, 28)):
                if flip:
                    x = SMALL_W - x - w
                # nới hộp mặt: tóc, cằm, miệng đang ngậm khay
                x0, y0 = (x - 0.2 * w) / SMALL_W, (y - 0.35 * h) / SMALL_H
                x1, y1 = (x + 1.2 * w) / SMALL_W, (y + 1.45 * h) / SMALL_H
                faces.append((max(0, x0), max(0, y0), min(1, x1), min(1, y1)))
        edges = cv2.GaussianBlur(cv2.Canny(gray, 80, 160), (9, 9), 0).astype("float32") / 255.0
        self.cache[key] = (faces, edges)
        return self.cache[key]

    def close(self):
        for c in self.caps.values():
            c.release()


def _overlap(a: tuple, b: tuple) -> float:
    """Diện tích giao / diện tích a."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    return w * h / max(1e-6, (a[2] - a[0]) * (a[3] - a[1]))


def _score(box, frames_data, pref: float | None, placed: list[tuple], ) -> float:
    s = 0.0
    for faces, edges in frames_data:
        s += FACE_WEIGHT * sum(_overlap(box, f) for f in faces)
        if edges is not None:
            y0, y1 = int(box[1] * SMALL_H), max(int(box[1] * SMALL_H) + 1, int(box[3] * SMALL_H))
            x0, x1 = int(box[0] * SMALL_W), max(int(box[0] * SMALL_W) + 1, int(box[2] * SMALL_W))
            s += BUSY_WEIGHT * float(edges[y0:y1, x0:x1].mean()) * 4
    s /= max(1, len(frames_data))
    if pref is not None:
        s += PREF_WEIGHT * abs(box[1] - pref)
    s += COLLIDE_WEIGHT * sum(_overlap(box, p) for p in placed)
    return s


def best_y(frames_data, w: float, h: float, pref: float | None, placed: list[tuple]) -> float:
    x0 = (1 - w) / 2
    best, best_s = TOP_MIN, math.inf
    y = TOP_MIN
    while y + h <= BOTTOM_MAX + 1e-6:
        box = (x0, y, x0 + w, y + h)
        s = _score(box, frames_data, pref, placed)
        if s < best_s - 1e-9:
            best, best_s = y, s
        y += 0.02
    return round(best, 3)


def place(
    pieces: list[Segment],
    videos: list[PieceVideo],
    sources: dict[str, Path],
    overlays: list[TextOverlay],
    graphics: list[Graphic],
) -> tuple[list[TextOverlay], list[Graphic]]:
    """Đặt `y` cho mọi chữ/hiệu ứng chưa có y. Hiệu ứng đặt trước (to hơn), chữ tránh hiệu ứng đang hiện."""
    frames = _Frames(sources)
    placed: list[tuple[float, float, tuple]] = []  # (start, end, box)

    def sample(start: float, end: float):
        ts = [start + 0.15, (start + end) / 2, max(start + 0.15, end - 0.15)]
        return [frames.analyse(*source_time(pieces, videos, t)) for t in ts]

    def busy(start, end):
        return [b for (s, e, b) in placed if s < end and start < e]

    try:
        out_g = []
        for g in graphics:
            w, h = graphic_box(g)
            y = g.y if g.y is not None else best_y(sample(g.start, g.end), w, h, None, busy(g.start, g.end))
            placed.append((g.start, g.end, ((1 - w) / 2, y, (1 + w) / 2, y + h)))
            out_g.append(g.model_copy(update={"y": y}))
        out_o = []
        for o in overlays:
            w, h = text_box(o)
            pref = PREFERRED[o.position]
            y = o.y if o.y is not None else best_y(sample(o.start, o.end), w, h, pref, busy(o.start, o.end))
            placed.append((o.start, o.end, ((1 - w) / 2, y, (1 + w) / 2, y + h)))
            out_o.append(o.model_copy(update={"y": y}))
        return out_o, out_g
    finally:
        frames.close()
