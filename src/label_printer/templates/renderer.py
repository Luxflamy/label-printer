"""模板变量渲染 — 将 loader 解析好的模板 + 业务变量 转换为 TSPL。

依赖方向：templates/ → tspl/（符合 docs/ARCHITECTURE.md 约定）
不涉及连接/打印，纯函数，便于单测和"仅预览"场景复用。
"""

from __future__ import annotations

import re
from typing import Any

from label_printer.calibration import CalibrationProfile
from label_printer.tspl.commands import LabelJob
from label_printer.tspl.layout import resolve_x_mm

_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")

_ELEMENT_BUILDERS: dict[str, str] = {
    "text": "text",
    "barcode": "barcode",
    "qrcode": "qrcode",
}


def extract_variables(template: dict[str, Any]) -> set[str]:
    """提取模板中所有 {{ variable }} 占位符名称。"""
    names: set[str] = set()
    for element in template.get("elements", []):
        content = element.get("content")
        if isinstance(content, str):
            names.update(_VAR_PATTERN.findall(content))
    return names


def _substitute(text: str, variables: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(key)
        return str(variables[key])

    return _VAR_PATTERN.sub(repl, text)


def validate_variables(template: dict[str, Any], variables: dict[str, Any]) -> None:
    """变量缺失时抛出清晰错误，供 Service/API 层捕获后转为友好提示。"""
    required = extract_variables(template)
    missing = sorted(required - variables.keys())
    if missing:
        raise ValueError(f"缺少模板变量: {missing}")


def _font_mul(value: Any) -> int:
    """TSPL TEXT 的 x_mul/y_mul 仅支持 1–10 整数。"""
    return max(1, min(10, round(float(value))))


def build_label_job(
    template: dict[str, Any],
    variables: dict[str, Any],
    calibration: CalibrationProfile | None = None,
) -> LabelJob:
    """按模板 elements 构建 LabelJob，不落地为 bytes（供需要复用 job 的场景）。"""
    validate_variables(template, variables)

    label = template.get("label", {})
    label_width_mm = float(label["width_mm"])
    reference = (0, 0)
    gap_offset_mm = 0.0
    if calibration is not None:
        reference = (calibration.reference_x_dots, calibration.reference_y_dots)
        gap_offset_mm = calibration.gap_offset_mm

    job = LabelJob(
        width_mm=label_width_mm,
        height_mm=label["height_mm"],
        gap_mm=label.get("gap_mm", 2),
        gap_offset_mm=gap_offset_mm,
        direction=label.get("direction", 1),
        reference=reference,
    )

    for element in template.get("elements", []):
        el_type = element.get("type")
        if el_type not in _ELEMENT_BUILDERS:
            raise ValueError(f"不支持的元素类型: {el_type!r}")

        raw_content = element.get("content", "")
        content = _substitute(raw_content, variables) if raw_content else raw_content
        x_mm = resolve_x_mm(element, content, label_width_mm)

        if el_type == "text":
            job.text(
                x_mm=x_mm,
                y_mm=element["y_mm"],
                content=content,
                font=element.get("font", "3"),
                rotation=element.get("rotation", 0),
                x_mul=_font_mul(element.get("x_mul", 1)),
                y_mul=_font_mul(element.get("y_mul", 1)),
            )
        elif el_type == "barcode":
            job.barcode(
                x_mm=x_mm,
                y_mm=element["y_mm"],
                content=content,
                symbology=element.get("symbology", "128"),
                height_mm=element.get("height_mm", 10),
                human_readable=element.get("human_readable", True),
                rotation=element.get("rotation", 0),
                narrow=element.get("narrow", 2),
                wide=element.get("wide", 4),
            )
        elif el_type == "qrcode":
            job.qrcode(
                x_mm=x_mm,
                y_mm=element["y_mm"],
                content=content,
                error_correction=element.get("error_correction", "M"),
                cell_width=element.get("cell_width", 4),
                mode=element.get("mode", "A"),
                rotation=element.get("rotation", 0),
            )

    return job


def render_template(
    template: dict[str, Any],
    variables: dict[str, Any],
    copies: int = 1,
    calibration: CalibrationProfile | None = None,
) -> bytes:
    """将模板与变量合并，输出 TSPL bytes（可直接发送给连接层）。"""
    return build_label_job(template, variables, calibration).build(copies=copies)


def render_template_text(
    template: dict[str, Any],
    variables: dict[str, Any],
    copies: int = 1,
    calibration: CalibrationProfile | None = None,
) -> str:
    """同 render_template，但返回可读文本，供预览接口使用。"""
    return build_label_job(template, variables, calibration).build_text(copies=copies)
