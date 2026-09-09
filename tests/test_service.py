"""LabelPrinterService 单元测试 — mock 连接层，不测真机。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from label_printer.api.service import (
    ConfigError,
    LabelPrinterService,
    MissingVariablesError,
    PrinterConnectionError,
    TemplateNotFoundError,
)
from label_printer.connection.base import PrinterConnection

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


class FakeConnection(PrinterConnection):
    """真实实现 PrinterConnection 接口的假连接，验证 with 语句触发 connect/close。"""

    def __init__(self, fail_on_send: bool = False) -> None:
        self.connected = False
        self.closed = False
        self.sent: list[bytes] = []
        self._fail_on_send = fail_on_send

    def connect(self) -> None:
        self.connected = True

    def send(self, data: bytes) -> None:
        if self._fail_on_send:
            raise RuntimeError("lp 发送失败")
        self.sent.append(data)

    def close(self) -> None:
        self.closed = True


@pytest.fixture()
def config_dir(tmp_path: Path) -> Path:
    """临时配置目录，避免测试依赖/污染真实 config/printer.yaml。"""
    cfg = {
        "connection": {"type": "cups_raw", "queue": "TSC_TE344", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203},
    }
    (tmp_path / "printer.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return tmp_path


@pytest.fixture()
def service(config_dir: Path) -> LabelPrinterService:
    return LabelPrinterService(config_dir=config_dir, labels_dir=LABELS_DIR)


def test_list_templates_includes_expected_names(service: LabelPrinterService) -> None:
    names = {s.id for s in service.list_templates()}
    assert "xiaobiaoqian" in names
    assert "50x30_800p_product" in names
    assert "100x150_250p_product" in names


def test_list_templates_reports_xiaobiaoqian_as_default(service: LabelPrinterService) -> None:
    summaries = {s.id: s for s in service.list_templates()}
    small = summaries["xiaobiaoqian"]
    assert small.name == "小标签"
    assert small.default is True
    assert small.variables == ["fnsku", "short_title", "sku"]
    assert small.width_mm == 50
    assert small.height_mm == 30
    assert small.stock_code == "800P"


def test_list_templates_puts_xiaobiaoqian_first(service: LabelPrinterService) -> None:
    summaries = service.list_templates()
    assert summaries[0].id == "xiaobiaoqian"
    assert summaries[0].name == "小标签"


def test_list_templates_reports_variables(service: LabelPrinterService) -> None:
    summaries = {s.id: s for s in service.list_templates()}
    compact = summaries["50x30_800p_product"]
    assert compact.variables == ["fnsku", "short_title", "sku"]
    assert compact.width_mm == 50
    assert compact.height_mm == 30
    assert compact.stock_code == "800P"


def test_get_template_unknown_raises_template_not_found(service: LabelPrinterService) -> None:
    with pytest.raises(TemplateNotFoundError):
        service.get_template("does_not_exist")


def test_get_template_detail_includes_variables(service: LabelPrinterService) -> None:
    detail = service.get_template_detail("xiaobiaoqian")
    assert detail["id"] == "xiaobiaoqian"
    assert detail["name"] == "小标签"
    assert detail["variables"] == ["fnsku", "short_title", "sku"]
    assert detail["meta"]["stock_code"] == "800P"
    assert len(detail["elements"]) == 4


def test_render_returns_tspl_text(service: LabelPrinterService) -> None:
    result = service.render(
        "50x30_800p_product",
        {
            "sku": "BT-Green-Queen",
            "fnsku": "X002J4KZS3",
            "short_title": "BESTOUCH DuvetCover SetGreen Queen New",
        },
    )
    assert "SIZE 50" in result.tspl and "30 mm" in result.tspl
    assert result.label["width_mm"] == 50


def test_render_missing_variables_raises(service: LabelPrinterService) -> None:
    with pytest.raises(MissingVariablesError):
        service.render("50x30_800p_product", {"sku": "BT-Green-Queen"})


def test_get_printer_config_missing_file_raises(tmp_path: Path) -> None:
    service = LabelPrinterService(config_dir=tmp_path, labels_dir=LABELS_DIR)
    with pytest.raises(ConfigError):
        service.get_printer_config()


@patch("label_printer.api.service.build_connection")
def test_print_one_sends_rendered_bytes(mock_build_connection: MagicMock, service: LabelPrinterService) -> None:
    fake_conn = FakeConnection()
    mock_build_connection.return_value = fake_conn

    result = service.print_one(
        "50x30_800p_product",
        {
            "sku": "BT-Green-Queen",
            "fnsku": "X002J4KZS3",
            "short_title": "BESTOUCH DuvetCover SetGreen Queen New",
        },
    )

    assert fake_conn.connected is True
    assert fake_conn.closed is True
    assert len(fake_conn.sent) == 1
    assert b"SIZE 50" in fake_conn.sent[0]
    assert b"BARCODE 76," in fake_conn.sent[0]
    assert result.template == "50x30_800p_product"
    assert result.queue == "TSC_TE344"


@patch("label_printer.api.service.build_connection")
def test_print_one_connection_failure_raises_printer_connection_error(
    mock_build_connection: MagicMock, service: LabelPrinterService
) -> None:
    mock_build_connection.return_value = FakeConnection(fail_on_send=True)

    with pytest.raises(PrinterConnectionError):
        service.print_one(
            "50x30_800p_product",
            {
                "sku": "BT-Green-Queen",
                "fnsku": "X002J4KZS3",
                "short_title": "BESTOUCH DuvetCover SetGreen Queen New",
            },
        )


@patch("label_printer.api.service.build_connection")
def test_print_raw_sends_given_bytes(mock_build_connection: MagicMock, service: LabelPrinterService) -> None:
    fake_conn = FakeConnection()
    mock_build_connection.return_value = fake_conn

    service.print_raw("SIZE 40 mm,30 mm\r\nPRINT 1\r\n")

    assert fake_conn.sent == [b"SIZE 40 mm,30 mm\r\nPRINT 1\r\n"]


@patch("label_printer.api.service.build_connection")
def test_auto_feed_uses_printer_dpi_and_skips_formfeed_by_default(
    mock_build_connection: MagicMock,
    service: LabelPrinterService,
) -> None:
    fake_conn = FakeConnection()
    mock_build_connection.return_value = fake_conn

    result = service.auto_feed_calibrate("TSC_TE344", "800P")

    assert b"GAPDETECT 240,16\r\n" in fake_conn.sent[0]
    assert b"FORMFEED" not in fake_conn.sent[0]
    assert "省纸模式" in result.message


def test_list_printers_returns_list(service: LabelPrinterService) -> None:
    # 不 mock，直接调用真实 lpstat；仅断言返回类型正确，不依赖具体打印机
    printers = service.list_printers()
    assert isinstance(printers, list)
