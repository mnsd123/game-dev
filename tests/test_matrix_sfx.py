import wave

from vf.matrix import expand
from vf.sfx import NAMES, make_sfx


def test_expand_matrix_shifts_local_times():
    edl = {"job": "lo-09", "variants": [], "matrix": {
        "presets": ["ugc", "pink"],
        "hooks": [{"id": "h1", "hook_type": "pain", "hook": {"source": "a.mp4", "start": 0, "end": 2},
                   "overlays": [{"text": "Răng vàng?", "start": 0.1, "end": 1.5}]}],
        "bodies": [{"id": "b1", "segments": [{"source": "a.mp4", "start": 10, "end": 20}],
                    "graphics": [{"kind": "shade", "start": 1, "end": 3}]}],
        "ctas": [{"id": "c1", "segments": [{"source": "a.mp4", "start": 40, "end": 44}],
                  "overlays": [{"text": "Bấm giỏ hàng", "start": 0.5, "end": 3.5, "style": "cta"}]}],
    }}
    vs = expand(edl)
    assert [v["id"] for v in vs] == ["lo-09_h1_b1_c1_ugc", "lo-09_h1_b1_c1_pink"]
    v = vs[0]
    assert v["graphics"][0]["start"] == 3.0  # body bắt đầu sau hook 2 s
    assert v["overlays"][-1]["start"] == 12.5  # cta bắt đầu ở 2 + 10


def test_make_sfx_creates_missing_only(tmp_path):
    (tmp_path / "pop.mp3").write_bytes(b"x")  # SFX có bản quyền người dùng bỏ vào: giữ nguyên
    made = make_sfx(tmp_path)
    assert len(made) == len(NAMES) - 1 and not (tmp_path / "pop.wav").exists()
    with wave.open(str(tmp_path / "whoosh.wav")) as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 2 and w.getnframes() / 48000 <= 0.6
