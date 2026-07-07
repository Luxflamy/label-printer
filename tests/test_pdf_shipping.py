"""PDF 运货标签渲染与 TSPL 测试。"""

from __future__ import annotations

import fitz

from label_printer.pdf.label_job import build_pdf_label_tspl
from label_printer.pdf.renderer import render_pdf_page


def _minimal_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=288, height=432)  # 4x6 inch in pt
    page.insert_text((72, 72), "SHIP TEST", fontsize=24)
    return doc.tobytes()


def test_render_pdf_page_produces_preview_at_203dpi() -> None:
    pdf = _minimal_pdf_bytes()
    result = render_pdf_page(pdf, page_index=0, scale=1.0, dots_per_mm=8)
    assert result.info.page_count == 1
    assert result.info.target_stock == "250P"
    assert result.info.dots_per_mm == 8
    assert result.image.size == (800, 1200)
    assert len(result.preview_png) > 100


def test_render_pdf_page_at_300dpi() -> None:
    pdf = _minimal_pdf_bytes()
    result = render_pdf_page(pdf, scale=1.0, dots_per_mm=12)
    assert result.info.dots_per_mm == 12
    assert result.image.size == (1200, 1800)


def test_build_pdf_label_tspl_contains_bitmap() -> None:
    pdf = _minimal_pdf_bytes()
    rendered = render_pdf_page(pdf, scale=1.0, dots_per_mm=8)
    tspl = build_pdf_label_tspl(rendered.image, 100, 150)
    assert b"SIZE 100 mm,150 mm" in tspl
    assert b"BITMAP 0,0,100,1200,0," in tspl
    assert b"PRINT 1" in tspl


def test_build_pdf_label_tspl_300dpi_bitmap_header() -> None:
    pdf = _minimal_pdf_bytes()
    rendered = render_pdf_page(pdf, scale=1.0, dots_per_mm=12)
    tspl = build_pdf_label_tspl(rendered.image, 100, 150)
    assert b"BITMAP 0,0,150,1800,0," in tspl
