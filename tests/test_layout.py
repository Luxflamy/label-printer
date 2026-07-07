"""布局与居中坐标计算单元测试。"""

from label_printer.tspl.layout import (
    estimate_barcode_width_dots,
    estimate_text_width_dots,
    resolve_x_mm,
)


def test_estimate_text_width_scales_with_font_and_mul() -> None:
    assert estimate_text_width_dots("ABCD", font="3", x_mul=1) == 64
    assert estimate_text_width_dots("ABCD", font="3", x_mul=2) == 128


def test_resolve_x_mm_left_uses_template_x() -> None:
    x = resolve_x_mm(
        {"type": "text", "align": "left", "x_mm": 3, "font": "3"},
        "Hello",
        label_width_mm=50,
    )
    assert x == 3


def test_resolve_x_mm_center_places_text_in_middle() -> None:
    # 50mm = 400 dots; "Apple Gift" (10 chars) font 3 => 160 dots; center x = 120 dots = 15mm
    x = resolve_x_mm(
        {"type": "text", "align": "center", "font": "3", "x_mul": 1},
        "Apple Gift",
        label_width_mm=50,
    )
    assert x == 15.0


def test_resolve_x_mm_center_barcode_not_at_left_edge() -> None:
    x = resolve_x_mm(
        {
            "type": "barcode",
            "align": "center",
            "symbology": "128",
            "narrow": 2,
            "wide": 4,
        },
        "6901234567890",
        label_width_mm=50,
    )
    assert x >= 10


def test_barcode_width_grows_with_data_length() -> None:
    short = estimate_barcode_width_dots("123", symbology="128", narrow=2)
    long = estimate_barcode_width_dots("6901234567890", symbology="128", narrow=2)
    assert long > short
