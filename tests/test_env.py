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
