"""商品库加载测试。"""

from __future__ import annotations

from services.api.product_stores import get_default_store_id, list_stores, load_products


def test_default_store_is_example_store() -> None:
    assert get_default_store_id() == "example_store"


def test_list_stores_includes_example_store() -> None:
    stores, default_id = list_stores()
    store_ids = {s.id for s in stores}
    assert "example_store" in store_ids
    assert default_id == "example_store"


def test_load_example_store_has_products() -> None:
    products = load_products("example_store")
    assert len(products) > 0
    assert all(p.sku for p in products)
