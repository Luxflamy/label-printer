"""TSPL2 命令构建器 — 将标签描述转换为 TSPL 字节流。

设计目标：只负责"画什么"到"TSPL 文本"的转换，不涉及连接、模板变量替换。
供 templates/renderer.py 调用。
"""

from __future__ import annotations

from label_printer.tspl.constants import DOTS_PER_MM, EOL
from label_printer.utils.units import mm_to_dots


def _escape(text: str) -> str:
    """TSPL 用双引号包裹字符串，内容中的双引号需替换以避免破坏指令。"""
    return str(text).replace('"', "'")


class LabelJob:
    """链式构建 TSPL 指令，最终 build() 输出 bytes。"""

    def __init__(
        self,
        width_mm: float,
        height_mm: float,
        gap_mm: float = 2,
        direction: int = 1,
        dots_per_mm: int = DOTS_PER_MM,
        reference: tuple[int, int] = (0, 0),
    ) -> None:
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.gap_mm = gap_mm
        self.direction = direction
        self.dots_per_mm = dots_per_mm
        self.reference = reference
        self._elements: list[str] = []

    def _dots(self, mm: float) -> int:
        return mm_to_dots(mm, self.dots_per_mm)

    def text(
        self,
        x_mm: float,
        y_mm: float,
        content: str,
        font: str = "3",
        rotation: int = 0,
        x_mul: int = 1,
        y_mul: int = 1,
    ) -> "LabelJob":
        x, y = self._dots(x_mm), self._dots(y_mm)
        self._elements.append(
            f'TEXT {x},{y},"{font}",{rotation},{x_mul},{y_mul},"{_escape(content)}"'
        )
        return self

    def barcode(
        self,
        x_mm: float,
        y_mm: float,
        content: str,
        symbology: str = "128",
        height_mm: float = 10,
        human_readable: bool = True,
        rotation: int = 0,
        narrow: int = 2,
        wide: int = 4,
    ) -> "LabelJob":
        x, y = self._dots(x_mm), self._dots(y_mm)
        height = self._dots(height_mm)
        readable = 1 if human_readable else 0
        self._elements.append(
            f'BARCODE {x},{y},"{symbology}",{height},{readable},'
            f'{rotation},{narrow},{wide},"{_escape(content)}"'
        )
        return self

    def qrcode(
        self,
        x_mm: float,
        y_mm: float,
        content: str,
        error_correction: str = "M",
        cell_width: int = 4,
        mode: str = "A",
        rotation: int = 0,
    ) -> "LabelJob":
        x, y = self._dots(x_mm), self._dots(y_mm)
        self._elements.append(
            f'QRCODE {x},{y},{error_correction},{cell_width},{mode},'
            f'{rotation},"{_escape(content)}"'
        )
        return self

    def build(self, copies: int = 1) -> bytes:
        lines = [
            f"SIZE {self.width_mm} mm,{self.height_mm} mm",
            f"GAP {self.gap_mm} mm,0 mm",
            f"DIRECTION {self.direction}",
            f"REFERENCE {self.reference[0]},{self.reference[1]}",
            "CLS",
            *self._elements,
            f"PRINT {copies}",
        ]
        text = EOL.join(lines) + EOL
        return text.encode("utf-8")

    def build_text(self, copies: int = 1) -> str:
        """便于预览：返回可读的 TSPL 文本（等价于 build() 解码）。"""
        return self.build(copies).decode("utf-8")
