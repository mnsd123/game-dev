"""Đường dẫn mặc định, tính từ gốc dự án (chạy lệnh ở thư mục nào cũng được)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"
TEMPLATES = ROOT / "templates"
BRAND_DIR = LIBRARY / "brand"
FORBIDDEN_PATH = LIBRARY / "forbidden.txt"
PENDING_PATH = LIBRARY / "claims_pending.txt"
CAPTION_STYLE = TEMPLATES / "caption_style.ass"
BRIEF_TEMPLATE = TEMPLATES / "brief.yaml"
