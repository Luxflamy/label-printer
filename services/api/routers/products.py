"""商品数据 API — 从 data/stores/ 读取多个商品库。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.api.product_stores import StoreNotFoundError, list_stores, load_products
from services.api.schemas import Envelope, ProductItem, ProductStoresData

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/stores", response_model=Envelope[ProductStoresData])
def list_product_stores() -> Envelope[ProductStoresData]:
    """返回可用商品库列表及默认库 ID。"""
    stores, default_id = list_stores()
    return Envelope(
        ok=True,
        data=ProductStoresData(stores=stores, default_store=default_id),
    )


@router.get("", response_model=Envelope[list[ProductItem]])
def list_products(
    store: str | None = Query(default=None, description="商品库 ID，默认使用 manifest 中的 default"),
    q: str = Query(default="", description="搜索关键词（匹配 SKU / FNSKU / 短标题）"),
    qty_only: bool = Query(default=False, description="仅返回 qty > 0 的商品"),
) -> Envelope[list[ProductItem]]:
    """返回指定商品库的商品列表。"""
    try:
        items = load_products(store)
    except StoreNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"商品库不存在: {exc}") from exc

    if qty_only:
        items = [i for i in items if i.qty > 0]

    if q:
        kw = q.lower()
        items = [
            i
            for i in items
            if kw in i.sku.lower()
            or kw in i.fnsku.lower()
            or kw in i.short_title.lower()
            or kw in i.product_name.lower()
        ]

    return Envelope(ok=True, data=items)
