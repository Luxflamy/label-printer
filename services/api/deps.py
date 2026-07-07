"""FastAPI 依赖注入 — 提供单例 LabelPrinterService。

Service 本身无状态（每次调用即时读文件），用 lru_cache 只是避免重复构造对象，
不代表持有连接或其他需要清理的资源。
"""

from __future__ import annotations

from functools import lru_cache

from label_printer.api.service import LabelPrinterService


@lru_cache
def get_service() -> LabelPrinterService:
    return LabelPrinterService()
