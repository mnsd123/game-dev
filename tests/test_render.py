import json
import subprocess
from pathlib import Path

import pytest

from vf.edl import Variant, output_duration
from vf.probe import probe
from vf.qa import measure_lufs
from vf.render import build_ffmpeg_cmd, render_variant
from vf.transcribe import Word

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "library" / "brand"
STYLE = ROOT / "templates" / "caption_style.ass"


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def _variant(**kw):
    base = dict(
        id="v-test", hook_type="pain",
        hook={"source": "a.mp4", "start": 1.0, "end": 2.5},
        segments=[{"source": "b.mp4", "start": 0.0, "end": 2.0}, {"source": "a.mp4", "start": 4.0, "end": 4.9}],
        overlays=[{"text": "Răng ố vàng: cười, che miệng?", "start": 0.0, "end": 1.5, "position": "top"}],
        effects=[{"kind": "zoom_punch", "at": 0.0, "duration": 0.3}, {"kind": "flash", "at": 1.5, "duration": 0.1}],
        rationale="test",
    )
    base.update(kw)
    return Variant(**base)


@pytest.fixture(scope="module")
def two_sources(sample_video, sample_video_b):
    sources = {"a.mp4": sample_video, "b.mp4": sample_video_b}
    return sources, {k: probe(p) for k, p in sources.items()}


def test_render_two_sources_vertical_output(two_sources, tmp_path):
    sources, infos = two_sources
    v = _variant()
    words = {"a.mp4": [Word("Răng", 1.1, 1.4), Word("trắng", 1.5, 1.9)], "b.mp4": [Word("sáng", 0.2, 0.6)]}
    out = render_variant(sources, infos, v, tmp_path / "v.mp4", words_by_source=words,
                         brand=BRAND, style_path=STYLE, work_dir=tmp_path / "work")
    info = probe(out)
    assert (info.width, info.height) == (1080, 1920)
    assert info.fps == 30
    assert abs(info.duration - output_duration(v)) <= 0.15
    s = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams",
                                   "-print_format", "json", str(out)], capture_output=True, text=True).stdout)["streams"][0]
    assert s.get("sample_aspect_ratio", "1:1") == "1:1"
    assert s.get("display_aspect_ratio", "9:16") == "9:16"


def test_no_subtitles_when_captions_off(two_sources, tmp_path):
    sources, infos = two_sources
    ass = tmp_path / "c.ass"
    ass.write_text("x", encoding="utf-8")
    cmd = build_ffmpeg_cmd(sources, infos, _variant(captions=False), ass, BRAND, tmp_path / "o.mp4",
                           gains={"a.mp4": 0.0, "b.mp4": 0.0})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "subtitles=" not in fc


def test_no_subtitles_when_transcript_empty(two_sources, tmp_path):
    sources, infos = two_sources
    work = tmp_path / "work"
    render_variant(sources, infos, _variant(), tmp_path / "o.mp4", words_by_source={},
                   brand=BRAND, style_path=STYLE, work_dir=work)
    assert not list(work.glob("*.ass"))


def test_landscape_source_not_distorted(two_sources, tmp_path):
    """Nguồn ngang: hình giữa giữ tỉ lệ 16:9 → ở giữa khung có dải 1080x608, trên/dưới là nền blur."""
    sources, infos = two_sources
    v = _variant(hook={"source": "b.mp4", "start": 0.0, "end": 1.0}, segments=[{"source": "b.mp4", "start": 1.0, "end": 2.0}],
                 overlays=[], effects=[])
    cmd = build_ffmpeg_cmd(sources, infos, v, None, BRAND, tmp_path / "o.mp4", gains={"a.mp4": 0.0, "b.mp4": 0.0})
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert "force_original_aspect_ratio=decrease" in fc and "boxblur" in fc


@pytest.fixture(scope="module")
def loud_and_quiet(tmp_path_factory):
    d = tmp_path_factory.mktemp("lvl")
    loud, quiet = d / "loud.mp4", d / "quiet.mp4"
    for path, vol in ((loud, "0dB"), (quiet, "-10dB")):
        _ff("-f", "lavfi", "-i", "color=c=gray:s=720x1280:r=30:d=4",
            "-f", "lavfi", "-i", "sine=f=500:r=48000:d=4", "-af", f"volume={vol}",
            "-ac", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path))
    return {"loud.mp4": loud, "quiet.mp4": quiet}


def _lufs_slice(path, start, dur, tmp):
    piece = tmp / f"slice_{start}.wav"
    _ff("-ss", str(start), "-t", str(dur), "-i", str(path), "-vn", str(piece))
    return measure_lufs(piece)


def test_loudness_matched_across_sources(loud_and_quiet, tmp_path):
    infos = {k: probe(p) for k, p in loud_and_quiet.items()}
    v = Variant(id="lvl", hook_type="x", hook={"source": "loud.mp4", "start": 0.5, "end": 3.0},
                segments=[{"source": "quiet.mp4", "start": 0.5, "end": 3.5}], captions=False, rationale="t")
    out = render_variant(loud_and_quiet, infos, v, tmp_path / "o.mp4", brand=BRAND, style_path=STYLE,
                         work_dir=tmp_path / "w")
    first = _lufs_slice(out, 0.3, 2.0, tmp_path)
    second = _lufs_slice(out, 3.0, 2.3, tmp_path)
    assert abs(first - second) <= 2.0, (first, second)


def test_broll_without_speech_not_boosted_to_voice_level(loud_and_quiet):
    from vf.render import source_gains
    infos = {k: probe(p) for k, p in loud_and_quiet.items()}
    g = source_gains(loud_and_quiet, infos, set(infos), speech={"loud.mp4"})
    lq = measure_lufs(loud_and_quiet["quiet.mp4"])
    ll = measure_lufs(loud_and_quiet["loud.mp4"])
    assert g["loud.mp4"] == pytest.approx(-16 - ll, abs=0.01)
    assert g["quiet.mp4"] == pytest.approx(min(0.0, -26 - lq), abs=0.01)


def _gray_frame(path, t, w=108, h=192):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(path), "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return raw, w, h


def test_zoom_punch_stays_centered(tmp_path):
    src = tmp_path / "dot.mp4"
    # nền trắng, ô đen 200x200 ở chính giữa khung 1080x1920
    _ff("-f", "lavfi", "-i", "color=c=white:s=1080x1920:r=30:d=2", "-f", "lavfi", "-i", "sine=d=2",
        "-vf", "drawbox=x=440:y=860:w=200:h=200:color=black:t=fill",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(src))
    v = Variant(id="z", hook_type="x", hook={"source": "d.mp4", "start": 0, "end": 2}, segments=[],
                effects=[{"kind": "zoom_punch", "at": 0.0, "duration": 2.0}], captions=False, rationale="t")
    out = render_variant({"d.mp4": src}, {"d.mp4": probe(src)}, v, tmp_path / "o.mp4", brand=BRAND,
                         style_path=STYLE, work_dir=tmp_path / "w")
    raw, w, h = _gray_frame(out, 1.8)
    pts = [(i % w, i // w) for i, b in enumerate(raw) if b < 100]
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    assert abs(cx - w / 2) <= 2 and abs(cy - h / 2) <= 2, (cx, cy)
