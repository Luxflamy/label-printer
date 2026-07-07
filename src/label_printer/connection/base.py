"""连接抽象接口 — 阶段 1 实现。"""

from __future__ import annotations

from abc import ABC, abstractmethod


class PrinterConnection(ABC):
    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def send(self, data: bytes) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def __enter__(self) -> PrinterConnection:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
