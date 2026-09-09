"""自定义 SKU 小标签编排测试 — mock 连接层，历史写入临时目录。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from PIL import Image

from label_printer.api.service import (
    SKU_LABEL_TEMPLATE,
    EmptySkuError,
    LabelPrinterService,
    PrinterConnectionError,
)
from label_printer.connection.base import PrinterConnection
from label_printer.templates.loader import load_template
from label_printer.tspl.bitmap import render_text_bitmap

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


class FakeConnection(PrinterConnection):
    def __init__(self, fail_on_send: bool = False) -> None:
        self.sent: list[bytes] = []
        self._fail_on_send = fail_on_send

    def connect(self) -> None:
        pass

    def send(self, data: bytes) -> None:
        if self._fail_on_send:
            raise RuntimeError("lp 发送失败")
        self.sent.append(data)

    def close(self) -> None:
        pass


@pytest.fixture()
def service(tmp_path: Path) -> LabelPrinterService:
    cfg = {
        "connection": {"type": "cups_raw", "queue": "TSC_TE344", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203, "dots_per_mm": 8},
    }
    (tmp_path / "printer.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return LabelPrinterService(
        config_dir=tmp_path,
        labels_dir=LABELS_DIR,
        history_path=tmp_path / "sku_history.json",
    )


def _sku_bitmap(sku: str) -> Image.Image:
    """按模板实际参数渲染 SKU 位图（203dpi → 8 dots/mm）。"""
    tpl = load_template(SKU_LABEL_TEMPLATE, LABELS_DIR)
    element = next(el for el in tpl["elements"] if el["id"] == "sku")
    return render_text_bitmap(
        sku,
        width_dots=round(float(element["width_mm"]) * 8),
        height_dots=round(float(element["height_mm"]) * 8),
        font_size_dots=round(float(element["font_size_mm"]) * 8),
    )


def _ink_rows(image: Image.Image) -> list[int]:
    pixels = image.load()
    width, height = image.size
    return [y for y in range(height) if any(pixels[x, y] == 0 for x in range(width))]


@pytest.mark.parametrize(
    "sku", ["MM-01", "BT-Green-Queen", "BT-Soft-Duvet-Queen-Grey"]
)
def test_sku_bitmap_never_clips(sku: str) -> None:
    """任意长度 SKU 都靠自动缩小字号完整显示，四边不得触到画布边缘。"""
    image = _sku_bitmap(sku)
    pixels = image.load()
    width, height = image.size

    assert not any(pixels[0, y] == 0 for y in range(height)), "左边缘被裁切"
    assert not any(pixels[width - 1, y] == 0 for y in range(height)), "右边缘被裁切"
    assert _ink_rows(image), "位图没有任何墨点"


def test_sku_bitmap_uses_bigger_font_for_shorter_sku() -> None:
    """同一画布下短 SKU 的字应明显更高——这就是「尽可能大」的体现。"""
    short_height = len(_ink_rows(_sku_bitmap("MM-01")))
    long_height = len(_ink_rows(_sku_bitmap("BT-Soft-Duvet-Queen-Grey")))
    assert short_height > long_height * 2


def test_sku_template_needs_only_sku(service: LabelPrinterService) -> None:
    summary = next(s for s in service.list_templates() if s.id == SKU_LABEL_TEMPLATE)
    assert summary.variables == ["sku"]
    assert summary.stock_code == "800P"
    assert summary.default is False


@patch("label_printer.api.service.build_connection")
def test_print_sku_label_sends_tspl_and_records(
    mock_build_connection: MagicMock, service: LabelPrinterService
) -> None:
    fake = FakeConnection()
    mock_build_connection.return_value = fake

    result = service.print_sku_label("BT-Green-Queen", copies=2)

    assert result.sku == "BT-Green-Queen"
    assert result.copies == 2
    assert result.print_count == 1
    # SKU 走 bitmap_text，TSPL 里是固定几何的位图而非明文：
    # x=2mm(16 dots), y=3mm(24 dots), 46 字节宽(368 dots), 24mm 高(192 dots)
    assert b"BITMAP 16,24,46,192,0," in fake.sent[0]
    assert b"PRINT 2" in fake.sent[0]
    # 打印过的 SKU 立即可查
    assert [r.sku for r in service.list_sku_history()] == ["BT-Green-Queen"]


@patch("label_printer.api.service.build_connection")
def test_print_sku_label_accumulates_count(
    mock_build_connection: MagicMock, service: LabelPrinterService
) -> None:
    mock_build_connection.return_value = FakeConnection()

    service.print_sku_label("SKU-A")
    second = service.print_sku_label("SKU-A")

    assert second.print_count == 2
    assert len(service.list_sku_history()) == 1


@patch("label_printer.api.service.build_connection")
def test_print_sku_label_does_not_record_on_send_failure(
    mock_build_connection: MagicMock, service: LabelPrinterService
) -> None:
    mock_build_connection.return_value = FakeConnection(fail_on_send=True)

    with pytest.raises(PrinterConnectionError):
        service.print_sku_label("SKU-FAIL")

    assert service.list_sku_history() == []


def test_print_sku_label_rejects_blank(service: LabelPrinterService) -> None:
    with pytest.raises(EmptySkuError):
        service.print_sku_label("   ")


@patch("label_printer.api.service.build_connection")
def test_sku_history_search_and_delete(
    mock_build_connection: MagicMock, service: LabelPrinterService
) -> None:
    mock_build_connection.return_value = FakeConnection()

    service.print_sku_label("BT-Green-Queen")
    service.print_sku_label("MM-Blue-King")

    assert [r.sku for r in service.list_sku_history("green")] == ["BT-Green-Queen"]
    assert service.delete_sku_history("BT-Green-Queen") is True
    assert [r.sku for r in service.list_sku_history()] == ["MM-Blue-King"]
    assert service.delete_sku_history("BT-Green-Queen") is False
