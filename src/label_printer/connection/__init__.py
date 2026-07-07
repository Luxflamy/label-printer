"""打印机连接层 — 只负责字节流收发，不含 TSPL / 模板业务逻辑。

对外统一入口是 build_connection(config)：按 config/printer.yaml 的
connection.type 选择具体实现，上层（printer.py / api/service.py）
只依赖 PrinterConnection 接口，不关心底层是 CUPS 还是串口。
"""

from __future__ import annotations

from typing import Any

from label_printer.connection.base import PrinterConnection
from label_printer.connection.cups_raw import CupsRawConnection
from label_printer.connection.usb_serial import UsbSerialConnection

__all__ = [
    "PrinterConnection",
    "CupsRawConnection",
    "UsbSerialConnection",
    "build_connection",
]


def build_connection(config: dict[str, Any]) -> PrinterConnection:
    """根据 printer.yaml 的 connection 段构建对应连接实例。"""
    conn_cfg = config.get("connection", {})
    conn_type = conn_cfg.get("type", "cups_raw")

    if conn_type == "cups_raw":
        queue = conn_cfg.get("queue")
        if not queue:
            raise ValueError("connection.type=cups_raw 时必须配置 connection.queue")
        return CupsRawConnection(
            queue=queue,
            timeout=conn_cfg.get("timeout", 10.0),
        )

    if conn_type == "usb_serial":
        port = conn_cfg.get("port")
        if not port:
            raise ValueError("connection.type=usb_serial 时必须配置 connection.port")
        return UsbSerialConnection(
            port=port,
            baudrate=conn_cfg.get("baudrate", 9600),
            timeout=conn_cfg.get("timeout", 5.0),
            write_delay_ms=conn_cfg.get("write_delay_ms", 50),
        )

    raise ValueError(f"未知的连接类型: {conn_type!r}（支持 cups_raw / usb_serial）")
