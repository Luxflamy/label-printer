"""批量打印 API — 先渲染全部条目，合并后一次发送，消除张间卡顿。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from label_printer.api.service import LabelPrinterService
from services.api.deps import get_service
from services.api.product_stores import load_products
from services.api.schemas import (
    BatchItemResult,
    BatchPrintData,
    BatchPrintRequest,
    Envelope,
)

router = APIRouter(tags=["batch"])


def _product_index(store_id: str | None) -> dict[str, dict]:
    """把商品列表转成 {id: item} 字典，方便按 ID 查找。"""
    return {item.id: item for item in load_products(store_id)}


@router.post("/batch/print", response_model=Envelope[BatchPrintData])
def batch_print(
    req: BatchPrintRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[BatchPrintData]:
    """按队列顺序渲染所有条目，合并成一次打印发送。

    - 商品 ID 不存在：直接标为失败，不影响其余条目
    - 渲染失败（变量缺失等）：跳过该条，其余正常打印
    - 发送失败（连接错误）：由全局异常处理器返回 502
    结束后响应中包含每条成功/失败及原因。
    """
    index = _product_index(req.store)

    # 先过滤掉商品 ID 不存在的条目
    pre_results: list[BatchItemResult] = []
    items: list[dict] = []

    for item in req.items:
        product = index.get(item.product_id)
        if product is None:
            pre_results.append(
                BatchItemResult(
                    product_id=item.product_id,
                    sku="",
                    copies=item.copies,
                    ok=False,
                    error=f"商品 ID 不存在: {item.product_id}",
                )
            )
        else:
            items.append(
                {
                    "product_id": item.product_id,
                    "sku": product.sku,
                    "variables": {
                        "sku": product.sku,
                        "fnsku": product.fnsku,
                        "short_title": product.short_title,
                    },
                    "copies": item.copies,
                }
            )

    # 合并渲染 + 一次发送
    batch = service.print_batch(req.template, items)

    all_results = pre_results + [
        BatchItemResult(
            product_id=r.product_id,
            sku=r.sku,
            copies=r.copies,
            ok=r.ok,
            error=r.error,
        )
        for r in batch.results
    ]

    succeeded = sum(1 for r in all_results if r.ok)
    return Envelope(
        ok=True,
        data=BatchPrintData(
            total=len(all_results),
            succeeded=succeeded,
            failed=len(all_results) - succeeded,
            results=all_results,
        ),
    )
