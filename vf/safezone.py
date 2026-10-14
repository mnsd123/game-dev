"""Vùng an toàn của khung 9:16 (1080x1920): chữ, nhãn, hình minh hoạ DO PIPELINE THÊM VÀO phải nằm trong vùng này để không bị
giao diện TikTok che (tên tài khoản + caption + nút CTA quảng cáo ở đáy, thanh tab ở trên, cột nút
avatar/tim/bình luận/chia sẻ ở mép phải).

Số liệu: library/brand/tokens.json (safe_zone, skill v2: phải 300 px khi y > 840) — gốc là file template safe zone của TikTok (vẽ trên 720x1280, quy ra 1080x1920) theo Socialync —
https://www.socialync.io/tools/safe-zones/tiktok . Lấy bộ chặt nhất trong các nguồn 2026 (đáy 660 px;
nguồn khác nói 350–560 px) để quảng cáo có caption dài + nút CTA cũng không bị che.

Không áp cho nội dung có sẵn trong source gốc (chữ in sẵn, sticker): giữ nguyên.
Một nguồn số liệu duy nhất: placement (Python), Remotion (truyền qua props `safe`) và QA đều đọc từ đây.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

W, H = 1080, 1920


@dataclass(frozen=True)
class SafeZone:
    top: int = 240  # px: thanh tab "Đang theo dõi / Dành cho bạn", nhãn "Được tài trợ"
    bottom: int = 660  # px: tên tài khoản, caption, nhạc, nút CTA quảng cáo
    side: int = 120  # px mỗi bên
    rail_w: int = 300  # px: mép phải phần dưới — cột nút (avatar, tim, bình luận, lưu, chia sẻ), skill v2
    rail_top: int = 840  # px: cột nút bắt đầu từ đây xuống đáy

    # --- tỉ lệ khung (0–1) ---
    @property
    def y0(self) -> float:
        return self.top / H

    @property
    def y1(self) -> float:
        return (H - self.bottom) / H

    @property
    def rail_y(self) -> float:
        return self.rail_top / H

    def x_range(self, y_top: float, y_bot: float) -> tuple[float, float]:
        """Khoảng ngang an toàn (tỉ lệ) cho một hộp kéo dài từ y_top tới y_bot."""
        right = W - self.side
        if y_bot > self.rail_y:
            right = min(right, W - self.rail_w)
        return self.side / W, right / W

    def center_x(self, y_top: float, y_bot: float) -> float:
        """Tâm ngang (tỉ lệ) của khoảng an toàn ở độ cao này: 0.5 ở nửa trên, lệch trái khi chạm hàng cột nút."""
        x0, x1 = self.x_range(y_top, y_bot)
        return (x0 + x1) / 2

    def max_w(self, y_top: float, y_bot: float) -> float:
        """Bề rộng (tỉ lệ) của khoảng an toàn ở độ cao này — hộp đặt giữa khoảng đó (center_x)."""
        x0, x1 = self.x_range(y_top, y_bot)
        return x1 - x0

    def max_centered_w(self, y_top: float, y_bot: float) -> float:
        """Bề rộng tối đa (tỉ lệ) của hộp căn giữa khung mà vẫn nằm trong vùng an toàn."""
        x0, x1 = self.x_range(y_top, y_bot)
        return 2 * min(0.5 - x0, x1 - 0.5)

    def violations(self, box: tuple[float, float, float, float]) -> list[str]:
        """Các cạnh của hộp (x0, y0, x1, y1, tỉ lệ) lấn ra ngoài vùng an toàn; rỗng = an toàn."""
        bx0, by0, bx1, by1 = box
        eps = 1e-6
        out = []
        if by0 < self.y0 - eps:
            out.append("trên")
        if by1 > self.y1 + eps:
            out.append("dưới")
        x0, x1 = self.x_range(by0, by1)
        if bx0 < x0 - eps:
            out.append("trái")
        if bx1 > x1 + eps:
            out.append("phải (cột nút)" if by1 > self.rail_y else "phải")
        return out

    def props(self) -> dict:
        """Truyền sang Remotion (px)."""
        return asdict(self)


def _from_tokens() -> SafeZone:
    """Số liệu từ library/brand/tokens.json (safe_zone); thiếu file thì dùng mặc định ở trên."""
    try:
        from vf.tokens import load_tokens

        z = load_tokens()["safe_zone"]
    except (FileNotFoundError, KeyError):
        return SafeZone()
    return SafeZone(top=z["top"], bottom=z["bottom"], side=max(z["left"], z["right"]),
                    rail_w=z["right_lower"], rail_top=z["right_lower_from_y"])


SAFE = _from_tokens()
