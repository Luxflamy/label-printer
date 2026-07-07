"""标签校准 — 按打印机 + 纸张规格读写偏移并试打。"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, Query

from label_printer.api.service import LabelPrinterService
from label_printer.calibration import CalibrationProfile
from services.api.deps import get_service
from services.api.schemas import (
    AutoFeedData,
    AutoFeedRequest,
    CalibrationData,
    CalibrationPreviewData,
    CalibrationPreviewRequest,
    CalibrationPrintRequest,
    CalibrationProfileSchema,
    CalibrationSaveRequest,
    CalibrationStocksData,
    Envelope,
    PrintData,
    StockSpecSchema,
)

router = APIRouter(prefix="/calibration", tags=["calibration"])


def _profile_schema(profile: CalibrationProfile) -> CalibrationProfileSchema:
    return CalibrationProfileSchema.model_validate(profile, from_attributes=True)


@router.get("/stocks", response_model=Envelope[CalibrationStocksData])
def list_stocks(
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[CalibrationStocksData]:
    stocks = [StockSpecSchema.model_validate(s) for s in service.list_calibration_stocks()]
    return Envelope(ok=True, data=CalibrationStocksData(stocks=stocks))


@router.get("", response_model=Envelope[CalibrationData])
def get_calibration(
    printer: str = Query(...),
    stock_code: str = Query(..., alias="stock"),
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[CalibrationData]:
    profile = service.get_calibration(printer, stock_code)
    return Envelope(
        ok=True,
        data=CalibrationData(
            printer=printer,
            stock_code=stock_code,
            profile=_profile_schema(profile),
        ),
    )


@router.put("", response_model=Envelope[CalibrationData])
def save_calibration(
    req: CalibrationSaveRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[CalibrationData]:
    profile = CalibrationProfile.from_dict(req.profile.model_dump())
    saved = service.save_calibration(req.printer, req.stock_code, profile)
    return Envelope(
        ok=True,
        data=CalibrationData(
            printer=req.printer,
            stock_code=req.stock_code,
            profile=_profile_schema(saved),
        ),
    )


@router.post("/preview", response_model=Envelope[CalibrationPreviewData])
def preview_calibration(
    req: CalibrationPreviewRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[CalibrationPreviewData]:
    profile = CalibrationProfile.from_dict(req.profile.model_dump())
    result = service.render_calibration_preview(req.printer, req.stock_code, profile)
    b64 = base64.b64encode(result.png_bytes).decode("ascii")
    return Envelope(
        ok=True,
        data=CalibrationPreviewData(
            printer=result.printer,
            stock_code=result.stock_code,
            profile=_profile_schema(result.profile),
            image_b64=b64,
            tspl=result.tspl,
            width_mm=result.width_mm,
            height_mm=result.height_mm,
        ),
    )


@router.post("/auto-feed", response_model=Envelope[AutoFeedData])
def auto_feed_calibrate(
    req: AutoFeedRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[AutoFeedData]:
    result = service.auto_feed_calibrate(
        req.printer,
        req.stock_code,
        media_type=req.media_type,
        strategy=req.strategy,
        print_test_after=req.print_test_after,
    )
    return Envelope(ok=True, data=AutoFeedData.model_validate(result))


@router.post("/print", response_model=Envelope[PrintData])
def print_calibration(
    req: CalibrationPrintRequest,
    service: LabelPrinterService = Depends(get_service),
) -> Envelope[PrintData]:
    profile = CalibrationProfile.from_dict(req.profile.model_dump())
    result = service.print_calibration_test(req.printer, req.stock_code, profile)
    return Envelope(ok=True, data=PrintData.model_validate(result))
