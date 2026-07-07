"""打印机发现与配置查询。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from label_printer.api.service import LabelPrinterService
from services.api.deps import get_service
from services.api.schemas import Envelope, PrinterConfigData, PrinterInfo

router = APIRouter(tags=["printers"])


@router.get("/printers", response_model=Envelope[list[PrinterInfo]])
def list_printers(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[list[PrinterInfo]]:
    printers = service.list_printers()
    return Envelope(ok=True, data=[PrinterInfo(**p) for p in printers])


@router.get("/config", response_model=Envelope[PrinterConfigData])
def get_config(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[PrinterConfigData]:
    config = service.get_printer_config()
    return Envelope(ok=True, data=PrinterConfigData(**config))
