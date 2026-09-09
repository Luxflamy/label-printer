"""已打印 SKU 历史 — 纯存储与查询，不涉及渲染或打印。

写入采用「临时文件 + 原子替换」，避免连续打印时把 JSON 写坏。
文件不存在或内容损坏时一律降级为空历史，不影响打印主流程。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from label_printer.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "sku_history.json"


@dataclass(frozen=True)
class SkuRecord:
    sku: str
    first_printed_at: str
    last_printed_at: str
    print_count: int
    last_template: str | None = None

    @classmethod
    def from_dict(cls, sku: str, data: dict[str, Any]) -> SkuRecord:
        timestamp = str(data.get("last_printed_at", ""))
        return cls(
            sku=sku,
            first_printed_at=str(data.get("first_printed_at", timestamp)),
            last_printed_at=timestamp,
            print_count=int(data.get("print_count", 1)),
            last_template=data.get("last_template"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_printed_at": self.first_printed_at,
            "last_printed_at": self.last_printed_at,
            "print_count": self.print_count,
            "last_template": self.last_template,
        }


def _now_iso(now: datetime | None = None) -> str:
    current = now or datetime.now().astimezone()
    return current.isoformat(timespec="seconds")


def load_history(path: Path | None = None) -> dict[str, SkuRecord]:
    """读取全部历史；文件缺失或格式异常时返回空字典。"""
    file_path = path or HISTORY_FILE
    if not file_path.exists():
        return {}

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}

    return {
        str(sku): SkuRecord.from_dict(str(sku), entry)
        for sku, entry in raw.items()
        if isinstance(entry, dict)
    }


def _save_history(records: dict[str, SkuRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {sku: record.to_dict() for sku, record in records.items()}
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(tmp_path, path)


def record_sku(
    sku: str,
    template: str | None = None,
    path: Path | None = None,
    now: datetime | None = None,
) -> SkuRecord:
    """登记一次打印；已存在则累加次数并刷新最后打印时间。"""
    normalized = sku.strip()
    if not normalized:
        raise ValueError("SKU 不能为空")

    file_path = path or HISTORY_FILE
    records = load_history(file_path)
    timestamp = _now_iso(now)
    existing = records.get(normalized)

    if existing is None:
        record = SkuRecord(
            sku=normalized,
            first_printed_at=timestamp,
            last_printed_at=timestamp,
            print_count=1,
            last_template=template,
        )
    else:
        record = SkuRecord(
            sku=normalized,
            first_printed_at=existing.first_printed_at,
            last_printed_at=timestamp,
            print_count=existing.print_count + 1,
            last_template=template or existing.last_template,
        )

    records[normalized] = record
    _save_history(records, file_path)
    return record


def query_skus(
    keyword: str = "",
    limit: int = 20,
    path: Path | None = None,
) -> list[SkuRecord]:
    """按子串匹配查询历史，最近打印的排在前面。limit <= 0 表示不限制。"""
    records = list(load_history(path or HISTORY_FILE).values())

    kw = keyword.strip().lower()
    if kw:
        records = [r for r in records if kw in r.sku.lower()]

    records.sort(key=lambda r: (r.last_printed_at, r.sku), reverse=True)
    return records if limit <= 0 else records[:limit]


def delete_sku(sku: str, path: Path | None = None) -> bool:
    """删除一条历史记录；不存在时返回 False。"""
    file_path = path or HISTORY_FILE
    records = load_history(file_path)
    if sku not in records:
        return False
    del records[sku]
    _save_history(records, file_path)
    return True
