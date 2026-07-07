"""加载 config/printer.yaml 等配置。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
LABELS_DIR = CONFIG_DIR / "labels"


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
