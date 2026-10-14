"""SFX tạm tự tổng hợp bằng numpy (48 kHz, stereo, ≤ 0,6 s) cho auto_sfx: pop, whoosh, click, ding, marker,
slam, paper, tick, swipe, shimmer. Đủ để video có nhịp âm thanh; nên thay bằng SFX có bản quyền cùng tên."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 48000
NAMES = ("pop", "whoosh", "click", "ding", "marker", "slam", "paper", "tick", "swipe", "shimmer")


def _t(dur: float) -> np.ndarray:
    return np.arange(int(SR * dur)) / SR


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / max(decay, 1e-4))


def _noise(n: int, rng: np.random.Generator, smooth: int = 1) -> np.ndarray:
    x = rng.standard_normal(n)
    if smooth > 1:  # lọc thông thấp đơn giản: trung bình trượt
        x = np.convolve(x, np.ones(smooth) / smooth, mode="same")
    return x / (np.abs(x).max() + 1e-9)


def synth(name: str, seed: int = 7) -> np.ndarray:
    """Mono float trong [-1, 1]."""
    rng = np.random.default_rng(seed)
    if name == "pop":
        t = _t(0.09)
        f = np.linspace(900, 260, t.size)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(t.size, 0.002, 0.03)
    if name in ("whoosh", "swipe"):
        dur = 0.38 if name == "whoosh" else 0.26
        t = _t(dur)
        x = _noise(t.size, rng, smooth=12 if name == "whoosh" else 5)
        shape = np.sin(np.pi * t / dur) ** 2
        return x * shape * 0.9
    if name == "click":
        t = _t(0.03)
        return (0.6 * _noise(t.size, rng) + np.sin(2 * np.pi * 2200 * t)) * _env(t.size, 0.0005, 0.006) * 0.8
    if name == "tick":
        t = _t(0.025)
        return np.sin(2 * np.pi * 3200 * t) * _env(t.size, 0.0005, 0.005)
    if name == "ding":
        t = _t(0.6)
        return (np.sin(2 * np.pi * 1320 * t) + 0.4 * np.sin(2 * np.pi * 2640 * t)) / 1.4 * _env(t.size, 0.003, 0.22)
    if name == "marker":
        t = _t(0.32)
        x = _noise(t.size, rng, smooth=3) * (0.6 + 0.4 * np.sin(2 * np.pi * 18 * t))
        return x * np.sin(np.pi * t / 0.32) * 0.7
    if name == "slam":
        t = _t(0.3)
        f = np.linspace(110, 45, t.size)
        thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(t.size, 0.002, 0.09)
        return 0.85 * thump + 0.35 * _noise(t.size, rng, smooth=4) * _env(t.size, 0.001, 0.03)
    if name == "paper":
        t = _t(0.36)
        bursts = np.zeros(t.size)
        for k in rng.integers(0, t.size - 2000, 9):
            bursts[k:k + 2000] += _env(2000, 0.001, 0.008)
        return _noise(t.size, rng, smooth=2) * np.clip(bursts, 0, 1) * 0.8
    if name == "shimmer":
        t = _t(0.55)
        x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (2637, 3136, 3520, 4186))
        return x / 4 * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t)) * _env(t.size, 0.02, 0.25)
    raise ValueError(f"không có SFX tên {name}")


def write_wav(path: Path, mono: np.ndarray, peak_db: float = -3.0) -> None:
    x = mono / (np.abs(mono).max() + 1e-9) * 10 ** (peak_db / 20)
    fade = min(240, x.size // 4)  # chống tiếng tách ở mép
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    pcm = (np.stack([x, x], axis=1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def make_sfx(out_dir: Path, force: bool = False) -> list[Path]:
    """Tạo các file còn thiếu (không ghi đè SFX có bản quyền bạn đã bỏ vào, trừ khi force)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for name in NAMES:
        existing = [p for p in out_dir.glob(f"{name}.*")]
        if existing and not force:
            continue
        p = out_dir / f"{name}.wav"
        write_wav(p, synth(name))
        made.append(p)
    return made
