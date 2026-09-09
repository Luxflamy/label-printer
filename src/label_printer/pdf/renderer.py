"""PDF 页面 → 标签尺寸位图。"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Literal

from PIL import Image

from label_printer.tspl.bitmap import paste_scaled_centered, rasterize_for_label
from label_printer.tspl.constants import DOTS_PER_MM
from label_printer.utils.units import mm_to_dots

FitMode = Literal["contain", "cover", "fill"]
MAX_PDF_BYTES = 20 * 1024 * 1024

# 运货大标签固定 250P
SHIPPING_WIDTH_MM = 100.0
SHIPPING_HEIGHT_MM = 150.0
SHIPPING_STOCK_CODE = "250P"
SHIPPING_GAP_MM = 2.0
SHIPPING_DIRECTION = 1
DEFAULT_PRINT_SCALE = 0.94
MIN_PRINT_SCALE = 0.5
MAX_PRINT_SCALE = 1.5


@dataclass
class PdfPageInfo:
    page_count: int
    page_index: int
    pdf_width_mm: float
    pdf_height_mm: float
    target_width_mm: float
    target_height_mm: float
    target_stock: str
    fit_mode: FitMode
    rotation: int
    scale: float
    dots_per_mm: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class PdfRenderResult:
    info: PdfPageInfo
    image: Image.Image
    preview_png: bytes


def _require_fitz():
    try:
        import fitz  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError("PDF 功能需要 PyMuPDF：pip install '.[pdf]'") from exc
    return fitz


def validate_pdf_bytes(data: bytes) -> None:
    if len(data) > MAX_PDF_BYTES:
        raise ValueError(f"PDF 超过大小限制（最大 {MAX_PDF_BYTES // (1024 * 1024)}MB）")
    if not data.startswith(b"%PDF"):
        raise ValueError("不是有效的 PDF 文件")


def _page_size_mm(page) -> tuple[float, float]:
    rect = page.rect
    # PDF 默认单位 pt，72 pt = 1 inch = 25.4 mm
    width_mm = rect.width * 25.4 / 72.0
    height_mm = rect.height * 25.4 / 72.0
    return width_mm, height_mm


def _render_page_rgb(page, rotation: int, render_dpi: float = 203) -> Image.Image:
    fitz = _require_fitz()
    zoom = render_dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    if rotation:
        matrix = matrix.prerotate(rotation)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _clamp_scale(scale: float) -> float:
    return max(MIN_PRINT_SCALE, min(MAX_PRINT_SCALE, scale))


def _fit_image(
    img: Image.Image,
    width_dots: int,
    height_dots: int,
    fit_mode: FitMode,
    threshold: int,
    scale: float = 1.0,
) -> Image.Image:
    scale = _clamp_scale(scale)

    if fit_mode == "fill":
        canvas = Image.new("L", (width_dots, height_dots), 255)
        base = img.convert("L").resize((width_dots, height_dots), Image.LANCZOS)
        paste_scaled_centered(canvas, base, scale)
        return canvas.point(lambda p: 0 if p < threshold else 255, mode="1")

    if fit_mode == "cover":
        src = img.convert("L")
        base_scale = max(width_dots / src.width, height_dots / src.height)
        factor = base_scale * scale
        new_w = max(1, int(round(src.width * factor)))
        new_h = max(1, int(round(src.height * factor)))
        resized = src.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width_dots) // 2
        top = (new_h - height_dots) // 2
        cropped = resized.crop((left, top, left + width_dots, top + height_dots))
        return cropped.point(lambda p: 0 if p < threshold else 255, mode="1")

    return rasterize_for_label(
        img, width_dots, height_dots, threshold=threshold, scale=scale
    )


def render_pdf_page(
    pdf_bytes: bytes,
    page_index: int = 0,
    fit_mode: FitMode = "contain",
    rotation: int = 0,
    threshold: int = 128,
    scale: float = DEFAULT_PRINT_SCALE,
    width_mm: float = SHIPPING_WIDTH_MM,
    height_mm: float = SHIPPING_HEIGHT_MM,
    dots_per_mm: int = DOTS_PER_MM,
) -> PdfRenderResult:
    """渲染 PDF 指定页为标签尺寸 1-bit 图像，并生成 PNG 预览。

    dots_per_mm 应与打印机 DPI 一致（203dpi→8，300dpi→12）。
    """
    validate_pdf_bytes(pdf_bytes)
    fitz = _require_fitz()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.is_encrypted and not doc.authenticate(""):
        doc.close()
        raise ValueError("PDF 已加密，请先解密或另存为未加密文件")

    page_count = doc.page_count
    if page_count == 0:
        doc.close()
        raise ValueError("PDF 没有页面")
    if page_index < 0 or page_index >= page_count:
        doc.close()
        raise ValueError(f"页码超出范围：{page_index + 1} / {page_count}")

    page = doc[page_index]
    pdf_w_mm, pdf_h_mm = _page_size_mm(page)
    warnings: list[str] = []

    aspect_pdf = pdf_w_mm / pdf_h_mm if pdf_h_mm else 1.0
    aspect_label = width_mm / height_mm
    if abs(aspect_pdf - aspect_label) > 0.15:
        warnings.append(
            f"PDF 比例 ({pdf_w_mm:.0f}×{pdf_h_mm:.0f}mm) 与标签 ({width_mm:.0f}×{height_mm:.0f}mm) 不完全一致，将按「{fit_mode}」缩放"
        )

    rgb = _render_page_rgb(page, rotation, render_dpi=dots_per_mm * 25.4)
    doc.close()

    width_dots = mm_to_dots(width_mm, dots_per_mm)
    height_dots = mm_to_dots(height_mm, dots_per_mm)
    mono = _fit_image(rgb, width_dots, height_dots, fit_mode, threshold, scale=scale)

    preview_buf = io.BytesIO()
    mono.resize(
        (max(1, width_dots // 3), max(1, height_dots // 3)),
        Image.NEAREST,
    ).convert("RGB").save(preview_buf, format="PNG", optimize=True)

    info = PdfPageInfo(
        page_count=page_count,
        page_index=page_index,
        pdf_width_mm=round(pdf_w_mm, 1),
        pdf_height_mm=round(pdf_h_mm, 1),
        target_width_mm=width_mm,
        target_height_mm=height_mm,
        target_stock=SHIPPING_STOCK_CODE,
        fit_mode=fit_mode,
        rotation=rotation,
        scale=_clamp_scale(scale),
        dots_per_mm=dots_per_mm,
        warnings=warnings,
    )
    return PdfRenderResult(info=info, image=mono, preview_png=preview_buf.getvalue())
