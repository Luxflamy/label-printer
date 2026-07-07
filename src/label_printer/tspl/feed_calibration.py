"""走纸/传感器自动校准 TSPL — GAPDETECT、AUTODETECT、BLINEDETECT。"""

from __future__ import annotations

from typing import Any, Literal

from label_printer.tspl.commands import _fmt_mm
from label_printer.tspl.constants import EOL

MediaType = Literal["gap", "blackmark"]
FeedStrategy = Literal["gapdetect", "autodetect"]

# 走纸搜索上限：约 3 个标签节距 + 余量，防止传感器未识别时无限走纸
_LIMIT_LABEL_PITCHES = 3
_LIMIT_EXTRA_MM = 10


def _limit_feed_mm(height_mm: float, gap_mm: float) -> float:
    pitch = height_mm + gap_mm
    return pitch * _LIMIT_LABEL_PITCHES + _LIMIT_EXTRA_MM


def build_auto_feed_calibration_bytes(
    label: dict[str, Any],
    media_type: MediaType = "gap",
    strategy: FeedStrategy = "gapdetect",
    dots_per_mm: int = 8,
    bline_mm: float = 3.0,
) -> bytes:
    """生成走纸传感器校准 TSPL（不打印，仅走纸定位）。

    设计要点（避免不停走纸）：
    - 不使用 SET GAP AUTO（会额外走 2~3 张，失败时可能走 10~20 英寸）
    - 不使用 HOME（传感器未校准时会无限找原点）
    - 使用 LIMITFEED 限制最大走纸长度
    - GAPDETECT 不传 x,y，由打印机自动测定（参数偏差会导致一直找间隙）
    - 最后用 FORMFEED 走到下一张标签起始（需已设 SIZE/GAP）
    """
    width_mm = float(label["width_mm"])
    height_mm = float(label["height_mm"])
    gap_mm = float(label.get("gap_mm", 2))
    direction = int(label.get("direction", 1))
    limit_mm = _limit_feed_mm(height_mm, gap_mm)

    lines: list[str] = [
        f"SIZE {_fmt_mm(width_mm)} mm,{_fmt_mm(height_mm)} mm",
        f"DIRECTION {direction}",
        f"LIMITFEED {_fmt_mm(limit_mm)} mm",
    ]

    if media_type == "blackmark":
        lines.insert(1, f"BLINE {_fmt_mm(bline_mm)} mm,0 mm")
        lines.append("BLINEDETECT")
    elif strategy == "autodetect":
        lines.append("AUTODETECT")
    else:
        lines.insert(1, f"GAP {_fmt_mm(gap_mm)} mm,0 mm")
        lines.append("GAPDETECT")

    lines.append("FORMFEED")
    return (EOL.join(lines) + EOL).encode("utf-8")


def build_auto_feed_calibration_text(
    label: dict[str, Any],
    media_type: MediaType = "gap",
    strategy: FeedStrategy = "gapdetect",
    dots_per_mm: int = 8,
    bline_mm: float = 3.0,
) -> str:
    return build_auto_feed_calibration_bytes(
        label, media_type, strategy, dots_per_mm, bline_mm
    ).decode("utf-8")
