import json
from pathlib import Path

import pytest

from vf.edl import EDL, Segment, Variant, load_edl, output_duration
from vf.probe import MediaInfo

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "templates" / "edl.example.json"

INFOS = {
    "nguon_a.mp4": MediaInfo(5.0, 720, 1280, 30, True, "h264"),
    "nguon_b.mp4": MediaInfo(3.0, 1920, 1080, 30, True, "h264"),
}


def _variant(**kw):
    base = dict(id="v1", hook_type="pain", hook={"source": "nguon_a.mp4", "start": 1.0, "end": 2.5},
                segments=[{"source": "nguon_b.mp4", "start": 0.0, "end": 2.0}], rationale="r")
    base.update(kw)
    return base


def _write(tmp_path, variants):
    p = tmp_path / "edl.json"
    p.write_text(json.dumps({"job": "lo-test", "variants": variants}, ensure_ascii=False), encoding="utf-8")
    return p


def test_example_loads_with_two_sources():
    edl = load_edl(EXAMPLE, INFOS)
    assert isinstance(edl, EDL)
    used = {s.source for v in edl.variants for s in [v.hook, *v.segments]}
    assert used == set(INFOS)
    assert len({v.hook_type for v in edl.variants}) == len(edl.variants)


def test_segment_past_its_own_source_duration(tmp_path):
    # 4.0 s hợp lệ với nguồn A (5 s) nhưng vượt nguồn B (3 s)
    p = _write(tmp_path, [_variant(id="bien-the-2", segments=[
        {"source": "nguon_a.mp4", "start": 3.0, "end": 4.0},
        {"source": "nguon_b.mp4", "start": 2.0, "end": 4.0}])])
    with pytest.raises(ValueError) as e:
        load_edl(p, INFOS)
    msg = str(e.value)
    assert "bien-the-2" in msg and "segments[1]" in msg and "nguon_b.mp4" in msg


def test_unknown_source(tmp_path):
    p = _write(tmp_path, [_variant(segments=[{"source": "khong_co.mov", "start": 0, "end": 1}])])
    with pytest.raises(ValueError, match="khong_co.mov"):
        load_edl(p, INFOS)


def test_start_not_before_end(tmp_path):
    p = _write(tmp_path, [_variant(id="v9", segments=[{"source": "nguon_a.mp4", "start": 2, "end": 2}])])
    with pytest.raises(ValueError, match="v9"):
        load_edl(p, INFOS)


def test_hook_longer_than_3s(tmp_path):
    p = _write(tmp_path, [_variant(id="v3", hook={"source": "nguon_a.mp4", "start": 0, "end": 3.5})])
    with pytest.raises(ValueError, match="v3"):
        load_edl(p, INFOS)


def test_output_duration():
    v = Variant(**_variant(segments=[{"source": "nguon_b.mp4", "start": 0.0, "end": 2.0},
                                     {"source": "nguon_a.mp4", "start": 3.0, "end": 3.5}]))
    assert output_duration(v) == pytest.approx(1.5 + 2.0 + 0.5)
