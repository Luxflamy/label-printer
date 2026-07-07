"""PDF 位图标签 TSPL 组装。"""

from __future__ import annotations

from PIL import Image

from label_printer.calibration import CalibrationProfile
from label_printer.pdf.renderer import SHIPPING_DIRECTION, SHIPPING_GAP_MM
from label_printer.tspl.bitmap import pack_monochrome_image
from label_printer.tspl.commands import LabelJob, _fmt_mm
from label_printer.tspl.constants import DOTS_PER_MM, EOL


def build_pdf_label_tspl(
    image: Image.Image,
    width_mm: float,
    height_mm: float,
    calibration: CalibrationProfile | None = None,
    gap_mm: float = SHIPPING_GAP_MM,
    direction: int = SHIPPING_DIRECTION,
    copies: int = 1,
) -> bytes:
    """将整页位图打成一张 TSPL（BITMAP 全幅）。"""
    profile = calibration or CalibrationProfile()
    bitmap = pack_monochrome_image(image)

    job = LabelJob(
        width_mm=width_mm,
        height_mm=height_mm,
        gap_mm=gap_mm,
        gap_offset_mm=profile.gap_offset_mm,
        direction=direction,
        reference=(profile.reference_x_dots, profile.reference_y_dots),
    )

    header = (
        f"SIZE {_fmt_mm(job.width_mm)} mm,{_fmt_mm(job.height_mm)} mm{EOL}"
        f"GAP {_fmt_mm(job.gap_mm)} mm,{_fmt_mm(job.gap_offset_mm)} mm{EOL}"
        f"DIRECTION {job.direction}{EOL}"
        f"REFERENCE {job.reference[0]},{job.reference[1]}{EOL}"
        f"CLS{EOL}"
        f"BITMAP 0,0,{bitmap.width_bytes},{bitmap.height_dots},0,"
    ).encode("utf-8")
    footer = f"{EOL}PRINT {copies}{EOL}".encode("utf-8")
    return header + bitmap.data + footer
