"""LabelPrinterService — CLI / FastAPI / 测试共用的唯一编排入口。

依赖方向遵循 docs/ARCHITECTURE.md：
    api/service.py → templates/ + connection/ + config.py

任何新客户端（脚本、自动化、未来的桌面 App）只需依赖这一个类，
不应绕过它直接拼 TSPL 或直接调用 connection/*。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from label_printer.calibration import (
    CalibrationProfile,
    StockSpec,
    build_calibration_job,
    get_calibration_profile,
    list_stock_specs,
    save_calibration_profile,
)
from label_printer.config import CONFIG_DIR, LABELS_DIR, load_printer_config, resolve_dots_per_mm, save_printer_queue
from label_printer.connection import build_connection
from label_printer.connection.cups_raw import list_cups_printers
from label_printer.history import SkuRecord, delete_sku, query_skus, record_sku
from label_printer.templates.loader import list_templates as _list_template_names
from label_printer.templates.loader import load_template
from label_printer.pdf.label_job import build_pdf_label_tspl
from label_printer.pdf.renderer import (
    FitMode,
    SHIPPING_HEIGHT_MM,
    SHIPPING_STOCK_CODE,
    SHIPPING_WIDTH_MM,
    render_pdf_page,
)
from label_printer.tspl.feed_calibration import FeedStrategy, MediaType, build_auto_feed_calibration_bytes
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


class PrinterNotFoundError(ServiceError):
    code = "PRINTER_NOT_FOUND"


class EmptySkuError(ServiceError):
    code = "EMPTY_SKU"


# 自定义小标签默认模板：复用 50×30mm 800P 尺寸基座，仅渲染 SKU
SKU_LABEL_TEMPLATE = "xiaobiaoqian_sku"


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
class PrinterSummary:
    name: str
    status: str
    selected: bool = False


@dataclass
class PrintResult:
    template: str
    copies: int
    queue: str | None


@dataclass
class SkuLabelPrintResult:
    sku: str
    template: str
    copies: int
    queue: str | None
    print_count: int
    first_printed_at: str
    last_printed_at: str


@dataclass
class BatchItemInfo:
    product_id: str
    sku: str
    copies: int
    ok: bool
    error: str | None = None


@dataclass
class CalibrationPreviewResult:
    printer: str
    stock_code: str
    profile: CalibrationProfile
    png_bytes: bytes
    tspl: str
    width_mm: float
    height_mm: float


@dataclass
class AutoFeedResult:
    printer: str
    stock_code: str
    media_type: str
    strategy: str
    tspl: str
    message: str
    test_printed: bool = False


@dataclass
class ShippingLabelPreviewResult:
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
    warnings: list[str]


@dataclass
class ShippingLabelPrintResult:
    pages_printed: int
    copies: int
    queue: str | None
    stock_code: str


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
        history_path: Path | None = None,
    ) -> None:
        self._config_dir = config_dir or CONFIG_DIR
        self._labels_dir = labels_dir or LABELS_DIR
        # None 表示使用 history 模块的默认路径（data/sku_history.json）
        self._history_path = history_path

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

    def get_selected_queue(self) -> str | None:
        config = self.get_printer_config()
        queue = config.get("connection", {}).get("queue")
        return str(queue) if queue else None

    def list_printers_detailed(self) -> list[PrinterSummary]:
        selected = self.get_selected_queue()
        return [
            PrinterSummary(
                name=p["name"],
                status=p["status"],
                selected=p["name"] == selected,
            )
            for p in self.list_printers()
        ]

    def select_printer(self, queue: str) -> str:
        """将选中的 CUPS 队列写回 config/printer.yaml。"""
        known = {p["name"] for p in self.list_printers()}
        if known and queue not in known:
            raise PrinterNotFoundError(f"打印机 '{queue}' 不在本机 CUPS 列表中")
        path = self._config_dir / "printer.yaml"
        save_printer_queue(queue, path)
        return queue

    def get_calibration(
        self, printer: str, stock_code: str
    ) -> CalibrationProfile:
        return get_calibration_profile(
            printer, stock_code, self._config_dir / "calibration.yaml"
        )

    def save_calibration(
        self, printer: str, stock_code: str, profile: CalibrationProfile
    ) -> CalibrationProfile:
        save_calibration_profile(
            printer,
            stock_code,
            profile,
            self._config_dir / "calibration.yaml",
        )
        return profile

    def list_calibration_stocks(self) -> list[StockSpec]:
        return list_stock_specs(self._labels_dir)

    def _label_for_stock(self, stock_code: str) -> dict[str, Any]:
        for spec in list_stock_specs(self._labels_dir):
            if spec.stock_code == stock_code:
                return {
                    "width_mm": spec.width_mm,
                    "height_mm": spec.height_mm,
                    "gap_mm": spec.gap_mm,
                    "direction": spec.direction,
                }
        raise TemplateNotFoundError(f"纸张规格 '{stock_code}' 不存在")

    def _resolve_calibration(
        self, stock_code: str | None, printer: str | None
    ) -> CalibrationProfile | None:
        if not stock_code:
            return None
        queue = printer or self.get_selected_queue()
        if not queue:
            return None
        return self.get_calibration(queue, stock_code)

    def _stock_code_from_template(self, tpl: dict[str, Any]) -> str | None:
        code = tpl.get("meta", {}).get("stock_code")
        return str(code) if code else None

    def render_calibration_preview(
        self,
        printer: str,
        stock_code: str,
        profile: CalibrationProfile,
    ) -> CalibrationPreviewResult:
        try:
            from label_printer.preview.drawer import draw_calibration_png  # noqa: PLC0415
        except ImportError as exc:
            raise ServiceError(
                "预览功能未安装：pip install '.[preview]'"
            ) from exc

        label = self._label_for_stock(stock_code)
        job = build_calibration_job(label, profile)
        tspl = job.build_text()
        png = draw_calibration_png(label, profile)
        return CalibrationPreviewResult(
            printer=printer,
            stock_code=stock_code,
            profile=profile,
            png_bytes=png,
            tspl=tspl,
            width_mm=float(label["width_mm"]),
            height_mm=float(label["height_mm"]),
        )

    def print_calibration_test(
        self,
        printer: str,
        stock_code: str,
        profile: CalibrationProfile,
    ) -> PrintResult:
        label = self._label_for_stock(stock_code)
        data = build_calibration_job(label, profile).build()
        config = self._resolve_config(printer)
        self._send(data, config)
        return PrintResult(template="_calibration", copies=1, queue=printer)

    def auto_feed_calibrate(
        self,
        printer: str,
        stock_code: str,
        media_type: MediaType = "gap",
        strategy: FeedStrategy = "gapdetect",
        print_test_after: bool = False,
        formfeed_after: bool = False,
    ) -> AutoFeedResult:
        """发送传感器校准命令，并按需额外定位到下一张标签起始。"""
        label = self._label_for_stock(stock_code)
        config = self._resolve_config(printer)
        dots_per_mm = resolve_dots_per_mm(config)
        data = build_auto_feed_calibration_bytes(
            label,
            media_type,
            strategy,
            dots_per_mm=dots_per_mm,
            formfeed_after=formfeed_after,
        )
        tspl = data.decode("utf-8")
        self._send(data, config)

        test_printed = False
        if print_test_after:
            profile = self.get_calibration(printer, stock_code)
            self.print_calibration_test(printer, stock_code, profile)
            test_printed = True

        alignment = "，并定位到下一张标签" if formfeed_after else "（省纸模式，不额外走到下一张）"
        if media_type == "blackmark":
            msg = f"已发送黑标传感器校准{alignment}，走纸应在数秒内停止。"
        elif strategy == "autodetect":
            msg = f"已发送自动介质检测{alignment}，走纸应在数秒内停止。"
        else:
            msg = (
                f"已按纸张尺寸发送间隙传感器校准{alignment}，走纸应在数秒内停止。"
                "若红灯闪，请检查间隙纸规格或试 AUTODETECT。"
            )

        return AutoFeedResult(
            printer=printer,
            stock_code=stock_code,
            media_type=media_type,
            strategy=strategy,
            tspl=tspl,
            message=msg,
            test_printed=test_printed,
        )

    def preview_shipping_label(
        self,
        pdf_bytes: bytes,
        page: int = 0,
        fit_mode: FitMode = "contain",
        rotation: int = 0,
        scale: float | None = None,
        printer: str | None = None,
    ) -> ShippingLabelPreviewResult:
        import base64

        from label_printer.pdf.renderer import DEFAULT_PRINT_SCALE

        dots_per_mm = resolve_dots_per_mm(self._resolve_config(printer))
        rendered = render_pdf_page(
            pdf_bytes,
            page_index=page,
            fit_mode=fit_mode,
            rotation=rotation,
            scale=DEFAULT_PRINT_SCALE if scale is None else scale,
            dots_per_mm=dots_per_mm,
        )
        info = rendered.info
        return ShippingLabelPreviewResult(
            page_count=info.page_count,
            page=info.page_index,
            pdf_width_mm=info.pdf_width_mm,
            pdf_height_mm=info.pdf_height_mm,
            target_stock=info.target_stock,
            target_width_mm=info.target_width_mm,
            target_height_mm=info.target_height_mm,
            fit_mode=info.fit_mode,
            rotation=info.rotation,
            scale=info.scale,
            image_b64=base64.b64encode(rendered.preview_png).decode("ascii"),
            warnings=info.warnings,
        )

    def _shipping_calibration(self, printer: str | None) -> CalibrationProfile | None:
        return self._resolve_calibration(SHIPPING_STOCK_CODE, printer)

    def build_shipping_label_tspl(
        self,
        pdf_bytes: bytes,
        page: int = 0,
        fit_mode: FitMode = "contain",
        rotation: int = 0,
        copies: int = 1,
        printer: str | None = None,
        scale: float | None = None,
    ) -> bytes:
        from label_printer.pdf.renderer import DEFAULT_PRINT_SCALE

        dots_per_mm = resolve_dots_per_mm(self._resolve_config(printer))
        rendered = render_pdf_page(
            pdf_bytes,
            page_index=page,
            fit_mode=fit_mode,
            rotation=rotation,
            scale=DEFAULT_PRINT_SCALE if scale is None else scale,
            dots_per_mm=dots_per_mm,
        )
        calibration = self._shipping_calibration(printer)
        return build_pdf_label_tspl(
            rendered.image,
            SHIPPING_WIDTH_MM,
            SHIPPING_HEIGHT_MM,
            calibration=calibration,
            copies=copies,
        )

    def print_shipping_label(
        self,
        pdf_bytes: bytes,
        printer: str | None = None,
        page: int = 0,
        copies: int = 1,
        fit_mode: FitMode = "contain",
        rotation: int = 0,
        print_all_pages: bool = False,
        scale: float | None = None,
    ) -> ShippingLabelPrintResult:
        from label_printer.pdf.renderer import DEFAULT_PRINT_SCALE

        effective_scale = DEFAULT_PRINT_SCALE if scale is None else scale
        dots_per_mm = resolve_dots_per_mm(self._resolve_config(printer))
        if print_all_pages:
            first = render_pdf_page(
                pdf_bytes,
                page_index=0,
                fit_mode=fit_mode,
                rotation=rotation,
                scale=effective_scale,
                dots_per_mm=dots_per_mm,
            )
            page_count = first.info.page_count
            parts: list[bytes] = []
            for idx in range(page_count):
                parts.append(
                    self.build_shipping_label_tspl(
                        pdf_bytes,
                        page=idx,
                        fit_mode=fit_mode,
                        rotation=rotation,
                        copies=copies,
                        printer=printer,
                        scale=effective_scale,
                    )
                )
            data = b"".join(parts)
            pages_printed = page_count
        else:
            data = self.build_shipping_label_tspl(
                pdf_bytes,
                page=page,
                fit_mode=fit_mode,
                rotation=rotation,
                copies=copies,
                printer=printer,
                scale=effective_scale,
            )
            pages_printed = 1

        config = self._resolve_config(printer)
        self._send(data, config)
        return ShippingLabelPrintResult(
            pages_printed=pages_printed,
            copies=copies,
            queue=config.get("connection", {}).get("queue"),
            stock_code=SHIPPING_STOCK_CODE,
        )

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
        self,
        template_name: str,
        variables: dict[str, Any],
        printer: str | None = None,
    ) -> PreviewResult:
        """渲染成 PNG 图像（bytes），供网页预览。需安装 preview 依赖组。"""
        try:
            from label_printer.preview.drawer import draw_label_png  # noqa: PLC0415
        except ImportError as exc:
            raise ServiceError(
                "预览功能未安装：pip install '.[preview]'"
            ) from exc

        tpl = self.get_template(template_name)
        stock_code = self._stock_code_from_template(tpl)
        calibration = self._resolve_calibration(stock_code, printer)
        try:
            png = draw_label_png(tpl, variables, calibration)
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
        self,
        template_name: str,
        variables: dict[str, Any],
        copies: int = 1,
        printer: str | None = None,
    ) -> RenderResult:
        tpl = self.get_template(template_name)
        stock_code = self._stock_code_from_template(tpl)
        calibration = self._resolve_calibration(stock_code, printer)
        try:
            text = render_template_text(
                tpl, variables, copies=copies, calibration=calibration
            )
        except ValueError as exc:
            raise MissingVariablesError(str(exc)) from exc
        return RenderResult(template=template_name, tspl=text, label=tpl.get("label", {}))

    # ---- 打印 -----------------------------------------------------------

    def print_one(
        self,
        template_name: str,
        variables: dict[str, Any],
        copies: int = 1,
        printer: str | None = None,
    ) -> PrintResult:
        tpl = self.get_template(template_name)
        stock_code = self._stock_code_from_template(tpl)
        calibration = self._resolve_calibration(stock_code, printer)
        try:
            data = render_template(tpl, variables, copies=copies, calibration=calibration)
        except ValueError as exc:
            raise MissingVariablesError(str(exc)) from exc

        config = self._resolve_config(printer)
        self._send(data, config)

        conn_cfg = config.get("connection", {})
        return PrintResult(template=template_name, copies=copies, queue=conn_cfg.get("queue"))

    def print_batch(
        self,
        template_name: str,
        items: list[dict[str, Any]],
        printer: str | None = None,
    ) -> BatchResult:
        """合并渲染后一次发送，消除多张之间的卡顿。

        items 每条格式：
            {product_id: str, sku: str, variables: dict[str, str], copies: int}

        渲染失败的条目跳过，其余 TSPL 拼接成一个字节流只调用一次 _send()，
        结束后在 results 中标注每条成功/失败及错误原因。
        """
        tpl = self.get_template(template_name)  # 模板不存在时直接抛 TemplateNotFoundError
        stock_code = self._stock_code_from_template(tpl)
        calibration = self._resolve_calibration(stock_code, printer)

        tspl_parts: list[bytes] = []
        results: list[BatchItemInfo] = []

        for item in items:
            try:
                data = render_template(
                    tpl, item["variables"], copies=item["copies"], calibration=calibration
                )
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
            config = self._resolve_config(printer)
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

    # ---- 自定义 SKU 小标签 -------------------------------------------------

    def print_sku_label(
        self,
        sku: str,
        template_name: str = SKU_LABEL_TEMPLATE,
        copies: int = 1,
        printer: str | None = None,
    ) -> SkuLabelPrintResult:
        """打印一张手工输入的 SKU 小标签，成功后才登记到打印历史。"""
        normalized = sku.strip()
        if not normalized:
            raise EmptySkuError("SKU 不能为空")

        printed = self.print_one(
            template_name, {"sku": normalized}, copies=copies, printer=printer
        )
        record = record_sku(
            normalized, template=template_name, path=self._history_path
        )

        return SkuLabelPrintResult(
            sku=record.sku,
            template=printed.template,
            copies=printed.copies,
            queue=printed.queue,
            print_count=record.print_count,
            first_printed_at=record.first_printed_at,
            last_printed_at=record.last_printed_at,
        )

    def list_sku_history(self, keyword: str = "", limit: int = 20) -> list[SkuRecord]:
        return query_skus(keyword, limit=limit, path=self._history_path)

    def delete_sku_history(self, sku: str) -> bool:
        return delete_sku(sku, path=self._history_path)

    # ---- 内部 -----------------------------------------------------------

    def _resolve_config(self, printer: str | None = None) -> dict[str, Any]:
        config = self.get_printer_config()
        if not printer:
            return config
        resolved = copy.deepcopy(config)
        resolved.setdefault("connection", {})["queue"] = printer
        return resolved

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
