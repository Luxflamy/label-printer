"""自定义 SKU 小标签 — 手工输入打印，并维护已打印 SKU 历史。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from label_printer.api.service import SKU_LABEL_TEMPLATE, LabelPrinterService
from services.api.deps import get_service
from services.api.schemas import (
    Envelope,
    SkuDeleteData,
    SkuHistoryData,
    SkuLabelPrintData,
    SkuLabelPrintRequest,
    SkuRecordSchema,
)

router = APIRouter(prefix="/sku-labels", tags=["sku-labels"])

MAX_COPIES = 99
MAX_HISTORY_LIMIT = 100


@router.post("/print", response_model=Envelope[SkuLabelPrintData])
def print_sku_label(
    req: SkuLabelPrintRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[SkuLabelPrintData]:
    """打印一张纯 SKU 小标签；成功后该 SKU 会进入历史，可供后续搜索。"""
    result = service.print_sku_label(
        req.sku,
        template_name=req.template or SKU_LABEL_TEMPLATE,
        copies=max(1, min(req.copies, MAX_COPIES)),
        printer=req.printer,
    )
    return Envelope(ok=True, data=SkuLabelPrintData.model_validate(result))


@router.get("/history", response_model=Envelope[SkuHistoryData])
def list_sku_history(
    q: str = Query(default="", description="关键词，按 SKU 子串匹配"),
    limit: int = Query(default=20, ge=1, le=MAX_HISTORY_LIMIT),
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[SkuHistoryData]:
    """查询已打印过的 SKU，最近打印的排在前面。"""
    records = service.list_sku_history(q, limit=limit)
    return Envelope(
        ok=True,
        data=SkuHistoryData(
            items=[SkuRecordSchema.model_validate(r) for r in records],
            total=len(records),
        ),
    )


@router.delete("/history/{sku}", response_model=Envelope[SkuDeleteData])
def delete_sku_history(
    sku: str,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[SkuDeleteData]:
    """删除一条历史记录（例如输错的 SKU）。"""
    if not service.delete_sku_history(sku):
        raise HTTPException(status_code=404, detail=f"历史中不存在该 SKU: {sku}")
    return Envelope(ok=True, data=SkuDeleteData(sku=sku))
