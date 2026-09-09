"""已打印 SKU 历史单元测试。"""

from datetime import datetime, timedelta, timezone

import pytest

from label_printer.history import (
    delete_sku,
    load_history,
    query_skus,
    record_sku,
)

_BASE = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)


def _history_file(tmp_path):
    return tmp_path / "sku_history.json"


def test_load_history_missing_file_returns_empty(tmp_path) -> None:
    assert load_history(_history_file(tmp_path)) == {}


def test_load_history_corrupt_file_returns_empty(tmp_path) -> None:
    path = _history_file(tmp_path)
    path.write_text("{ not json", encoding="utf-8")
    assert load_history(path) == {}


def test_record_sku_creates_and_persists(tmp_path) -> None:
    path = _history_file(tmp_path)
    record = record_sku("BT-Green-Queen", template="xiaobiaoqian_sku", path=path, now=_BASE)

    assert record.print_count == 1
    assert record.first_printed_at == record.last_printed_at
    assert record.last_template == "xiaobiaoqian_sku"

    reloaded = load_history(path)
    assert list(reloaded) == ["BT-Green-Queen"]
    assert reloaded["BT-Green-Queen"].print_count == 1


def test_record_sku_increments_and_keeps_first_time(tmp_path) -> None:
    path = _history_file(tmp_path)
    record_sku("SKU-A", path=path, now=_BASE)
    second = record_sku("SKU-A", path=path, now=_BASE + timedelta(hours=2))

    assert second.print_count == 2
    assert second.first_printed_at < second.last_printed_at


def test_record_sku_trims_whitespace_and_rejects_blank(tmp_path) -> None:
    path = _history_file(tmp_path)
    record_sku("  SKU-B  ", path=path, now=_BASE)
    assert "SKU-B" in load_history(path)

    with pytest.raises(ValueError):
        record_sku("   ", path=path)


def test_query_skus_orders_by_last_printed_desc(tmp_path) -> None:
    path = _history_file(tmp_path)
    record_sku("OLD-SKU", path=path, now=_BASE)
    record_sku("NEW-SKU", path=path, now=_BASE + timedelta(days=1))

    assert [r.sku for r in query_skus(path=path)] == ["NEW-SKU", "OLD-SKU"]


def test_query_skus_filters_case_insensitively(tmp_path) -> None:
    path = _history_file(tmp_path)
    record_sku("BT-Green-Queen", path=path, now=_BASE)
    record_sku("MM-Blue-King", path=path, now=_BASE)

    assert [r.sku for r in query_skus("green", path=path)] == ["BT-Green-Queen"]
    assert query_skus("nope", path=path) == []


def test_query_skus_respects_limit(tmp_path) -> None:
    path = _history_file(tmp_path)
    for idx in range(5):
        record_sku(f"SKU-{idx}", path=path, now=_BASE + timedelta(minutes=idx))

    assert len(query_skus(limit=2, path=path)) == 2
    assert len(query_skus(limit=0, path=path)) == 5


def test_delete_sku(tmp_path) -> None:
    path = _history_file(tmp_path)
    record_sku("SKU-X", path=path, now=_BASE)

    assert delete_sku("SKU-X", path=path) is True
    assert load_history(path) == {}
    assert delete_sku("SKU-X", path=path) is False
