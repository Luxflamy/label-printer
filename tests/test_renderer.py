"""模板渲染单元测试。"""

from pathlib import Path

import pytest

from label_printer.templates.loader import load_template
from label_printer.templates.renderer import (
    extract_variables,
    render_template,
    render_template_text,
)

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


def test_extract_variables_from_compact_template() -> None:
    tpl = load_template("50x30_800p_product", LABELS_DIR)
    assert extract_variables(tpl) == {"fnsku", "short_title", "sku"}


def test_render_template_small_label() -> None:
    tpl = load_template("50x30_800p_product", LABELS_DIR)
    variables = {
        "sku": "BT-Green-Queen",
        "fnsku": "X002J4KZS3",
        "short_title": "BESTOUCH DuvetCover SetGreen Queen New",
    }
    text = render_template_text(tpl, variables)

    assert "SIZE 50 mm,30 mm" in text or "SIZE 50.0 mm,30 mm" in text
    assert "GAP 2 mm,0 mm" in text
    assert '"BT-Green-Queen"' in text
    assert '"X002J4KZS3"' in text
    assert "BESTOUCH DuvetCover" in text
    assert text.strip().endswith("PRINT 1")
    assert "BARCODE 76," in text
    assert 'TEXT 124,40,"2",0,2,2,"BT-Green-Queen"' in text


def test_render_template_missing_variable_raises() -> None:
    tpl = load_template("50x30_800p_product", LABELS_DIR)
    with pytest.raises(ValueError, match="缺少模板变量"):
        render_template(tpl, {"sku": "BT-Green-Queen"})


def test_render_large_template_has_qrcode_command() -> None:
    tpl = load_template("100x150_250p_product", LABELS_DIR)
    variables = {
        "product_name": "Apple Gift",
        "sku": "A001",
        "barcode": "6901234567890",
        "remark": "Fragile",
    }
    text = render_template_text(tpl, variables)
    assert "QRCODE" in text
    assert "Fragile" in text
    assert "QRCODE 496," not in text  # 原先固定 x=62mm=496 dots，居中后应变化
