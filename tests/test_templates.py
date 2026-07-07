"""模板加载与 extends 合并测试。"""

from pathlib import Path

import pytest

from label_printer.templates.loader import list_templates, load_preset, load_size, load_template

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


def test_list_templates_includes_new_sizes() -> None:
    names = list_templates(LABELS_DIR)
    assert "xiaobiaoqian" in names
    assert "50x30_800p_product" in names
    assert "100x150_250p_product" in names


def test_load_size_50x30_800p() -> None:
    spec = load_size("50x30_800p", LABELS_DIR)
    assert spec["label"]["width_mm"] == 50
    assert spec["label"]["height_mm"] == 30
    assert spec["meta"]["stock_code"] == "800P"


def test_load_size_100x150_250p() -> None:
    spec = load_size("100x150_250p", LABELS_DIR)
    assert spec["label"]["width_mm"] == 100
    assert spec["label"]["height_mm"] == 150
    assert spec["meta"]["stock_code"] == "250P"


def test_load_preset_product_compact() -> None:
    preset = load_preset("product_compact", LABELS_DIR)
    ids = [el["id"] for el in preset["elements"]]
    assert ids == ["product_name", "sku", "barcode"]


def test_load_preset_fba_compact() -> None:
    preset = load_preset("fba_compact", LABELS_DIR)
    ids = [el["id"] for el in preset["elements"]]
    assert ids == ["sku", "fnsku_barcode", "fnsku_code", "short_title"]


def test_load_template_xiaobiaoqian_is_default_fba_layout() -> None:
    tpl = load_template("xiaobiaoqian", LABELS_DIR)
    assert tpl["name"] == "小标签"
    assert tpl["meta"].get("default") is True
    assert tpl["label"]["width_mm"] == 50
    assert len(tpl["elements"]) == 4
    assert tpl["elements"][0]["id"] == "sku"
    assert tpl["elements"][0]["x_mul"] == 1.5


def test_load_template_merges_extends() -> None:
    tpl = load_template("50x30_800p_product", LABELS_DIR)
    assert tpl["name"] == "50x30_800p_product"
    assert tpl["label"]["width_mm"] == 50
    assert tpl["label"]["height_mm"] == 30
    assert len(tpl["elements"]) == 4
    assert tpl["elements"][0]["content"] == "{{ sku }}"


def test_load_template_large_has_qrcode() -> None:
    tpl = load_template("100x150_250p_product", LABELS_DIR)
    types = [el["type"] for el in tpl["elements"]]
    assert "qrcode" in types
    assert tpl["label"]["width_mm"] == 100


def test_load_blank_base_has_no_elements() -> None:
    tpl = load_template("50x30_800p", LABELS_DIR)
    assert tpl["elements"] == []
    assert tpl["meta"]["stock_code"] == "800P"


def test_missing_template_lists_available() -> None:
    with pytest.raises(FileNotFoundError, match="可用"):
        load_template("no_such_template", LABELS_DIR)
