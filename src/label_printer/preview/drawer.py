"""标签预览图绘制 — 模板 + 变量 → PNG bytes。

设计原则：
- 与打印共用 templates/renderer.build_label_job() 和 tspl/layout.resolve_x_mm()，
  保证预览坐标与实打一致。
- 纯函数，无副作用，无 I/O，方便单测。
- 预览分辨率取 SCREEN_DPI（96），缩放因子 SCALE 使图像在屏幕上清晰。
"""

from __future__ import annotations

import io
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from label_printer.calibration import CalibrationProfile
from label_printer.templates.renderer import build_label_job, validate_variables
from label_printer.tspl.constants import DOTS_PER_MM
from label_printer.tspl.layout import (
    FONT_CHAR_WIDTH_DOTS,
    estimate_barcode_width_dots,
    estimate_qrcode_width_dots,
    resolve_x_mm,
)
from label_printer.utils.units import mm_to_dots

# --- 渲染参数 ---------------------------------------------------------------

# 1 mm = DOTS_PER_MM dots（203 dpi），预览图按 SCALE 倍放大便于屏幕查看
SCALE = 3  # 3x → 1mm ≈ 24px，50×30mm → 1500×900px 左右

BG_COLOR = (255, 255, 255)       # 标签底色
BORDER_COLOR = (160, 160, 160)   # 标签边框
BORDER_PX = 2
TEXT_COLOR = (30, 30, 30)
BARCODE_COLOR = (0, 0, 0)


# TSC 内置字体在 203 dpi 下的字符高度（dots）
FONT_CHAR_HEIGHT_DOTS: dict[str, int] = {
    "1": 8, "2": 16, "3": 24, "4": 32, "5": 40,
    "6": 14, "7": 21, "8": 14,
}


def _px(mm: float) -> int:
    """mm → 预览像素。"""
    return int(round(mm * DOTS_PER_MM * SCALE))


def _font_size_px(font_key: str, y_mul: int = 1) -> int:
    height_dots = FONT_CHAR_HEIGHT_DOTS.get(font_key, 24)
    return max(8, height_dots * y_mul * SCALE)


def _get_pil_font(size_px: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/Library/Fonts/Courier New.ttf", size_px)
    except OSError:
        pass
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size_px)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_barcode_image(
    content: str,
    symbology: str,
    bar_height_mm: float,
    human_readable: bool,
    max_width_px: int = 9999,
) -> Image.Image:
    """生成条码图像，缩放到 fit-inside(max_width_px, target_h_px) 后返回。

    python-barcode 的 module_width 单位是 mm；用 96dpi + module_width=1.5mm
    确保每模块 ≥ 5px，然后将生成结果等比 fit-inside 缩放。
    """
    try:
        import barcode as bc
        from barcode.writer import ImageWriter
    except ImportError as exc:
        raise ImportError("预览功能需要 python-barcode：pip install python-barcode") from exc

    sym_upper = symbology.upper().replace("-", "")
    code_cls_name = {
        "128": "Code128", "CODE128": "Code128",
        "39": "Code39", "CODE39": "Code39",
        "EAN13": "EAN13", "EAN8": "EAN8",
        "UPCA": "UPCA",
    }.get(sym_upper, "Code128")

    try:
        code_cls = bc.get_barcode_class(code_cls_name)
    except Exception:
        code_cls = bc.get_barcode_class("Code128")

    target_h_px = _px(bar_height_mm)
    render_dpi = 96
    module_w_mm = 1.5   # 96dpi: 1mm ≈ 3.78px → 1.5mm ≈ 5.7px，安全
    gen_height_mm = 10.0
    text_distance = 2.0 if human_readable else 0.0

    buf = io.BytesIO()
    try:
        writer = ImageWriter()
        code_obj = code_cls(content, writer=writer)
        code_obj.write(buf, options={
            "module_width": module_w_mm,
            "module_height": gen_height_mm,
            "quiet_zone": 1.0,
            "write_text": human_readable,
            "font_size": 9 if human_readable else 0,
            "text_distance": text_distance,
            "dpi": render_dpi,
        })
    except Exception:
        raise  # 调用方捕获并降级到占位框

    buf.seek(0)
    img = Image.open(buf).convert("RGB")

    # 裁掉 python-barcode 的空白边框
    gray = img.convert("L")
    bbox = gray.getbbox()
    if bbox:
        img = img.crop(bbox)

    # fit-inside 缩放：不超过 (max_width_px, target_h_px)，保持纵横比
    orig_w, orig_h = img.size
    if orig_h > 0 and orig_w > 0:
        scale = min(target_h_px / orig_h, max_width_px / orig_w)
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)

    return img


def _draw_qrcode_image(content: str, cell_width: int, error_correction: str) -> Image.Image:
    try:
        import qrcode  # type: ignore[import]
        from qrcode.constants import (  # type: ignore[import]
            ERROR_CORRECT_H,
            ERROR_CORRECT_L,
            ERROR_CORRECT_M,
            ERROR_CORRECT_Q,
        )
    except ImportError as exc:
        raise ImportError("预览功能需要 qrcode：pip install qrcode[pil]") from exc

    ec_map = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M,
              "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
    ec = ec_map.get(error_correction.upper(), ERROR_CORRECT_M)
    box_size = max(1, cell_width * SCALE // 2)

    qr = qrcode.QRCode(error_correction=ec, box_size=box_size, border=0)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("L")
    return img


def _align_x_px(align: str, container_w: int, item_w: int, fallback_x: int = 0) -> int:
    """按 align 计算水平粘贴/绘制起点（像素）。"""
    if align == "center":
        return (container_w - item_w) // 2
    if align == "right":
        return max(0, container_w - item_w)
    return fallback_x


def draw_label_png(
    template: dict[str, Any],
    variables: dict[str, Any],
    calibration: CalibrationProfile | None = None,
) -> bytes:
    """主入口：模板 + 变量 → PNG bytes（内存，不写文件）。"""
    validate_variables(template, variables)

    label = template.get("label", {})
    width_mm = float(label["width_mm"])
    height_mm = float(label["height_mm"])
    width_px = _px(width_mm)
    height_px = _px(height_mm)

    ref_x_mm = 0.0
    ref_y_mm = 0.0
    if calibration is not None:
        ref_x_mm = calibration.reference_x_dots / DOTS_PER_MM
        ref_y_mm = calibration.reference_y_dots / DOTS_PER_MM

    img = Image.new("RGB", (width_px, height_px), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 标签边框
    draw.rectangle(
        [BORDER_PX, BORDER_PX, width_px - BORDER_PX - 1, height_px - BORDER_PX - 1],
        outline=BORDER_COLOR,
        width=BORDER_PX,
    )

    from label_printer.templates.renderer import _substitute  # noqa: PLC0415

    for element in template.get("elements", []):
        el_type = element.get("type")
        raw_content = element.get("content", "")
        content = _substitute(raw_content, variables) if raw_content else raw_content

        x_mm = resolve_x_mm(element, content, width_mm) + ref_x_mm
        y_mm = float(element.get("y_mm", 0)) + ref_y_mm
        x_px = _px(x_mm)
        y_px = _px(y_mm)

        if el_type == "text":
            font_key = str(element.get("font", "3"))
            x_mul = int(element.get("x_mul", 1))
            y_mul = int(element.get("y_mul", 1))
            size_px = _font_size_px(font_key, max(x_mul, y_mul))
            pil_font = _get_pil_font(size_px)
            align = element.get("align", "left")
            # 用 PIL 实测宽度居中，避免估算字体与屏幕字体不一致导致偏左
            bbox = draw.textbbox((0, 0), content, font=pil_font)
            text_w = bbox[2] - bbox[0]
            text_x = _align_x_px(align, width_px, text_w, x_px)
            draw.text((text_x, y_px), content, fill=TEXT_COLOR, font=pil_font)

        elif el_type == "barcode":
            height_mm_bar = float(element.get("height_mm", 10))
            human_readable = bool(element.get("human_readable", True))
            symbology = str(element.get("symbology", "128"))
            try:
                bc_img = _draw_barcode_image(
                    content, symbology, height_mm_bar, human_readable, max_width_px=width_px
                )
                # 预览图知道真实渲染宽度，直接用真实宽度居中
                align = element.get("align", "left")
                paste_x = _align_x_px(align, width_px, bc_img.width, x_px)
                img.paste(bc_img, (paste_x, y_px))
            except Exception:
                fw = _px(min(40, width_mm - float(element.get("x_mm", 0)) - 2))
                fh = _px(height_mm_bar)
                draw.rectangle(
                    [x_px, y_px, x_px + fw, y_px + fh],
                    outline=BARCODE_COLOR, width=2,
                )
                draw.text((x_px + 4, y_px + 4), content[:12], fill=TEXT_COLOR,
                          font=_get_pil_font(12))

        elif el_type == "qrcode":
            cell_width = int(element.get("cell_width", 4))
            error_correction = str(element.get("error_correction", "M"))
            try:
                qr_img = _draw_qrcode_image(content, cell_width, error_correction)
                align = element.get("align", "left")
                paste_x = _align_x_px(align, width_px, qr_img.width, x_px)
                img.paste(qr_img.convert("RGB"), (paste_x, y_px))
            except Exception:
                side = estimate_qrcode_width_dots(content, cell_width) * SCALE // DOTS_PER_MM
                draw.rectangle([x_px, y_px, x_px + side, y_px + side],
                                outline=BARCODE_COLOR, width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def draw_calibration_png(
    label: dict[str, Any],
    profile: CalibrationProfile,
) -> bytes:
    """校准测试页预览 — 与 build_calibration_job 布局一致。"""
    width_mm = float(label["width_mm"])
    height_mm = float(label["height_mm"])
    width_px = _px(width_mm)
    height_px = _px(height_mm)

    ref_x_mm = profile.reference_x_dots / DOTS_PER_MM
    ref_y_mm = profile.reference_y_dots / DOTS_PER_MM

    img = Image.new("RGB", (width_px, height_px), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle(
        [BORDER_PX, BORDER_PX, width_px - BORDER_PX - 1, height_px - BORDER_PX - 1],
        outline=BORDER_COLOR,
        width=BORDER_PX,
    )

    inset = 1.0
    ix1, iy1 = _px(inset + ref_x_mm), _px(inset + ref_y_mm)
    ix2, iy2 = _px(width_mm - inset + ref_x_mm), _px(height_mm - inset + ref_y_mm)
    draw.rectangle([ix1, iy1, ix2, iy2], outline=BARCODE_COLOR, width=2)

    cx = width_mm / 2 + ref_x_mm
    cy = height_mm / 2 + ref_y_mm
    draw.line([_px(cx - 5), _px(cy), _px(cx + 5), _px(cy)], fill=BARCODE_COLOR, width=2)
    draw.line([_px(cx), _px(cy - 5), _px(cx), _px(cy + 5)], fill=BARCODE_COLOR, width=2)

    font = _get_pil_font(_font_size_px("1"))
    for text, x_mm, y_mm in (
        ("TL", 2, 2),
        ("TR", width_mm - 8, 2),
        ("BL", 2, height_mm - 4),
        ("BR", width_mm - 8, height_mm - 4),
        (f"{width_mm:g}x{height_mm:g}mm", width_mm / 2 - 6, height_mm / 2 + 3),
        (f"REF {profile.reference_x_dots},{profile.reference_y_dots}", 2, height_mm / 2 - 2),
        (f"GAP+{profile.gap_offset_mm:g}mm", 2, height_mm / 2 + 1),
    ):
        draw.text((_px(x_mm + ref_x_mm), _px(y_mm + ref_y_mm)), text, fill=TEXT_COLOR, font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
