"""标签校准单元测试。"""

from __future__ import annotations

from pathlib import Path

import yaml

from label_printer.calibration import (
    CalibrationProfile,
    build_calibration_job,
    get_calibration_profile,
    list_stock_specs,
    profile_key,
    save_calibration_profile,
)
from label_printer.templates.renderer import render_template_text

LABELS_DIR = Path(__file__).resolve().parents[1] / "config" / "labels"


def test_profile_key_format() -> None:
    assert profile_key("TSC_TE344", "800P") == "TSC_TE344::800P"


def test_save_and_load_calibration_profile(tmp_path: Path) -> None:
    path = tmp_path / "calibration.yaml"
    profile = CalibrationProfile(reference_x_dots=4, reference_y_dots=-2, gap_offset_mm=0.3)
    save_calibration_profile("TSC_TE344", "800P", profile, path)

    loaded = get_calibration_profile("TSC_TE344", "800P", path)
    assert loaded.reference_x_dots == 4
    assert loaded.reference_y_dots == -2
    assert loaded.gap_offset_mm == 0.3


def test_calibration_falls_back_to_default(tmp_path: Path) -> None:
    path = tmp_path / "calibration.yaml"
    path.write_text(
        yaml.dump(
            {
                "default": {"reference_x_dots": 1, "reference_y_dots": 0, "gap_offset_mm": 0.0},
                "profiles": {},
            }
        ),
        encoding="utf-8",
    )
    loaded = get_calibration_profile("OTHER", "800P", path)
    assert loaded.reference_x_dots == 1


def test_build_calibration_job_applies_profile() -> None:
    label = {"width_mm": 50, "height_mm": 30, "gap_mm": 2, "direction": 1}
    profile = CalibrationProfile(reference_x_dots=8, reference_y_dots=-4, gap_offset_mm=0.5)
    text = build_calibration_job(label, profile).build_text()

    assert "REFERENCE 8,-4" in text
    assert "GAP 2 mm,0.5 mm" in text
    assert "BOX" in text
    assert "TL" in text


def test_render_template_applies_calibration() -> None:
    from label_printer.templates.loader import load_template

    tpl = load_template("50x30_800p_product", LABELS_DIR)
    variables = {
        "sku": "BT-Green-Queen",
        "fnsku": "X002J4KZS3",
        "short_title": "Test Title",
    }
    profile = CalibrationProfile(reference_x_dots=10, reference_y_dots=0, gap_offset_mm=0.2)
    text = render_template_text(tpl, variables, calibration=profile)

    assert "REFERENCE 10,0" in text
    assert "GAP 2 mm,0.2 mm" in text


def test_list_stock_specs_includes_known_sizes() -> None:
    specs = list_stock_specs(LABELS_DIR)
    codes = {s.stock_code for s in specs}
    assert "800P" in codes
    assert "250P" in codes
