"""模板渲染单元测试。"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from label_printer.templates.loader import load_template
from label_printer.templates.renderer import (
    enrich_variables,
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
    assert 'TEXT ' in text and '"BT-Green-Queen"' in text


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


def test_overseas_template_computes_local_time_and_renders_bitmap() -> None:
    tpl = load_template("100x150_250p_overseas", LABELS_DIR)
    assert extract_variables(tpl) == {"sku"}

    variables = enrich_variables(
        tpl,
        {"sku": "SKU-OVERSEAS-001"},
        now=datetime(2026, 8, 3, 15, 12, 30, tzinfo=timezone.utc),
    )
    assert variables["shipped_date"] == "2026-08-03"
    assert variables["shipped_time"] == "10:12:30 CDT"

    text = render_template_text(tpl, {"sku": "SKU-OVERSEAS-001"})
    data = render_template(tpl, {"sku": "SKU-OVERSEAS-001"})
    assert "BITMAP " in text
    assert "<40500 binary bytes>" in text
    assert 'BARCODE ' in text
    assert b"\xe6\xb5\xb7\xe5\xa4\x96\xe4\xbb\x93\xe5\x8f\x91\xe8\xb4\xa7" not in data
