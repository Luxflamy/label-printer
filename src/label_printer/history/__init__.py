"""打印历史 — 记录并查询已打印过的 SKU。

依赖方向：history/ → config（仅取数据目录），不依赖 templates / tspl / connection，
因此可被 Service、CLI、测试独立复用。
"""

from label_printer.history.sku_history import (
    SkuRecord,
    delete_sku,
    load_history,
    query_skus,
    record_sku,
)

__all__ = [
    "SkuRecord",
    "delete_sku",
    "load_history",
    "query_skus",
    "record_sku",
]
