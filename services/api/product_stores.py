"""商品库加载 — 支持 data/stores/ 下多个 JSON 库。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from services.api.schemas import ProductItem, ProductStoreSummary

_STORES_DIR = Path(__file__).resolve().parents[2] / "data" / "stores"
_MANIFEST_FILE = _STORES_DIR / "manifest.yaml"


class StoreNotFoundError(KeyError):
    """指定的商品库不存在。"""


@lru_cache(maxsize=1)
def _load_manifest() -> dict[str, Any]:
    if not _MANIFEST_FILE.exists():
        return {"default": None, "stores": {}}
    data = yaml.safe_load(_MANIFEST_FILE.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"default": None, "stores": {}}
    return data


def _store_display_name(store_id: str) -> str:
    manifest = _load_manifest()
    stores_meta = manifest.get("stores") or {}
    entry = stores_meta.get(store_id)
    if isinstance(entry, dict) and entry.get("name"):
        return str(entry["name"])
    return store_id


def _discover_store_ids() -> list[str]:
    manifest = _load_manifest()
    manifest_ids = list((manifest.get("stores") or {}).keys())
    file_ids = sorted(p.stem for p in _STORES_DIR.glob("*.json"))
    seen: set[str] = set()
    ordered: list[str] = []
    for store_id in manifest_ids + file_ids:
        if store_id not in seen and (_STORES_DIR / f"{store_id}.json").exists():
            seen.add(store_id)
            ordered.append(store_id)
    return ordered


def get_default_store_id() -> str | None:
    manifest = _load_manifest()
    default_id = manifest.get("default")
    store_ids = _discover_store_ids()
    if default_id and (_STORES_DIR / f"{default_id}.json").exists():
        return str(default_id)
    return store_ids[0] if store_ids else None


def list_stores() -> tuple[list[ProductStoreSummary], str | None]:
    """返回可用商品库列表及默认库 ID。"""
    summaries: list[ProductStoreSummary] = []
    for store_id in _discover_store_ids():
        products = _load_products(store_id)
        summaries.append(
            ProductStoreSummary(
                id=store_id,
                name=_store_display_name(store_id),
                product_count=len(products),
            )
        )
    return summaries, get_default_store_id()


@lru_cache(maxsize=8)
def _load_products(store_id: str) -> tuple[ProductItem, ...]:
    path = _STORES_DIR / f"{store_id}.json"
    if not path.exists():
        raise StoreNotFoundError(store_id)

    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    items: list[ProductItem] = []
    for item_id, entry in raw.items():
        product = entry.get("product", {})
        sku = product.get("sku", "")
        fnsku = product.get("fnsku", "")
        short_title = product.get("短标题", "").strip()
        product_name = product.get("product-name", "")
        qty = int(entry.get("qty", 0))
        items.append(
            ProductItem(
                id=item_id,
                sku=sku,
                fnsku=fnsku,
                short_title=short_title,
                product_name=product_name,
                qty=qty,
            )
        )
    items.sort(key=lambda x: x.sku.lower())
    return tuple(items)


def load_products(store_id: str | None = None) -> list[ProductItem]:
    """加载指定商品库；未指定时使用 manifest 中的 default。"""
    resolved = store_id or get_default_store_id()
    if not resolved:
        return []
    return list(_load_products(resolved))
