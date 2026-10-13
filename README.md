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
cd remotion && npm install && cd ..   # chữ động (Remotion, cần Node 20+)
copy vf.toml.example vf.toml  # Mac: cp; rồi sửa drive_root tới thư mục EDIT (Drive đã bật Available offline)
pytest                        # kiểm tra môi trường (test chậm, phiên âm thật: pytest -m slow)
```

### Mỗi khi có source gốc mới

Bỏ video vào `EDIT/source gốc/`, mở Claude Code ở thư mục repo và gõ `/smilee-video` (hoặc nói "có source mới").
Skill sẽ: xem nguồn mới (`vf status`), học từ điểm đã chấm, tạo lô kế tiếp, hỏi brief một lần, phân tích, viết kịch bản dựng, render MP4 kèm chữ động (Remotion) vào `EDIT/out/<lô>/` và báo lại.

### Chạy tay từng bước

```
vf status          # nguồn nào mới, lô nào đã có, lô kế tiếp
vf new auto        # tạo jobs/lo-NN/brief.yaml, điền sẵn nguồn mới
vf analyze lo-NN    # chuẩn hoá + phiên âm + tìm khoảng lặng (lần đầu tải model large-v3 ~3 GB)
# Claude viết jobs/lo-NN/edl.json theo skill video-batch-edit
vf render lo-NN     # xuất EDIT/out/lo-NN/*.mp4, *_sheet.png, qa.json, review.csv
```
