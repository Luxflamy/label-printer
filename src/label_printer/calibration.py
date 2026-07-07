"""标签校准配置 — 按「打印机队列 + 纸张规格」存储 REFERENCE / GAP 偏移。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from label_printer.config import CONFIG_DIR, LABELS_DIR
from label_printer.tspl.commands import LabelJob


@dataclass(frozen=True)
class CalibrationProfile:
    reference_x_dots: int = 0
    reference_y_dots: int = 0
    gap_offset_mm: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CalibrationProfile:
        if not data:
            return cls()
        return cls(
            reference_x_dots=int(data.get("reference_x_dots", 0)),
            reference_y_dots=int(data.get("reference_y_dots", 0)),
            gap_offset_mm=float(data.get("gap_offset_mm", 0.0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_x_dots": self.reference_x_dots,
            "reference_y_dots": self.reference_y_dots,
            "gap_offset_mm": self.gap_offset_mm,
        }


@dataclass(frozen=True)
class StockSpec:
    stock_code: str
    name: str
    width_mm: float
    height_mm: float
    gap_mm: float
    direction: int


def profile_key(queue: str, stock_code: str) -> str:
    return f"{queue}::{stock_code}"


def load_calibration(path: Path | None = None) -> dict[str, Any]:
    config_path = path or (CONFIG_DIR / "calibration.yaml")
    if not config_path.exists():
        return {"default": CalibrationProfile().to_dict(), "profiles": {}}
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {"default": CalibrationProfile().to_dict(), "profiles": {}}
    return data


def save_calibration_profile(
    queue: str,
    stock_code: str,
    profile: CalibrationProfile,
    path: Path | None = None,
) -> dict[str, Any]:
    config_path = path or (CONFIG_DIR / "calibration.yaml")
    data = load_calibration(config_path)
    profiles = data.setdefault("profiles", {})
    profiles[profile_key(queue, stock_code)] = profile.to_dict()
    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    return data


def get_calibration_profile(
    queue: str,
    stock_code: str,
    path: Path | None = None,
) -> CalibrationProfile:
    data = load_calibration(path)
    profiles = data.get("profiles", {})
    key = profile_key(queue, stock_code)
    if key in profiles:
        return CalibrationProfile.from_dict(profiles[key])
    return CalibrationProfile.from_dict(data.get("default"))


def list_stock_specs(labels_dir: Path | None = None) -> list[StockSpec]:
    base = labels_dir or LABELS_DIR
    sizes_dir = base / "sizes"
    specs: list[StockSpec] = []
    if not sizes_dir.is_dir():
        return specs
    for path in sorted(sizes_dir.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        meta = raw.get("meta", {})
        label = raw.get("label", {})
        stock_code = meta.get("stock_code")
        if not stock_code:
            continue
        specs.append(
            StockSpec(
                stock_code=str(stock_code),
                name=str(meta.get("description", stock_code)),
                width_mm=float(label["width_mm"]),
                height_mm=float(label["height_mm"]),
                gap_mm=float(label.get("gap_mm", 2)),
                direction=int(label.get("direction", 1)),
            )
        )
    return specs


def build_calibration_job(
    label: dict[str, Any],
    profile: CalibrationProfile,
    dots_per_mm: int = 8,
) -> LabelJob:
    """生成校准测试页 TSPL：边框、四角标记、中心十字与尺寸文字。"""
    width_mm = float(label["width_mm"])
    height_mm = float(label["height_mm"])
    gap_mm = float(label.get("gap_mm", 2))
    direction = int(label.get("direction", 1))

    job = LabelJob(
        width_mm=width_mm,
        height_mm=height_mm,
        gap_mm=gap_mm,
        direction=direction,
        dots_per_mm=dots_per_mm,
        reference=(profile.reference_x_dots, profile.reference_y_dots),
        gap_offset_mm=profile.gap_offset_mm,
    )

    inset = 1.0
    job.box(inset, inset, width_mm - inset, height_mm - inset, thickness=2)
    job.box(width_mm / 2 - 5, height_mm / 2, width_mm / 2 + 5, height_mm / 2, thickness=2)
    job.box(width_mm / 2, height_mm / 2 - 5, width_mm / 2, height_mm / 2 + 5, thickness=2)

    job.text(2, 2, "TL", font="1")
    job.text(width_mm - 8, 2, "TR", font="1")
    job.text(2, height_mm - 4, "BL", font="1")
    job.text(width_mm - 8, height_mm - 4, "BR", font="1")

    size_text = f"{width_mm:g}x{height_mm:g}mm"
    job.text(width_mm / 2 - 6, height_mm / 2 + 3, size_text, font="1")

    ref_text = f"REF {profile.reference_x_dots},{profile.reference_y_dots}"
    job.text(2, height_mm / 2 - 2, ref_text, font="1")
    gap_text = f"GAP+{profile.gap_offset_mm:g}mm"
    job.text(2, height_mm / 2 + 1, gap_text, font="1")

    return job
