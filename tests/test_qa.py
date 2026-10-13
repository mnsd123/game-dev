import subprocess
from pathlib import Path

import pytest

from vf.edl import Variant
from vf.probe import probe
from vf.qa import ClaimViolation, QAReport, check_claims, check_output, contact_sheet, measure_lufs
from vf.render import render_variant
from vf.transcribe import Word

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [l for l in (ROOT / "library/forbidden.txt").read_text(encoding="utf-8").splitlines() if l]


def _make(path: Path, vol_db: float, size="1080x1920", d=4):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=s={size}:r=30:d={d}",
                    "-f", "lavfi", "-i", f"sine=f=500:r=48000:d={d}",
                    "-af", f"loudnorm=I={vol_db}:TP=-1.5:LRA=11,aresample=48000", "-ac", "2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(path)], check=True)
    return path


def test_valid_output_all_ok(tmp_path):
    r = check_output(_make(tmp_path / "ok.mp4", -14), expected=4.0)
    assert isinstance(r, QAReport)
    assert r.duration_ok and r.size_ok and r.loudness_ok, r.notes
    assert abs(r.loudness_lufs + 14) <= 1


def test_quiet_output_flagged(tmp_path):
    r = check_output(_make(tmp_path / "quiet.mp4", -30), expected=4.0)
    assert r.loudness_ok is False
    assert any("LUFS" in n for n in r.notes)


def test_wrong_size_and_duration_flagged(tmp_path):
    r = check_output(_make(tmp_path / "wide.mp4", -14, size="1920x1080"), expected=6.0)
    assert r.size_ok is False and r.duration_ok is False


def test_check_claims_case_and_spaces():
    assert check_claims(["Trắng THẦN  KỲ"], ["thần kỳ"]) == ["thần kỳ"]


def test_check_claims_allows_tone_vs_forbidden():
    assert check_claims(["Trắng 3–4 tone"], FORBIDDEN) == []


def test_check_claims_unaccented_bypass_caught():
    assert check_claims(["Gel dieu tri rang"], ["điều trị"]) == ["điều trị"]


def test_check_claims_no_false_hit_on_other_accents():
    # "chưa" (chưa thử) không phải "chữa"
    assert check_claims(["Bạn chưa thử à?"], ["chữa"]) == []


def test_check_claims_whole_word_only():
    assert check_claims(["Hướng đảm bảo"], ["bảo"]) == ["bảo"]
    assert check_claims(["baoquat"], ["bao"]) == []


def test_contact_sheet(tmp_path):
    png = contact_sheet(_make(tmp_path / "v.mp4", -14), tmp_path / "sheet.png", cols=6)
    assert png.exists()
    info = probe(png)
    assert info.width == 6 * 180


def test_render_blocked_by_overlay_claim(sample_video, tmp_path):
    srcs = {"a.mp4": sample_video}
    v = Variant(id="bad", hook_type="x", hook={"source": "a.mp4", "start": 1.0, "end": 2.0}, segments=[],
                overlays=[{"text": "Trắng THẦN KỲ", "start": 0, "end": 1}], rationale="t")
    out = tmp_path / "bad.mp4"
    with pytest.raises(ClaimViolation) as e:
        render_variant(srcs, {"a.mp4": probe(sample_video)}, v, out, forbidden=["thần kỳ"])
    assert "bad" in str(e.value) and "thần kỳ" in str(e.value)
    assert not out.exists()


def test_render_blocked_by_caption_claim(sample_video, tmp_path):
    srcs = {"a.mp4": sample_video}
    v = Variant(id="cap", hook_type="x", hook={"source": "a.mp4", "start": 1.0, "end": 2.5}, segments=[], rationale="t")
    words = {"a.mp4": [Word("trắng", 1.1, 1.4), Word("như", 1.5, 1.7), Word("sứ", 1.8, 2.0)]}
    with pytest.raises(ClaimViolation, match="như sứ"):
        render_variant(srcs, {"a.mp4": probe(sample_video)}, v, tmp_path / "c.mp4",
                       words_by_source=words, forbidden=["như sứ"])
