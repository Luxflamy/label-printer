"""毫米与 dots 换算 — 阶段 2 实现。"""

from label_printer.tspl.constants import DOTS_PER_MM


def mm_to_dots(mm: float, dots_per_mm: int = DOTS_PER_MM) -> int:
    return round(mm * dots_per_mm)


def dots_to_mm(dots: int, dots_per_mm: int = DOTS_PER_MM) -> float:
    return dots / dots_per_mm
