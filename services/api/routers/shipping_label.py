"""PDF 运货标签 — 拖入 PDF 预览与打印。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from label_printer.api.service import LabelPrinterService
from services.api.deps import get_service
from services.api.schemas import Envelope, ShippingLabelPreviewData, ShippingLabelPrintData

from label_printer.pdf.renderer import DEFAULT_PRINT_SCALE, MAX_PRINT_SCALE, MIN_PRINT_SCALE

router = APIRouter(prefix="/shipping-label", tags=["shipping-label"])

MAX_UPLOAD = 20 * 1024 * 1024


def _parse_scale(raw: str | float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_PRINT_SCALE
    return max(MIN_PRINT_SCALE, min(MAX_PRINT_SCALE, value))


async def _read_pdf(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise ValueError(f"PDF 超过大小限制（最大 {MAX_UPLOAD // (1024 * 1024)}MB）")
    return data


@router.post("/preview", response_model=Envelope[ShippingLabelPreviewData])
async def preview_shipping_label(
    file: UploadFile = File(...),
    page: int = Form(0),
    fit_mode: str = Form("contain"),
    rotation: int = Form(0),
    scale: float = Form(DEFAULT_PRINT_SCALE),
    printer: str | None = Form(None),
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[ShippingLabelPreviewData]:
    pdf_bytes = await _read_pdf(file)
    mode = fit_mode if fit_mode in ("contain", "cover", "fill") else "contain"
    rot = rotation if rotation in (0, 90, 180, 270) else 0
    result = service.preview_shipping_label(
        pdf_bytes,
        page=page,
        fit_mode=mode,
        rotation=rot,
        scale=_parse_scale(scale),
        printer=printer,
    )  # type: ignore[arg-type]
    return Envelope(ok=True, data=ShippingLabelPreviewData.model_validate(result))


@router.post("/print", response_model=Envelope[ShippingLabelPrintData])
async def print_shipping_label(
    file: UploadFile = File(...),
    page: int = Form(0),
    copies: int = Form(1),
    fit_mode: str = Form("contain"),
    rotation: int = Form(0),
    scale: float = Form(DEFAULT_PRINT_SCALE),
    printer: str | None = Form(None),
    print_all_pages: bool = Form(False),
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[ShippingLabelPrintData]:
    pdf_bytes = await _read_pdf(file)
    mode = fit_mode if fit_mode in ("contain", "cover", "fill") else "contain"
    rot = rotation if rotation in (0, 90, 180, 270) else 0
    copies_n = max(1, min(copies, 99))
    result = service.print_shipping_label(
        pdf_bytes,
        printer=printer,
        page=page,
        copies=copies_n,
        fit_mode=mode,  # type: ignore[arg-type]
        rotation=rot,
        print_all_pages=print_all_pages,
        scale=_parse_scale(scale),
    )
    return Envelope(ok=True, data=ShippingLabelPrintData.model_validate(result))
