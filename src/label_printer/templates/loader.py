"""从 config/labels/ 加载可组合模板 — 支持 extends 合并。"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from label_printer.config import LABELS_DIR

_TEMPLATE_SEARCH_DIRS = ("templates", "")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """递归合并字典；override 优先。"""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key == "extends":
            continue
        if key == "elements" and "elements_mode" in override and override["elements_mode"] == "replace":
            merged["elements"] = copy.deepcopy(value)
            continue
        if key == "elements_mode":
            continue
        if key == "elements_override":
            merged["elements"] = _apply_element_overrides(
                merged.get("elements", []),
                value,
            )
            continue
        if key == "elements" and isinstance(value, list) and isinstance(merged.get("elements"), list):
            merged["elements"] = merged["elements"] + copy.deepcopy(value)
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _apply_element_overrides(
    elements: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """按 id 覆盖元素字段，未匹配的 override 作为新元素追加。"""
    result = copy.deepcopy(elements)
    index_by_id = {el["id"]: i for i, el in enumerate(result) if "id" in el}

    for override in overrides:
        element_id = override.get("id")
        if element_id and element_id in index_by_id:
            idx = index_by_id[element_id]
            result[idx] = _deep_merge(result[idx], override)
        else:
            result.append(copy.deepcopy(override))
    return result


def _resolve_path(path: Path, labels_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (labels_dir / path).resolve()


def _load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"模板必须是 YAML 映射: {path}")
    return data


def _load_resolved(path: Path, labels_dir: Path, _stack: tuple[Path, ...] = ()) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved in _stack:
        chain = " -> ".join(str(p) for p in _stack + (resolved,))
        raise ValueError(f"模板 extends 循环引用: {chain}")

    raw = _load_yaml_file(resolved)
    extends = raw.get("extends")
    if not extends:
        return raw

    if isinstance(extends, str):
        extends_list = [extends]
    else:
        extends_list = list(extends)

    merged: dict[str, Any] = {}
    for ref in extends_list:
        parent_path = (resolved.parent / ref).resolve()
        if not parent_path.exists():
            parent_path = (labels_dir / ref).resolve()
        if not parent_path.exists():
            raise FileNotFoundError(f"extends 引用的模板不存在: {ref} (from {resolved})")
        parent = _load_resolved(parent_path, labels_dir, _stack + (resolved,))
        merged = _deep_merge(merged, parent)

    return _deep_merge(merged, raw)


def _find_template_path(name: str, labels_dir: Path) -> Path:
    for subdir in _TEMPLATE_SEARCH_DIRS:
        candidate = labels_dir / subdir / f"{name}.yaml" if subdir else labels_dir / f"{name}.yaml"
        if candidate.exists():
            return candidate
    available = list_templates(labels_dir)
    raise FileNotFoundError(f"模板 '{name}' 不存在。可用: {available}")


def list_templates(labels_dir: Path | None = None) -> list[str]:
    """列出可加载的模板名称。"""
    base = labels_dir or LABELS_DIR
    names: set[str] = set()

    templates_dir = base / "templates"
    if templates_dir.is_dir():
        names.update(p.stem for p in templates_dir.glob("*.yaml"))

    for p in base.glob("*.yaml"):
        if not p.name.startswith("_"):
            names.add(p.stem)

    return sorted(names)


def load_template(name: str, labels_dir: Path | None = None) -> dict[str, Any]:
    """加载指定名称的模板，自动解析 extends 链并合并。"""
    base = labels_dir or LABELS_DIR
    path = _find_template_path(name, base)
    return _load_resolved(path, base)


def load_size(name: str, labels_dir: Path | None = None) -> dict[str, Any]:
    """仅加载尺寸规格（sizes/ 目录）。"""
    base = labels_dir or LABELS_DIR
    path = base / "sizes" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"尺寸规格 '{name}' 不存在: {path}")
    return _load_yaml_file(path)


def load_preset(name: str, labels_dir: Path | None = None) -> dict[str, Any]:
    """仅加载排版预设（presets/ 目录）。"""
    base = labels_dir or LABELS_DIR
    path = base / "presets" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"预设 '{name}' 不存在: {path}")
    return _load_yaml_file(path)
