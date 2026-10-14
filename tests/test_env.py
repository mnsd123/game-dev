import re
import subprocess

from vf.ffutil import ffprobe_duration


def test_ffmpeg_available():
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True).stdout
    major = int(re.search(r"ffmpeg version n?(\d+)", out).group(1))
    assert major >= 6


def test_sample_video_fixture(sample_video):
    assert abs(ffprobe_duration(sample_video) - 5.0) <= 0.1


def test_sample_video_b_fixture(sample_video_b):
    assert abs(ffprobe_duration(sample_video_b) - 3.0) <= 0.1


def test_run_decodes_output_as_utf8(monkeypatch):
    """Windows mặc định cp1252: output ffmpeg có 'source gốc' phải đọc bằng UTF-8, không được lỗi."""
    import vf.ffutil as ffutil
    seen = {}
    real = subprocess.run

    def spy(cmd, **kw):
        seen.update(kw)
        return real(cmd, **kw)

    monkeypatch.setattr(ffutil.subprocess, "run", spy)
    ffutil.run(["ffmpeg", "-version"])
    assert seen.get("encoding") == "utf-8" and seen.get("errors") == "replace"
