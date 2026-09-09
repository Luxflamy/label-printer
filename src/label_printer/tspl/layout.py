"""布局辅助 — 估算元素宽度并计算水平对齐坐标。

TSPL 的 TEXT / BARCODE / QRCODE 均以左上角为锚点，无内置居中指令；
模板里设置 align: center 时，由本模块估算宽度后反算 x 坐标。
"""

from __future__ import annotations

from label_printer.tspl.constants import DOTS_PER_MM
from label_printer.utils.units import dots_to_mm, mm_to_dots

# TSC 内置字体在 203 dpi 下的单字符近似宽度（dots），来源：TSPL 手册字号表
FONT_CHAR_WIDTH_DOTS: dict[str, int] = {
    "1": 8,
    "2": 12,
    "3": 16,
    "4": 24,
    "5": 32,
    "6": 14,
    "7": 21,
    "8": 14,
}


def estimate_text_width_dots(
    content: str,
    font: str = "3",
    x_mul: int = 1,
) -> int:
    char_width = FONT_CHAR_WIDTH_DOTS.get(font, 16)
    return len(content) * char_width * x_mul


def estimate_barcode_width_dots(
    content: str,
    symbology: str = "128",
    narrow: int = 2,
    wide: int = 4,
) -> int:
    """估算一维条码条区宽度（不含人眼可读文字）。

    理论模块数按 Code128 计算，再乘以 TSC 203dpi 下的经验校准系数（约 0.55），
    避免估算过宽导致短标签上居中 x 仍贴左边。
    """
    n = len(content)
    if symbology.upper() in ("128", "CODE128"):
        modules = 11 * n + 35
    elif symbology.upper() in ("39", "CODE39"):
        modules = 12 * n + 25
    else:
        modules = 11 * n + 35

    _TSC_CALIBRATION = 0.55
    return int(modules * narrow * _TSC_CALIBRATION)


def estimate_qrcode_width_dots(content: str, cell_width: int = 4) -> int:
    """按数据长度选取 QR 版本，估算模块边长 × cell_width。"""
    length = len(content)
    if length <= 17:
        version = 1
    elif length <= 32:
        version = 2
    elif length <= 53:
        version = 3
    elif length <= 78:
        version = 4
    else:
        version = 5
    modules = version * 4 + 17
    return modules * cell_width


def resolve_x_mm(
    element: dict,
    content: str,
    label_width_mm: float,
    dots_per_mm: int = DOTS_PER_MM,
) -> float:
    """根据 align 解析最终 x_mm；left 时直接使用模板中的 x_mm。"""
    align = element.get("align", "left")
    base_x_mm = float(element.get("x_mm", 0))
    if align == "left":
        return base_x_mm

    el_type = element["type"]
    if el_type == "text":
        width_dots = estimate_text_width_dots(
            content,
            font=str(element.get("font", "3")),
            x_mul=int(element.get("x_mul", 1)),
        )
    elif el_type == "barcode":
        width_dots = estimate_barcode_width_dots(
            content,
            symbology=str(element.get("symbology", "128")),
            narrow=int(element.get("narrow", 2)),
            wide=int(element.get("wide", 4)),
        )
    elif el_type == "qrcode":
        width_dots = estimate_qrcode_width_dots(
            content,
            cell_width=int(element.get("cell_width", 4)),
        )
    elif el_type == "bitmap_text":
        width_dots = mm_to_dots(float(element["width_mm"]), dots_per_mm)
    else:
        return base_x_mm

    label_width_dots = mm_to_dots(label_width_mm, dots_per_mm)
    if align == "center":
        # 文字超宽时允许负 x，使左右等量裁切，视觉上仍居中
        x_dots = (label_width_dots - width_dots) // 2
    elif align == "right":
        x_dots = max(0, label_width_dots - width_dots)
    else:
        return base_x_mm

    x_dots += mm_to_dots(base_x_mm, dots_per_mm)
    return dots_to_mm(x_dots, dots_per_mm)
