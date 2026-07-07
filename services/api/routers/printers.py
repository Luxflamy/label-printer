"""打印机发现、选择与配置查询。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from label_printer.api.service import LabelPrinterService, PrinterNotFoundError
from services.api.deps import get_service
from services.api.schemas import (
    Envelope,
    PrinterConfigData,
    PrinterInfo,
    PrinterListData,
    SelectPrinterRequest,
)

router = APIRouter(tags=["printers"])


@router.get("/printers", response_model=Envelope[PrinterListData])
def list_printers(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[PrinterListData]:
    summaries = service.list_printers_detailed()
    data = PrinterListData(
        printers=[PrinterInfo.model_validate(s, from_attributes=True) for s in summaries],
        selected_queue=service.get_selected_queue(),
    )
    return Envelope(ok=True, data=data)


@router.post("/printers/select", response_model=Envelope[PrinterListData])
def select_printer(
    req: SelectPrinterRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[PrinterListData]:
    """选中打印机并写回 config/printer.yaml。"""
    try:
        service.select_printer(req.queue)
    except PrinterNotFoundError:
        raise

    summaries = service.list_printers_detailed()
    data = PrinterListData(
        printers=[PrinterInfo.model_validate(s, from_attributes=True) for s in summaries],
        selected_queue=service.get_selected_queue(),
    )
    return Envelope(ok=True, data=data)


@router.get("/config", response_model=Envelope[PrinterConfigData])
def get_config(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[PrinterConfigData]:
    config = service.get_printer_config()
    return Envelope(ok=True, data=PrinterConfigData(**config))
