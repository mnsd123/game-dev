from pathlib import Path

import pytest
from pydantic import ValidationError

from vf.brief import Brief, load_brief

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "brief.yaml"
FORBIDDEN = ROOT / "library" / "forbidden.txt"
PENDING = ROOT / "library" / "claims_pending.txt"

BASE = dict(platform="tiktok", target_seconds=30, goal="awareness", message="m", cta="c")


def test_template_loads():
    b = load_brief(TEMPLATE, FORBIDDEN)
    assert isinstance(b, Brief)
    assert b.aspect == "9:16"


def test_variants_zero_rejected():
    with pytest.raises(ValidationError):
        Brief(**{**BASE, "variants": 0})


def test_variants_over_20_rejected():
    with pytest.raises(ValidationError):
        Brief(**{**BASE, "variants": 21})


def test_missing_message_rejected():
    data = dict(BASE)
    del data["message"]
    with pytest.raises(ValidationError):
        Brief(**data)


def _write_brief(tmp_path, extra: str = "") -> Path:
    p = tmp_path / "brief.yaml"
    p.write_text(
        "platform: tiktok\ntarget_seconds: 30\ngoal: awareness\nmessage: m\ncta: c\n" + extra,
        encoding="utf-8",
    )
    return p


def test_forbidden_file_merged(tmp_path):
    b = load_brief(_write_brief(tmp_path), FORBIDDEN)
    assert "thần kỳ" in b.forbidden


def test_duplicates_removed(tmp_path):
    p = _write_brief(tmp_path, "forbidden:\n  - thần kỳ\n  - siêu trắng\n")
    b = load_brief(p, FORBIDDEN)
    assert b.forbidden.count("thần kỳ") == 1
    assert "siêu trắng" in b.forbidden


def test_pending_claims_merged(tmp_path):
    b = load_brief(_write_brief(tmp_path), FORBIDDEN, PENDING)
    assert "3–4 tone" in b.forbidden


def test_forbidden_txt_has_product_rules():
    lines = [l.strip() for l in FORBIDDEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    for phrase in ["điều trị", "chữa", "loại bỏ vi khuẩn", "tái tạo men răng", "thay thế nha sĩ",
                   "100% an toàn", "không bao giờ ê buốt", "thần kỳ", "đảm bảo", "cấp tốc"]:
        assert phrase in lines


def test_product_md_keeps_confirm_markers():
    text = (ROOT / "library" / "product.md").read_text(encoding="utf-8")
    assert text.count("[CẦN XÁC NHẬN") >= 5
    assert "Những điều KHÔNG được nói" in text
