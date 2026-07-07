"""标签模板列表与详情 — 前端据此动态生成变量表单。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from label_printer.api.service import LabelPrinterService
from services.api.deps import get_service
from services.api.schemas import Envelope, TemplateDetailSchema, TemplateSummarySchema

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=Envelope[list[TemplateSummarySchema]])
def list_templates(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[list[TemplateSummarySchema]]:
    summaries = service.list_templates()
    data = [TemplateSummarySchema.model_validate(s) for s in summaries]
    return Envelope(ok=True, data=data)


@router.get("/{name}", response_model=Envelope[TemplateDetailSchema])
def get_template(
    name: str, service: LabelPrinterService = Depends(get_service)
) -> Envelope[TemplateDetailSchema]:
    detail = service.get_template_detail(name)
    return Envelope(ok=True, data=TemplateDetailSchema(**detail))
