"""FastAPI 应用入口 — 仅本机监听，供 apps/web 调用。

启动方式（见 scripts/dev.sh）：
    .venv/bin/uvicorn services.api.main:app --port 8765 --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from label_printer.api.service import ServiceError
from services.api.routers import batch_print, calibration, health, print_job, printers, products, shipping_label, templates
from services.api.schemas import Envelope, ErrorInfo

_ERROR_STATUS: dict[str, int] = {
    "TEMPLATE_NOT_FOUND": 404,
    "MISSING_VARIABLES": 422,
    "CONFIG_ERROR": 500,
    "PRINTER_CONNECTION_ERROR": 502,
    "PRINTER_NOT_FOUND": 404,
    "PDF_ERROR": 422,
    "SERVICE_ERROR": 500,
}

app = FastAPI(title="Label Printer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    status_code = _ERROR_STATUS.get(exc.code, 500)
    envelope = Envelope(ok=False, error=ErrorInfo(code=exc.code, message=str(exc)))
    return JSONResponse(status_code=status_code, content=envelope.model_dump())




@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError) -> JSONResponse:
    envelope = Envelope(ok=False, error=ErrorInfo(code="PDF_ERROR", message=str(exc)))
    return JSONResponse(status_code=422, content=envelope.model_dump())


app.include_router(health.router)
app.include_router(printers.router)
app.include_router(calibration.router)
app.include_router(shipping_label.router)
app.include_router(templates.router)
app.include_router(print_job.router)
app.include_router(products.router)
app.include_router(batch_print.router)
