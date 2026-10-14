import json
import shutil
import subprocess
from pathlib import Path

import pytest

from vf.probe import MediaInfo, normalize, probe
from vf.silence import Range, detect_silences, keep_ranges
from vf.transcribe import Word, transcribe
from vf.analyze import analyze_all


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def _close(a, b, tol=0.1):
    return abs(a - b) <= tol


@pytest.fixture(scope="module")
def hevc_rotated_vfr(tmp_path_factory) -> Path:
    """HEVC 720x1280 có cờ xoay 90° và khung hình biến thiên (giống file .mov iPhone)."""
    d = tmp_path_factory.mktemp("hevc")
    raw = d / "raw.mov"
    _ff("-f", "lavfi", "-i", "testsrc2=s=720x1280:r=60:d=2",
        "-f", "lavfi", "-i", "sine=f=300:d=2",
        "-vf", "select='not(mod(n\\,3))+lt(t\\,1)',setpts=N/(40*TB)",  # bỏ khung không đều → VFR
        "-fps_mode", "vfr", "-c:v", "libx265", "-x265-params", "log-level=error",
        "-tag:v", "hvc1", "-c:a", "aac", str(raw))
    out = d / "rotated.mov"
    _ff("-display_rotation", "90", "-i", str(raw), "-c", "copy", str(out))
    return out


@pytest.fixture(scope="module")
def silent_video(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("noaudio") / "broll.mp4"
    _ff("-f", "lavfi", "-i", "color=c=white:s=720x1280:r=30:d=2", "-c:v", "libx264", str(out))
    return out


def test_probe_sample(sample_video):
    info = probe(sample_video)
    assert isinstance(info, MediaInfo)
    assert _close(info.duration, 5.0)
    assert (info.width, info.height) == (720, 1280)
    assert info.fps == 30
    assert info.has_audio is True
    assert info.codec == "h264"


def test_detect_silences(sample_video):
    s = detect_silences(sample_video)
    assert len(s) == 2
    assert _close(s[0].start, 0) and _close(s[0].end, 1)
    assert _close(s[1].start, 3) and _close(s[1].end, 4)


def test_keep_ranges():
    k = keep_ranges(5.0, [Range(0, 1), Range(3, 4)])
    assert [(round(r.start, 2), round(r.end, 2)) for r in k] == [(0.92, 3.08), (3.92, 5.0)]


def test_keep_ranges_trailing_silence():
    k = keep_ranges(5.0, [Range(4.0, 5.0)])
    assert [(round(r.start, 2), round(r.end, 2)) for r in k] == [(0.0, 4.08)]


def test_normalize_hevc_rotated_vfr(hevc_rotated_vfr, tmp_path):
    src_info = probe(hevc_rotated_vfr)
    assert src_info.codec == "hevc"
    out = normalize(hevc_rotated_vfr, tmp_path / "n.mp4")
    info = probe(out)
    assert info.codec == "h264"
    assert info.fps == 30
    # xoay 90° đã áp vào hình: 720x1280 → 1280x720, không còn cờ xoay
    assert (info.width, info.height) == (1280, 720)
    meta = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-select_streams", "v:0", str(out)],
        capture_output=True, text=True, check=True).stdout)
    s = meta["streams"][0]
    assert s["r_frame_rate"] == s["avg_frame_rate"] == "30/1"
    assert not any("rotation" in sd for sd in s.get("side_data_list", []))


def test_no_audio_returns_empty(silent_video):
    assert probe(silent_video).has_audio is False
    assert detect_silences(silent_video) == []
    assert transcribe(silent_video) == []


def test_normalize_no_audio(silent_video, tmp_path):
    out = normalize(silent_video, tmp_path / "n.mp4")
    info = probe(out)
    assert info.has_audio is False and info.codec == "h264"


def test_analyze_all_two_sources(sample_video, sample_video_b, tmp_path):
    src = tmp_path / "source gốc"
    src.mkdir()
    shutil.copy(sample_video, src / "a.mp4")
    shutil.copy(sample_video_b, src / "b roll.mp4")
    (src / "ghi chú.txt").write_text("không phải video", encoding="utf-8")
    work = tmp_path / "work"
    infos = analyze_all(src, work, transcriber=lambda p: [Word("xin", 0.1, 0.3)])
    assert set(infos) == {"a.mp4", "b roll.mp4"}
    for name in ("a.mp4", "b roll.mp4"):
        d = work / name
        for name in ("normalized.mp4", "transcript.json", "silences.json", "keep.json"):
            assert (d / name).exists(), d / name
    keep = json.loads((work / "a.mp4" / "keep.json").read_text(encoding="utf-8"))
    assert len(keep) == 2
    words = json.loads((work / "a.mp4" / "transcript.json").read_text(encoding="utf-8"))
    assert words == [{"text": "xin", "start": 0.1, "end": 0.3}]
    # nguồn không bị đụng tới
    assert (src / "a.mp4").stat().st_size == sample_video.stat().st_size


@pytest.mark.slow
def test_transcribe_real(sample_video):
    words = transcribe(sample_video)
    assert isinstance(words, list)


def test_same_stem_sources_kept_apart(sample_video, sample_video_b, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    shutil.copy(sample_video, src / "clip.mp4")
    shutil.copy(sample_video_b, src / "clip.mov")
    infos = analyze_all(src, tmp_path / "work", transcriber=lambda p: [])
    assert (infos["clip.mp4"].width, infos["clip.mov"].width) == (720, 1920)


def test_skipped_transcription_is_redone_later(sample_video, tmp_path):
    from vf.analyze import analyze_source, load_words
    src = tmp_path / "a.mp4"
    shutil.copy(sample_video, src)
    analyze_source(src, tmp_path / "work", transcriber=None)
    assert load_words(tmp_path / "work", "a.mp4") == []
    analyze_source(src, tmp_path / "work", transcriber=lambda p: [Word("xin", 0.1, 0.3)])
    assert load_words(tmp_path / "work", "a.mp4") == [Word("xin", 0.1, 0.3)]


def test_truncated_normalized_file_is_redone(sample_video, tmp_path):
    """normalize bị ngắt giữa chừng để lại file hỏng mới hơn nguồn → lần sau phải làm lại, không dùng file hỏng."""
    from vf.analyze import analyze_source
    src = tmp_path / "a.mp4"
    shutil.copy(sample_video, src)
    d = tmp_path / "work" / "a.mp4"
    d.mkdir(parents=True)
    (d / "normalized.mp4").write_bytes(b"\x00" * 1000)
    info = analyze_source(src, tmp_path / "work", transcriber=None)
    assert abs(info.duration - 5.0) <= 0.1
