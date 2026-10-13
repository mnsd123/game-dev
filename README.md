# game-dev

this is a new game development team.

## video-factory (Smilee)

Pipeline Python + ffmpeg để edit hàng loạt video Smilee. Kế hoạch: `docs/superpowers/plans/`.

### Cài trên máy (Windows/Mac)

```
git clone <repo> video-factory && cd video-factory
git checkout claude/smilee-video-pipeline-setup-y7gas2
python -m venv .venv
.venv\Scripts\activate        # Mac: source .venv/bin/activate
pip install -e ".[dev]"
copy vf.toml.example vf.toml  # Mac: cp; rồi sửa drive_root tới thư mục EDIT (Drive đã bật Available offline)
pytest                        # kiểm tra môi trường (test chậm, phiên âm thật: pytest -m slow)
```

### Chạy thử một lô

```
vf new lo-01        # tạo jobs/lo-01/brief.yaml để điền
vf analyze lo-01    # chuẩn hoá + phiên âm + tìm khoảng lặng (lần đầu tải model large-v3 ~3 GB)
# Claude viết jobs/lo-01/edl.json theo skill video-batch-edit
vf render lo-01     # xuất EDIT/out/lo-01/*.mp4, *_sheet.png, qa.json, review.csv
```
