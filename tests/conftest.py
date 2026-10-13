"""Fixture video tổng hợp bằng ffmpeg lavfi, dùng chung cho mọi test."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory) -> Path:
    """5 s, 720x1280, 30 fps. Hình: đỏ → trắng ở 1.7 s → xanh dương ở 3.4 s (độ sáng chênh lớn để dò cắt cảnh).
    Tiếng: 1 s im lặng, 2 s tone 440 Hz, 1 s im lặng, 1 s tone 440 Hz."""
    out = tmp_path_factory.mktemp("media") / "sample_a.mp4"
    _ffmpeg(
        "-f", "lavfi", "-i", "color=c=red:s=720x1280:r=30:d=1.7",
        "-f", "lavfi", "-i", "color=c=white:s=720x1280:r=30:d=1.7",
        "-f", "lavfi", "-i", "color=c=blue:s=720x1280:r=30:d=1.6",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=1",
        "-f", "lavfi", "-i", "sine=f=440:r=48000:d=2",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=1",
        "-f", "lavfi", "-i", "sine=f=440:r=48000:d=1",
        "-filter_complex",
        "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v];"
        "[4:a]aformat=channel_layouts=stereo[a4];[6:a]aformat=channel_layouts=stereo[a6];"
        "[3:a][a4][5:a][a6]concat=n=4:v=0:a=1[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        str(out),
    )
    return out


@pytest.fixture(scope="session")
def sample_video_b(tmp_path_factory) -> Path:
    """3 s, 1920x1080 (ngang), 30 fps, tone 880 Hz liên tục."""
    out = tmp_path_factory.mktemp("media") / "sample_b.mp4"
    _ffmpeg(
        "-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30:d=3",
        "-f", "lavfi", "-i", "sine=f=880:r=48000:d=3",
        "-map", "0:v", "-map", "1:a", "-ac", "2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        str(out),
    )
    return out
