"""Pydantic 请求/响应模型 — 与前端 TypeScript 类型一一对应。

字段命名刻意贴合 label_printer.api.service 的 dataclass / dict 结构，
方便用 model_validate(..., from_attributes=True) 直接转换，避免手写映射代码。
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

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


class RenderData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    template: str
    tspl: str
    label: dict[str, Any]


class PrintRequest(BaseModel):
    template: str
    variables: dict[str, str] = {}
    copies: int = 1


class PreviewRequest(BaseModel):
    template: str
    variables: dict[str, str] = {}


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
