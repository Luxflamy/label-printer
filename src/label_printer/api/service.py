"""LabelPrinterService — CLI / FastAPI / 测试共用的唯一编排入口。

依赖方向遵循 docs/ARCHITECTURE.md：
    api/service.py → templates/ + connection/ + config.py

任何新客户端（脚本、自动化、未来的桌面 App）只需依赖这一个类，
不应绕过它直接拼 TSPL 或直接调用 connection/*。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from label_printer.config import CONFIG_DIR, LABELS_DIR, load_printer_config
from label_printer.connection import build_connection
from label_printer.connection.cups_raw import list_cups_printers
from label_printer.templates.loader import list_templates as _list_template_names
from label_printer.templates.loader import load_template
from label_printer.templates.renderer import (
    extract_variables,
    render_template,
    render_template_text,
)


class ServiceError(Exception):
    """所有 Service 层错误的基类，携带机器可读 code，便于 API 层映射 HTTP 状态码。"""

    code = "SERVICE_ERROR"


class TemplateNotFoundError(ServiceError):
    code = "TEMPLATE_NOT_FOUND"


class MissingVariablesError(ServiceError):
    code = "MISSING_VARIABLES"


class PrinterConnectionError(ServiceError):
    code = "PRINTER_CONNECTION_ERROR"


class ConfigError(ServiceError):
    code = "CONFIG_ERROR"


@dataclass
class TemplateSummary:
    """模板列表页所需的摘要信息（不含完整 elements）。"""

    id: str
    name: str
    description: str
    width_mm: float
    height_mm: float
    stock_code: str | None
    variables: list[str]
    default: bool = False


@dataclass
class RenderResult:
    template: str
    tspl: str
    label: dict[str, Any]


@dataclass
class PreviewResult:
    template: str
    png_bytes: bytes
    width_mm: float
    height_mm: float


@dataclass
class PrintResult:
    template: str
    copies: int
    queue: str | None


@dataclass
class BatchItemInfo:
    product_id: str
    sku: str
    copies: int
    ok: bool
    error: str | None = None


@dataclass
class BatchResult:
    total: int
    succeeded: int
    failed: int
    results: list[BatchItemInfo]


class LabelPrinterService:
    """无状态编排层：每次调用即时读取配置/模板，不缓存连接，方便多客户端复用。"""

    def __init__(
        self,
        config_dir: Path | None = None,
        labels_dir: Path | None = None,
    ) -> None:
        self._config_dir = config_dir or CONFIG_DIR
        self._labels_dir = labels_dir or LABELS_DIR

    # ---- 配置 ---------------------------------------------------------

    def get_printer_config(self) -> dict[str, Any]:
        path = self._config_dir / "printer.yaml"
        try:
            return load_printer_config(path)
        except FileNotFoundError as exc:
            raise ConfigError(str(exc)) from exc

    # ---- 打印机发现 -----------------------------------------------------

    def list_printers(self) -> list[dict[str, str]]:
        """当前仅支持 CUPS 队列发现；未来可在此合并 usb_serial 的 discover 结果。"""
        return list_cups_printers()

    # ---- 模板 -----------------------------------------------------------

    def list_templates(self) -> list[TemplateSummary]:
        summaries: list[TemplateSummary] = []
        for name in _list_template_names(self._labels_dir):
            tpl = load_template(name, self._labels_dir)
            label = tpl.get("label", {})
            meta = tpl.get("meta", {})
            summaries.append(
                TemplateSummary(
                    id=name,
                    name=tpl.get("name", name),
                    description=tpl.get("description", ""),
                    width_mm=label.get("width_mm", 0),
                    height_mm=label.get("height_mm", 0),
                    stock_code=meta.get("stock_code"),
                    variables=sorted(extract_variables(tpl)),
                    default=bool(meta.get("default", False)),
                )
            )
        summaries.sort(key=lambda s: (0 if s.id == "xiaobiaoqian" else 1, s.id))
        return summaries

    def get_template(self, name: str) -> dict[str, Any]:
        try:
            return load_template(name, self._labels_dir)
        except FileNotFoundError as exc:
            raise TemplateNotFoundError(str(exc)) from exc

    def get_template_detail(self, name: str) -> dict[str, Any]:
        """供 API/前端使用：附带已解析的变量列表，供动态生成表单。"""
        tpl = self.get_template(name)
        return {
            "id": name,
            "name": tpl.get("name", name),
            "description": tpl.get("description", ""),
            "label": tpl.get("label", {}),
            "elements": tpl.get("elements", []),
            "meta": tpl.get("meta", {}),
            "variables": sorted(extract_variables(tpl)),
        }

    # ---- 渲染（不打印，供预览使用） ----------------------------------------

    def render_preview_image(
        self, template_name: str, variables: dict[str, Any]
    ) -> PreviewResult:
        """渲染成 PNG 图像（bytes），供网页预览。需安装 preview 依赖组。"""
        try:
            from label_printer.preview.drawer import draw_label_png  # noqa: PLC0415
        except ImportError as exc:
            raise ServiceError(
                "预览功能未安装：pip install '.[preview]'"
            ) from exc

        tpl = self.get_template(template_name)
        try:
            png = draw_label_png(tpl, variables)
        except ValueError as exc:
            raise MissingVariablesError(str(exc)) from exc

        label = tpl.get("label", {})
        return PreviewResult(
            template=template_name,
            png_bytes=png,
            width_mm=float(label.get("width_mm", 0)),
            height_mm=float(label.get("height_mm", 0)),
        )

    def render(
        self, template_name: str, variables: dict[str, Any], copies: int = 1
    ) -> RenderResult:
        tpl = self.get_template(template_name)
        try:
            text = render_template_text(tpl, variables, copies=copies)
        except ValueError as exc:
            raise MissingVariablesError(str(exc)) from exc
        return RenderResult(template=template_name, tspl=text, label=tpl.get("label", {}))

    # ---- 打印 -----------------------------------------------------------

    def print_one(
        self, template_name: str, variables: dict[str, Any], copies: int = 1
    ) -> PrintResult:
        tpl = self.get_template(template_name)
        try:
            data = render_template(tpl, variables, copies=copies)
        except ValueError as exc:
            raise MissingVariablesError(str(exc)) from exc

        config = self.get_printer_config()
        self._send(data, config)

        conn_cfg = config.get("connection", {})
        return PrintResult(template=template_name, copies=copies, queue=conn_cfg.get("queue"))

    def print_batch(
        self,
        template_name: str,
        items: list[dict[str, Any]],
    ) -> BatchResult:
        """合并渲染后一次发送，消除多张之间的卡顿。

        items 每条格式：
            {product_id: str, sku: str, variables: dict[str, str], copies: int}

        渲染失败的条目跳过，其余 TSPL 拼接成一个字节流只调用一次 _send()，
        结束后在 results 中标注每条成功/失败及错误原因。
        """
        tpl = self.get_template(template_name)  # 模板不存在时直接抛 TemplateNotFoundError

        tspl_parts: list[bytes] = []
        results: list[BatchItemInfo] = []

        for item in items:
            try:
                data = render_template(tpl, item["variables"], copies=item["copies"])
                tspl_parts.append(data)
                results.append(
                    BatchItemInfo(
                        product_id=item["product_id"],
                        sku=item["sku"],
                        copies=item["copies"],
                        ok=True,
                    )
                )
            except ValueError as exc:
                results.append(
                    BatchItemInfo(
                        product_id=item["product_id"],
                        sku=item["sku"],
                        copies=item["copies"],
                        ok=False,
                        error=str(exc),
                    )
                )

        if tspl_parts:
            combined = b"".join(tspl_parts)
            config = self.get_printer_config()
            self._send(combined, config)  # 连接失败时抛 PrinterConnectionError

        succeeded = sum(1 for r in results if r.ok)
        return BatchResult(
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )

    def print_raw(self, tspl: str | bytes, config: dict[str, Any] | None = None) -> None:
        data = tspl.encode("utf-8") if isinstance(tspl, str) else tspl
        cfg = config or self.get_printer_config()
        self._send(data, cfg)

    # ---- 内部 -----------------------------------------------------------

    def _send(self, data: bytes, config: dict[str, Any]) -> None:
        try:
            connection = build_connection(config)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc

        try:
            with connection:
                connection.send(data)
        except RuntimeError as exc:
            raise PrinterConnectionError(str(exc)) from exc
