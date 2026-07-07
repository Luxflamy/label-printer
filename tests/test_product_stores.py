"""商品库加载测试。"""

from __future__ import annotations

from pathlib import Path

from services.api.product_stores import get_default_store_id, list_stores, load_products

_STORES_DIR = Path(__file__).resolve().parents[1] / "data" / "stores"


def test_default_store_prefers_bt_store_when_present() -> None:
    default_id = get_default_store_id()
    if (_STORES_DIR / "BT_store.json").exists():
        assert default_id == "BT_store"
    else:
        assert default_id == "example_store"


def test_bt_store_listed_first_when_present() -> None:
    stores, default_id = list_stores()
    store_ids = [s.id for s in stores]
    assert "example_store" in store_ids
    if (_STORES_DIR / "BT_store.json").exists():
        assert store_ids[0] == "BT_store"
        assert default_id == "BT_store"
    else:
        assert default_id == "example_store"


def test_load_default_store_has_products() -> None:
    products = load_products()
    assert len(products) > 0
    assert all(p.sku for p in products)
