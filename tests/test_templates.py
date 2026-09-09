"""模板加载与 extends 合并测试。"""

from pathlib import Path

import pytest

from label_printer.templates.loader import list_templates, load_preset, load_size, load_template

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


def test_list_templates_includes_new_sizes() -> None:
    names = list_templates(LABELS_DIR)
    assert "xiaobiaoqian" in names
    assert "xiaobiaoqian_moomee" in names
    assert "50x30_800p_product" in names
    assert "100x150_250p_product" in names
    assert "100x150_250p_overseas" in names


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


def test_load_preset_moomee_compact_has_wider_barcode() -> None:
    preset = load_preset("moomee_compact", LABELS_DIR)
    barcode = next(el for el in preset["elements"] if el["id"] == "fnsku_barcode")
    assert barcode["narrow"] == 4
    assert barcode["wide"] == 8
    title = next(el for el in preset["elements"] if el["id"] == "short_title")
    assert title["type"] == "bitmap_text"
    assert title["wrap"] is True
    assert title["max_lines"] == 2


def test_load_template_xiaobiaoqian_moomee_is_independent() -> None:
    tpl = load_template("xiaobiaoqian_moomee", LABELS_DIR)
    assert tpl["name"] == "小标签 MooMee"
    assert tpl["label"]["width_mm"] == 50
    barcode = next(el for el in tpl["elements"] if el["id"] == "fnsku_barcode")
    assert barcode["narrow"] == 4
    # 默认小标签仍保持原窄条宽，互不影响
    default = load_template("xiaobiaoqian", LABELS_DIR)
    default_bc = next(el for el in default["elements"] if el["id"] == "fnsku_barcode")
    assert default_bc["narrow"] == 3


def test_load_template_xiaobiaoqian_is_default_fba_layout() -> None:
    tpl = load_template("xiaobiaoqian", LABELS_DIR)
    assert tpl["name"] == "小标签"
    assert tpl["meta"].get("default") is True
    assert tpl["label"]["width_mm"] == 50
    assert len(tpl["elements"]) == 4
    assert tpl["elements"][0]["id"] == "sku"
    assert tpl["elements"][0]["x_mul"] == 2


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


def test_load_overseas_template_has_expected_layout() -> None:
    tpl = load_template("100x150_250p_overseas", LABELS_DIR)
    ids = [element["id"] for element in tpl["elements"]]
    assert ids == [
        "shipping_title",
        "date_caption",
        "shipped_date",
        "shipped_time",
        "sku",
        "sku_barcode",
    ]
    assert tpl["meta"]["stock_code"] == "250P"
    assert tpl["meta"]["timezone"] == "America/Chicago"
    assert tpl["label"]["dots_per_mm"] == 12


def test_load_blank_base_has_no_elements() -> None:
    tpl = load_template("50x30_800p", LABELS_DIR)
    assert tpl["elements"] == []
    assert tpl["meta"]["stock_code"] == "800P"


def test_missing_template_lists_available() -> None:
    with pytest.raises(FileNotFoundError, match="可用"):
        load_template("no_such_template", LABELS_DIR)
