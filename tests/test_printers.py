"""打印机选择与配置持久化测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import yaml
import pytest

from label_printer.api.service import LabelPrinterService, PrinterNotFoundError
from label_printer.config import load_printer_config, save_printer_queue

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


def test_save_printer_queue_updates_yaml(tmp_path: Path) -> None:
    cfg = {
        "connection": {"type": "cups_raw", "queue": "OLD_QUEUE", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203},
    }
    path = tmp_path / "printer.yaml"
    path.write_text(yaml.dump(cfg), encoding="utf-8")

    updated = save_printer_queue("NEW_QUEUE", path)
    assert updated["connection"]["queue"] == "NEW_QUEUE"

    reloaded = load_printer_config(path)
    assert reloaded["connection"]["queue"] == "NEW_QUEUE"
    assert reloaded["printer"]["model"] == "TE344"


@patch("label_printer.api.service.list_cups_printers")
def test_select_printer_persists_to_config(
    mock_list: patch,
    tmp_path: Path,
) -> None:
    mock_list.return_value = [
        {"name": "TSC_TE344", "status": "idle"},
        {"name": "PDF_Writer", "status": "idle"},
    ]
    cfg = {
        "connection": {"type": "cups_raw", "queue": "TSC_TE344", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203},
    }
    (tmp_path / "printer.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    service = LabelPrinterService(config_dir=tmp_path, labels_dir=LABELS_DIR)
    service.select_printer("PDF_Writer")

    reloaded = load_printer_config(tmp_path / "printer.yaml")
    assert reloaded["connection"]["queue"] == "PDF_Writer"


@patch("label_printer.api.service.list_cups_printers")
def test_select_unknown_printer_raises(mock_list: patch, tmp_path: Path) -> None:
    mock_list.return_value = [{"name": "TSC_TE344", "status": "idle"}]
    cfg = {
        "connection": {"type": "cups_raw", "queue": "TSC_TE344", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203},
    }
    (tmp_path / "printer.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    service = LabelPrinterService(config_dir=tmp_path, labels_dir=LABELS_DIR)
    with pytest.raises(PrinterNotFoundError):
        service.select_printer("NO_SUCH_PRINTER")


@patch("label_printer.api.service.list_cups_printers")
def test_list_printers_detailed_marks_selected(mock_list: patch, tmp_path: Path) -> None:
    mock_list.return_value = [
        {"name": "TSC_TE344", "status": "idle"},
        {"name": "PDF_Writer", "status": "printing"},
    ]
    cfg = {
        "connection": {"type": "cups_raw", "queue": "PDF_Writer", "timeout": 10},
        "printer": {"model": "TE344", "dpi": 203},
    }
    (tmp_path / "printer.yaml").write_text(yaml.dump(cfg), encoding="utf-8")

    service = LabelPrinterService(config_dir=tmp_path, labels_dir=LABELS_DIR)
    summaries = service.list_printers_detailed()

    assert len(summaries) == 2
    assert summaries[0].selected is False
    assert summaries[1].selected is True
    assert summaries[1].status == "printing"
