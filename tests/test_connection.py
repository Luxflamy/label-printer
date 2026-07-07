"""连接层单元测试 — mock 系统命令，不测真机。"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from label_printer.connection import build_connection
from label_printer.connection.cups_raw import CupsRawConnection, list_cups_printers
from label_printer.connection.usb_serial import UsbSerialConnection


def test_build_connection_cups_raw() -> None:
    conn = build_connection({"connection": {"type": "cups_raw", "queue": "TSC_TE344"}})
    assert isinstance(conn, CupsRawConnection)
    assert conn.queue == "TSC_TE344"


def test_build_connection_usb_serial() -> None:
    conn = build_connection(
        {"connection": {"type": "usb_serial", "port": "/dev/cu.usbserial-1410"}}
    )
    assert isinstance(conn, UsbSerialConnection)
    assert conn.port == "/dev/cu.usbserial-1410"
    assert conn.baudrate == 9600


def test_build_connection_missing_queue_raises() -> None:
    with pytest.raises(ValueError, match="queue"):
        build_connection({"connection": {"type": "cups_raw"}})


def test_build_connection_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="未知的连接类型"):
        build_connection({"connection": {"type": "carrier_pigeon"}})


@patch("label_printer.connection.cups_raw.shutil.which", return_value="/usr/bin/lp")
@patch("label_printer.connection.cups_raw.subprocess.run")
def test_cups_raw_send_success(mock_run: MagicMock, _mock_which: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b"", stderr=b""
    )
    conn = CupsRawConnection(queue="TSC_TE344")
    conn.connect()
    conn.send(b"SIZE 50 mm,30 mm\r\n")
    conn.close()

    mock_run.assert_called_once()
    args = mock_run.call_args.args[0]
    assert args == ["lp", "-d", "TSC_TE344", "-o", "raw"]


@patch("label_printer.connection.cups_raw.shutil.which", return_value="/usr/bin/lp")
@patch("label_printer.connection.cups_raw.subprocess.run")
def test_cups_raw_send_failure_raises(mock_run: MagicMock, _mock_which: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"", stderr=b"printer-not-found"
    )
    conn = CupsRawConnection(queue="MISSING")
    conn.connect()
    with pytest.raises(RuntimeError, match="printer-not-found"):
        conn.send(b"data")


def test_cups_raw_send_without_connect_raises() -> None:
    conn = CupsRawConnection(queue="TSC_TE344")
    with pytest.raises(RuntimeError, match="连接未打开"):
        conn.send(b"data")


@patch("label_printer.connection.cups_raw.shutil.which", return_value=None)
def test_cups_raw_connect_without_lp_raises(_mock_which: MagicMock) -> None:
    conn = CupsRawConnection(queue="TSC_TE344")
    with pytest.raises(RuntimeError, match="lp"):
        conn.connect()


@patch("label_printer.connection.cups_raw.shutil.which", return_value="/usr/bin/lpstat")
@patch("label_printer.connection.cups_raw.subprocess.run")
def test_list_cups_printers_parses_english_output(
    mock_run: MagicMock, _mock_which: MagicMock
) -> None:
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout="TSC_TE344\n", stderr=""),
        subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="printer TSC_TE344 is idle.  enabled since Mon Jul  6 19:07:22 2026\n",
            stderr="",
        ),
    ]
    printers = list_cups_printers()
    assert printers == [{"name": "TSC_TE344", "status": "idle"}]


@patch("label_printer.connection.cups_raw.shutil.which", return_value="/usr/bin/lpstat")
@patch("label_printer.connection.cups_raw.subprocess.run")
def test_list_cups_printers_parses_localized_output(
    mock_run: MagicMock, _mock_which: MagicMock
) -> None:
    """macOS 中文系统下 lpstat -p 输出本地化文本，仍需正确识别队列名与状态。"""
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout="TSC_TE344\n", stderr=""),
        subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="打印机TSC_TE344闲置，启用时间始于Mon Jul  6 19:18:30 2026\n",
            stderr="",
        ),
    ]
    printers = list_cups_printers()
    assert printers == [{"name": "TSC_TE344", "status": "idle"}]


@patch("label_printer.connection.cups_raw.shutil.which", return_value="/usr/bin/lpstat")
@patch("label_printer.connection.cups_raw.subprocess.run")
def test_list_cups_printers_no_printers_returns_empty(
    mock_run: MagicMock, _mock_which: MagicMock
) -> None:
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    assert list_cups_printers() == []


def test_context_manager_calls_connect_and_close() -> None:
    with patch.object(CupsRawConnection, "connect") as mock_connect, patch.object(
        CupsRawConnection, "close"
    ) as mock_close:
        with CupsRawConnection(queue="TSC_TE344"):
            pass
        mock_connect.assert_called_once()
        mock_close.assert_called_once()
