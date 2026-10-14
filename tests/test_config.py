from pathlib import Path

from vf.config import load_config


def test_config_resolves_drive_paths(tmp_path):
    cfg_file = tmp_path / "vf.toml"
    cfg_file.write_text('drive_root = "G:/My Drive/EDIT"\n', encoding="utf-8")
    cfg = load_config(cfg_file)
    assert cfg.drive_root == Path("G:/My Drive/EDIT")
    assert cfg.sources_dir.name == "source gốc"
    assert cfg.references_dir == cfg.drive_root / "video tham khảo"
    assert cfg.out_dir == cfg.drive_root / "out"


def test_windows_backslash_path_gives_clear_error(tmp_path):
    import pytest
    cfg_file = tmp_path / "vf.toml"
    cfg_file.write_text('drive_root = "G:\\My Drive\\EDIT"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="dấu nháy đơn"):
        load_config(cfg_file)


def test_windows_path_in_single_quotes(tmp_path):
    cfg_file = tmp_path / "vf.toml"
    cfg_file.write_text("drive_root = 'G:\\My Drive\\EDIT'\n", encoding="utf-8")
    assert str(load_config(cfg_file).drive_root).replace("\\", "/") == "G:/My Drive/EDIT"
