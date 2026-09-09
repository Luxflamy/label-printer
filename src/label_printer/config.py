"""加载 config/printer.yaml 等配置。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
LABELS_DIR = CONFIG_DIR / "labels"
DATA_DIR = PROJECT_ROOT / "data"


def load_printer_config(path: Path | None = None) -> dict[str, Any]:
    """加载打印机连接配置。默认读取 config/printer.yaml。"""
    config_path = path or (CONFIG_DIR / "printer.yaml")
    if not config_path.exists():
        example = CONFIG_DIR / "printer.example.yaml"
        raise FileNotFoundError(
            f"未找到 {config_path}，请复制 {example} 为 printer.yaml 并填写 USB 端口"
        )
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_dots_per_mm(config: dict[str, Any]) -> int:
    """从 printer.yaml 解析每毫米点数（优先 dots_per_mm，否则由 dpi 推算）。"""
    printer = config.get("printer") or {}
    if printer.get("dots_per_mm") is not None:
        return int(printer["dots_per_mm"])
    dpi = int(printer.get("dpi", 203))
    return max(1, round(dpi / 25.4))


def save_printer_queue(queue: str, path: Path | None = None) -> dict[str, Any]:
    """更新 printer.yaml 中的 CUPS 队列名并写回磁盘。"""
    config_path = path or (CONFIG_DIR / "printer.yaml")
    config = load_printer_config(config_path)
    connection = config.setdefault("connection", {})
    connection["queue"] = queue
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    return config
