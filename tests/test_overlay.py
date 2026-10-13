import json
import os
import subprocess
from pathlib import Path

import pytest

from vf.edl import Segment, Variant, output_duration
from vf.motion import REMOTION_DIR, find_commitments, load_commitments, plan_overlays, render_overlay
from vf.probe import probe
from vf.render import build_ffmpeg_cmd, render_variant
from vf.transcribe import Word

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "library" / "brand"
needs_remotion = pytest.mark.skipif(not (REMOTION_DIR / "node_modules").exists(),
                                    reason="chưa cài remotion (cd remotion && npm i)")


def _w(text, start, end):
    return Word(text, start, end)


def test_commitments_file_has_three_result_claims():
    displays = {c.display for c in load_commitments()}
    assert {"Trắng sau 5–7 ngày", "Bật 3–4 tone", "Trắng như sứ"} <= displays


def test_find_spoken_range_commitment():
    words = [_w("dùng", 0.0, 0.3), _w("năm", 1.0, 1.2), _w("đến", 1.2, 1.4), _w("bảy", 1.4, 1.6),
             _w("ngày", 1.6, 1.9), _w("là", 2.0, 2.1), _w("trắng", 2.1, 2.4)]
    found = find_commitments(words, load_commitments(), total=10.0)
    assert len(found) == 1
    o = found[0]
    assert o.text == "Trắng sau 5–7 ngày" and o.style == "commit" and o.animation == "highlight"
    assert o.start == pytest.approx(0.9) and o.end >= 1.9 + 1.0


def test_find_three_commitments_and_none_in_plain_talk():
    words = [_w(t, i * 0.4, i * 0.4 + 0.35) for i, t in enumerate(
        "răng bật 3-4 tông trắng như răng sứ luôn".split())]
    texts = sorted(o.text for o in find_commitments(words, load_commitments(), total=20.0))
    assert texts == ["Bật 3–4 tone", "Trắng như sứ"]
    plain = [_w(t, i * 0.4, i * 0.4 + 0.3) for i, t in enumerate("mỗi lần 15 phút tại nhà".split())]
    assert find_commitments(plain, load_commitments(), total=5.0) == []


def test_plan_overlays_skips_commitment_already_covered():
    v = Variant(id="x", hook_type="pain", hook={"source": "a", "start": 0, "end": 2}, segments=[], rationale="r",
                overlays=[{"text": "Trắng như sứ", "start": 0.2, "end": 1.5, "style": "commit"}])
    words = {"a": [_w("như", 0.5, 0.7), _w("sứ", 0.7, 1.0)]}
    planned = plan_overlays(v, words)
    assert [o.text for o in planned] == ["Trắng như sứ"]


def test_captions_off_by_default():
    v = Variant(id="x", hook_type="pain", hook={"source": "a", "start": 0, "end": 1}, segments=[], rationale="r")
    assert v.captions is False


def test_ffmpeg_cmd_with_motion_overlay(sample_video, tmp_path):
    v = Variant(id="x", hook_type="pain", hook={"source": "a.mp4", "start": 1, "end": 2}, segments=[], rationale="r",
                overlays=[{"text": "Hook", "start": 0, "end": 1}])
    ov = tmp_path / "ov.mov"
    cmd = build_ffmpeg_cmd({"a.mp4": sample_video}, {"a.mp4": probe(sample_video)}, v, None, BRAND,
                           tmp_path / "o.mp4", gains={"a.mp4": 0.0}, overlay=ov)
    fc = cmd[cmd.index("-filter_complex") + 1]
    assert str(ov) in cmd and "overlay=0:0" in fc and "drawtext" not in fc


@needs_remotion
def test_render_overlay_has_alpha_and_duration(tmp_path):
    v = Variant(id="ov", hook_type="pain", hook={"source": "a", "start": 0, "end": 2.0},
                segments=[{"source": "a", "start": 3, "end": 4.5}], rationale="r",
                overlays=[{"text": "Cười mà phải che miệng?", "start": 0, "end": 1.5, "animation": "word_by_word"},
                          {"text": "Trắng sau 5–7 ngày", "start": 2.0, "end": 3.4, "style": "commit",
                           "animation": "highlight"}])
    out = render_overlay(v, ROOT / "library/style-guide.md", tmp_path / "ov.mov", overlays=v.overlays)
    s = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams",
                                   "-show_format", "-print_format", "json", str(out)],
                                  capture_output=True, text=True, check=True).stdout)
    assert s["streams"][0]["pix_fmt"].startswith("yuva")
    assert abs(float(s["format"]["duration"]) - output_duration(v)) <= 0.1


@needs_remotion
def test_render_variant_with_motion(sample_video, tmp_path):
    v = Variant(id="m", hook_type="result_first", hook={"source": "a.mp4", "start": 1.0, "end": 2.5},
                segments=[{"source": "a.mp4", "start": 4.0, "end": 4.9}], rationale="r",
                overlays=[{"text": "15 phút tại nhà", "start": 0.0, "end": 1.4, "animation": "pop"}])
    words = {"a.mp4": [_w("trắng", 1.2, 1.5), _w("như", 1.5, 1.7), _w("sứ", 1.7, 2.0)]}
    out = render_variant({"a.mp4": sample_video}, {"a.mp4": probe(sample_video)}, v, tmp_path / "m.mp4",
                         words_by_source=words, brand=BRAND, work_dir=tmp_path / "w", motion=True)
    info = probe(out)
    assert (info.width, info.height) == (1080, 1920)
    assert abs(info.duration - output_duration(v)) <= 0.15
    props = json.loads((tmp_path / "w" / "m_overlay.json").read_text(encoding="utf-8"))
    assert any(o["text"] == "Trắng như sứ" for o in props["overlays"])
