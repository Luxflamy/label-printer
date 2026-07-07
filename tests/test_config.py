"""配置加载测试。"""

from label_printer.config import resolve_dots_per_mm


def test_resolve_dots_per_mm_prefers_explicit() -> None:
    assert resolve_dots_per_mm({"printer": {"dpi": 203, "dots_per_mm": 12}}) == 12


def test_resolve_dots_per_mm_from_dpi() -> None:
    assert resolve_dots_per_mm({"printer": {"dpi": 300}}) == 12
    assert resolve_dots_per_mm({"printer": {"dpi": 203}}) == 8
