"""USB 串口直连 — 阶段 1 实现（pyserial）。"""

from __future__ import annotations

from label_printer.connection.base import PrinterConnection


class UsbSerialConnection(PrinterConnection):
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 5.0,
        write_delay_ms: int = 50,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_delay_ms = write_delay_ms
        self._serial = None

    def connect(self) -> None:
        raise NotImplementedError("阶段 1：使用 pyserial 打开 self.port")

    def send(self, data: bytes) -> None:
        raise NotImplementedError("阶段 1：写入串口")

    def close(self) -> None:
        raise NotImplementedError("阶段 1：关闭串口")
