"""Pydantic 请求/响应模型 — 与前端 TypeScript 类型一一对应。

字段命名刻意贴合 label_printer.api.service 的 dataclass / dict 结构，
方便用 model_validate(..., from_attributes=True) 直接转换，避免手写映射代码。
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str
    message: str


class Envelope(BaseModel, Generic[T]):
    """统一响应信封：成功时 data 有值，失败时 error 有值。"""

    ok: bool
    data: T | None = None
    error: ErrorInfo | None = None


class HealthData(BaseModel):
    status: str = "ok"
    service: str = "label-printer-api"


class PrinterInfo(BaseModel):
    name: str
    status: str
    selected: bool = False


class PrinterListData(BaseModel):
    printers: list[PrinterInfo]
    selected_queue: str | None = None


class SelectPrinterRequest(BaseModel):
    queue: str


class PrinterConfigData(BaseModel):
    connection: dict[str, Any]
    printer: dict[str, Any] = {}


class TemplateSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    width_mm: float
    height_mm: float
    stock_code: str | None = None
    variables: list[str]
    default: bool = False


class TemplateDetailSchema(BaseModel):
    id: str
    name: str
    description: str = ""
    label: dict[str, Any]
    elements: list[dict[str, Any]]
    meta: dict[str, Any] = {}
    variables: list[str]


class RenderRequest(BaseModel):
    template: str
    variables: dict[str, str] = {}
    copies: int = 1
    printer: str | None = None


class RenderData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template: str
    tspl: str
    label: dict[str, Any]


class PrintRequest(BaseModel):
    template: str
    variables: dict[str, str] = {}
    copies: int = 1
    printer: str | None = None


class PreviewRequest(BaseModel):
    template: str
    variables: dict[str, str] = {}
    printer: str | None = None


class PreviewData(BaseModel):
    template: str
    image_b64: str
    width_mm: float
    height_mm: float


class PrintData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template: str
    copies: int
    queue: str | None = None


# ---- 商品数据 --------------------------------------------------------------

class ProductItem(BaseModel):
    """商品库 JSON 单条记录，映射到前端 ProductItem 类型。"""

    id: str
    sku: str
    fnsku: str
    short_title: str
    product_name: str
    qty: int


class ProductStoreSummary(BaseModel):
    id: str
    name: str
    product_count: int


class ProductStoresData(BaseModel):
    stores: list[ProductStoreSummary]
    default_store: str | None = None


# ---- 批量打印 --------------------------------------------------------------

class BatchItem(BaseModel):
    """打印队列中的单个条目：商品 ID + 份数。"""

    product_id: str
    copies: int = 1


class BatchPrintRequest(BaseModel):
    template: str
    store: str | None = None
    printer: str | None = None
    items: list[BatchItem]


class BatchItemResult(BaseModel):
    product_id: str
    sku: str
    copies: int
    ok: bool
    error: str | None = None


class BatchPrintData(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BatchItemResult]


# ---- 校准 --------------------------------------------------------------

class CalibrationProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference_x_dots: int = 0
    reference_y_dots: int = 0
    gap_offset_mm: float = 0.0


class StockSpecSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_code: str
    name: str
    width_mm: float
    height_mm: float
    gap_mm: float
    direction: int


class CalibrationData(BaseModel):
    printer: str
    stock_code: str
    profile: CalibrationProfileSchema


class CalibrationStocksData(BaseModel):
    stocks: list[StockSpecSchema]


class CalibrationPreviewRequest(BaseModel):
    printer: str
    stock_code: str
    profile: CalibrationProfileSchema


class CalibrationPreviewData(BaseModel):
    printer: str
    stock_code: str
    profile: CalibrationProfileSchema
    image_b64: str
    tspl: str
    width_mm: float
    height_mm: float


class CalibrationSaveRequest(BaseModel):
    printer: str
    stock_code: str
    profile: CalibrationProfileSchema


class CalibrationPrintRequest(BaseModel):
    printer: str
    stock_code: str
    profile: CalibrationProfileSchema


class AutoFeedRequest(BaseModel):
    printer: str
    stock_code: str
    media_type: Literal["gap", "blackmark"] = "gap"
    strategy: Literal["gapdetect", "autodetect"] = "gapdetect"
    print_test_after: bool = False


class AutoFeedData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    printer: str
    stock_code: str
    media_type: str
    strategy: str
    tspl: str
    message: str
    test_printed: bool = False


class ShippingLabelPreviewData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_count: int
    page: int
    pdf_width_mm: float
    pdf_height_mm: float
    target_stock: str
    target_width_mm: float
    target_height_mm: float
    fit_mode: str
    rotation: int
    scale: float
    image_b64: str
    warnings: list[str] = []


class ShippingLabelPrintData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pages_printed: int
    copies: int
    queue: str | None = None
    stock_code: str
