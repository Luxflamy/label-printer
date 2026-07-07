"""渲染预览与打印 — MVP 范围：单张打印（批量见后续迭代）。"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends

from label_printer.api.service import LabelPrinterService
from services.api.deps import get_service
from services.api.schemas import (
    Envelope,
    PreviewData,
    PreviewRequest,
    PrintData,
    PrintRequest,
    RenderData,
    RenderRequest,
)

router = APIRouter(tags=["print"])


@router.post("/render", response_model=Envelope[RenderData])
def render(
    req: RenderRequest, service: LabelPrinterService = Depends(get_service)
) -> Envelope[RenderData]:
    result = service.render(req.template, req.variables, copies=req.copies)
    return Envelope(ok=True, data=RenderData.model_validate(result))


@router.post("/render/preview", response_model=Envelope[PreviewData])
def render_preview(
    req: PreviewRequest, service: LabelPrinterService = Depends(get_service)
) -> Envelope[PreviewData]:
    """返回 base64 编码的 PNG 预览图，前端直接用 <img src="data:image/png;base64,..."> 展示。"""
    result = service.render_preview_image(req.template, req.variables)
    b64 = base64.b64encode(result.png_bytes).decode("ascii")
    data = PreviewData(
        template=result.template,
        image_b64=b64,
        width_mm=result.width_mm,
        height_mm=result.height_mm,
    )
    return Envelope(ok=True, data=data)


@router.post("/print", response_model=Envelope[PrintData])
def print_label(
    req: PrintRequest, service: LabelPrinterService = Depends(get_service)
) -> Envelope[PrintData]:
    result = service.print_one(req.template, req.variables, copies=req.copies)
    return Envelope(ok=True, data=PrintData.model_validate(result))
