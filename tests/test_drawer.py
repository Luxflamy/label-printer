"""测试 preview/drawer.py — 验证 PNG 输出格式与尺寸。"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

import pytest

from label_printer.preview.drawer import SCALE, _px, draw_label_png
from label_printer.templates.loader import load_template
from label_printer.tspl.constants import DOTS_PER_MM

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

TEMPLATE_DIR = Path(__file__).parent.parent / "config" / "labels" / "templates"
LABELS_DIR = TEMPLATE_DIR.parent


def _png_dimensions(data: bytes) -> tuple[int, int]:
    """从 PNG 字节流中读取宽高（无需第三方库）。"""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "不是合法 PNG"
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    return w, h


def _simple_template(width_mm: float, height_mm: float, elements: list[dict[str, Any]]) -> dict:
    return {
        "label": {
            "width_mm": width_mm,
            "height_mm": height_mm,
            "gap_mm": 2,
            "direction": 1,
        },
        "elements": elements,
    }


# ---------------------------------------------------------------------------
# 基础 PNG 合法性
# ---------------------------------------------------------------------------

def test_draw_returns_bytes():
    tpl = _simple_template(50, 30, [])
    result = draw_label_png(tpl, {})
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_output_is_valid_png():
    tpl = _simple_template(50, 30, [])
    png = draw_label_png(tpl, {})
    # PNG 文件头
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    # 至少含 IHDR chunk (12 bytes) + IEND chunk
    assert b"IHDR" in png
    assert png.endswith(b"IEND\xaeB`\x82")


# ---------------------------------------------------------------------------
# 尺寸验证
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("w_mm,h_mm", [
    (50, 30),
    (100, 150),
    (60, 40),
])
def test_image_dimensions_match_label_size(w_mm: float, h_mm: float):
    tpl = _simple_template(w_mm, h_mm, [])
    png = draw_label_png(tpl, {})
    w_px, h_px = _png_dimensions(png)
    expected_w = _px(w_mm)
    expected_h = _px(h_mm)
    assert w_px == expected_w, f"宽度不对: {w_px} != {expected_w}"
    assert h_px == expected_h, f"高度不对: {h_px} != {expected_h}"


# ---------------------------------------------------------------------------
# 含 text 元素
# ---------------------------------------------------------------------------

def test_draw_with_text_element():
    tpl = _simple_template(50, 30, [
        {"type": "text", "content": "Hello", "x_mm": 3, "y_mm": 5, "font": "3"},
    ])
    png = draw_label_png(tpl, {})
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_draw_with_text_variable():
    tpl = _simple_template(50, 30, [
        {"type": "text", "content": "{{ sku }}", "align": "center", "y_mm": 5, "font": "3"},
    ])
    png = draw_label_png(tpl, {"sku": "SKU-001"})
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_draw_overseas_template_with_chinese_title():
    tpl = load_template("100x150_250p_overseas", LABELS_DIR)
    png = draw_label_png(tpl, {"sku": "SKU-OVERSEAS-001"})

    assert _png_dimensions(png) == (_px(100), _px(150))
    assert len(png) > 5000


# ---------------------------------------------------------------------------
# 含 barcode 元素
# ---------------------------------------------------------------------------

def test_draw_with_barcode_element():
    tpl = _simple_template(100, 60, [
        {
            "type": "barcode",
            "content": "1234567890",
            "align": "center",
            "y_mm": 10,
            "height_mm": 15,
            "symbology": "128",
            "human_readable": True,
        }
    ])
    png = draw_label_png(tpl, {})
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = _png_dimensions(png)
    assert w > 0 and h > 0


# ---------------------------------------------------------------------------
# 含 qrcode 元素
# ---------------------------------------------------------------------------

def test_draw_with_qrcode_element():
    tpl = _simple_template(100, 100, [
        {
            "type": "qrcode",
            "content": "https://example.com/product/123",
            "align": "center",
            "y_mm": 5,
            "cell_width": 4,
            "error_correction": "M",
        }
    ])
    png = draw_label_png(tpl, {})
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# 缺少变量时抛出异常
# ---------------------------------------------------------------------------

def test_missing_variable_raises():
    tpl = _simple_template(50, 30, [
        {"type": "text", "content": "{{ missing_var }}", "y_mm": 5, "font": "3"},
    ])
    with pytest.raises(ValueError, match="missing_var"):
        draw_label_png(tpl, {})


# ---------------------------------------------------------------------------
# SCALE / _px 辅助函数
# ---------------------------------------------------------------------------

def test_px_helper_correctness():
    assert _px(1) == DOTS_PER_MM * SCALE
    assert _px(50) == 50 * DOTS_PER_MM * SCALE
