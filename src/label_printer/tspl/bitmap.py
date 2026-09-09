"""单色位图 → TSPL BITMAP 命令数据。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class BitmapPayload:
    width_bytes: int
    height_dots: int
    data: bytes


_CJK_FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)


def load_cjk_font(
    size_px: int,
    font_path: str | None = None,
) -> ImageFont.FreeTypeFont:
    """加载可打印中文的字体；不将系统字体复制进项目。"""
    candidates = (font_path,) if font_path else _CJK_FONT_CANDIDATES
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            return ImageFont.truetype(candidate, size_px)
        except OSError:
            continue
    raise RuntimeError("未找到中文字体，请安装 Noto Sans CJK 或在模板中配置 font_path")


def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    stroke_width: int,
) -> tuple[int, int, tuple[int, int, int, int]]:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox


def _wrap_text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    stroke_width: int,
) -> list[str]:
    """按空格折行；超宽单词再按字符切开。"""
    content = " ".join(text.split())
    if not content:
        return [""]

    words = content.split(" ")
    lines: list[str] = []
    current = ""

    def fits(candidate: str) -> bool:
        width, _, _ = _measure_text(draw, candidate, font, stroke_width)
        return width <= max_width

    def split_word(word: str) -> list[str]:
        parts: list[str] = []
        chunk = ""
        for ch in word:
            trial = chunk + ch
            if chunk and not fits(trial):
                parts.append(chunk)
                chunk = ch
            else:
                chunk = trial
        if chunk:
            parts.append(chunk)
        return parts or [word]

    for word in words:
        pieces = split_word(word) if not fits(word) else [word]
        for piece in pieces:
            trial = piece if not current else f"{current} {piece}"
            if current and not fits(trial):
                lines.append(current)
                current = piece
            else:
                current = trial
    if current:
        lines.append(current)
    return lines


def render_text_bitmap(
    text: str,
    width_dots: int,
    height_dots: int,
    font_size_dots: int,
    font_path: str | None = None,
    stroke_width_dots: int = 0,
    wrap: bool = False,
    max_lines: int = 2,
    line_spacing: float = 1.15,
) -> Image.Image:
    """将文字居中栅格化为标签机可用的 1-bit 位图。

    wrap=True 时按宽度自动换行（默认最多 max_lines 行），放不下则缩小字号。
    """
    if width_dots <= 0 or height_dots <= 0:
        raise ValueError("文字位图尺寸必须大于 0")

    canvas = Image.new("L", (width_dots, height_dots), 255)
    draw = ImageDraw.Draw(canvas)
    font_size = max(1, font_size_dots)
    stroke_width = max(0, stroke_width_dots)
    max_content_width = max(1, width_dots - 4)
    max_content_height = max(1, height_dots - 4)
    lines = [text]
    font = load_cjk_font(font_size, font_path)
    line_height = 0

    while True:
        font = load_cjk_font(font_size, font_path)
        if wrap:
            lines = _wrap_text_lines(
                draw, text, font, max_content_width, stroke_width
            )
            if len(lines) > max_lines:
                lines = lines[:max_lines]
            _, sample_h, _ = _measure_text(draw, "Ag", font, stroke_width)
            line_height = max(1, int(round(sample_h * line_spacing)))
            total_height = sample_h + line_height * (len(lines) - 1)
            widest = max(
                (_measure_text(draw, line, font, stroke_width)[0] for line in lines),
                default=0,
            )
            fits = widest <= max_content_width and total_height <= max_content_height
            # 还有未放下的词时继续缩小
            full_lines = _wrap_text_lines(
                draw, text, font, max_content_width, stroke_width
            )
            if len(full_lines) > max_lines:
                fits = False
        else:
            widest, total_height, _ = _measure_text(draw, text, font, stroke_width)
            lines = [text]
            line_height = total_height
            fits = widest <= max_content_width and total_height <= max_content_height

        if fits or font_size == 1:
            break
        font_size = max(1, int(font_size * 0.9))

    if wrap:
        _, sample_h, _ = _measure_text(draw, "Ag", font, stroke_width)
        line_height = max(1, int(round(sample_h * line_spacing)))
        total_height = sample_h + line_height * (len(lines) - 1)
        y0 = (height_dots - total_height) // 2
        for i, line in enumerate(lines):
            line_w, _, bbox = _measure_text(draw, line, font, stroke_width)
            x = (width_dots - line_w) // 2 - bbox[0]
            draw.text(
                (x, y0 + i * line_height - bbox[1]),
                line,
                fill=0,
                font=font,
                stroke_width=stroke_width,
                stroke_fill=0,
            )
    else:
        line_w, line_h, bbox = _measure_text(draw, text, font, stroke_width)
        x = (width_dots - line_w) // 2 - bbox[0]
        y = (height_dots - line_h) // 2 - bbox[1]
        draw.text(
            (x, y),
            text,
            fill=0,
            font=font,
            stroke_width=stroke_width,
            stroke_fill=0,
        )

    return canvas.point(lambda p: 0 if p < 128 else 255, mode="1")


def pack_monochrome_image(img: Image.Image) -> BitmapPayload:
    """将 1-bit 图像打包为 TSC BITMAP 行数据（MSB 在左，0=打印黑点）。"""
    if img.mode != "1":
        img = img.convert("1")

    width, height = img.size
    width_bytes = (width + 7) // 8
    pixels = img.load()
    rows: list[bytes] = []

    for y in range(height):
        row = bytearray([0xFF] * width_bytes)
        for x in range(width):
            if pixels[x, y] == 0:
                byte_idx = x // 8
                bit = 7 - (x % 8)
                row[byte_idx] &= ~(1 << bit)
        rows.append(bytes(row))

    return BitmapPayload(width_bytes=width_bytes, height_dots=height, data=b"".join(rows))


def rasterize_for_label(
    img: Image.Image,
    width_dots: int,
    height_dots: int,
    threshold: int = 128,
    scale: float = 1.0,
) -> Image.Image:
    """缩放并居中铺到标签画布，输出精确尺寸的 1-bit 图。

    scale > 1 时在适应方式基础上进一步放大，超出部分居中裁切。
    """
    canvas = Image.new("L", (width_dots, height_dots), 255)
    src = img.convert("RGB") if img.mode not in ("L", "1") else img.convert("L")

    base_scale = min(width_dots / src.width, height_dots / src.height)
    factor = base_scale * max(0.5, min(2.0, scale))
    new_w = max(1, int(round(src.width * factor)))
    new_h = max(1, int(round(src.height * factor)))
    resized = src.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - width_dots) // 2
    top = (new_h - height_dots) // 2
    if new_w >= width_dots and new_h >= height_dots:
        cropped = resized.crop((left, top, left + width_dots, top + height_dots))
        canvas.paste(cropped, (0, 0))
    else:
        offset_x = (width_dots - new_w) // 2
        offset_y = (height_dots - new_h) // 2
        canvas.paste(resized, (offset_x, offset_y))
    return canvas.point(lambda p: 0 if p < threshold else 255, mode="1")


def paste_scaled_centered(
    canvas: Image.Image,
    src: Image.Image,
    scale: float,
) -> None:
    """将 src 按 scale 相对画布等比放大后居中粘贴，超出部分裁切。"""
    cw, ch = canvas.size
    factor = max(0.5, min(2.0, scale))
    new_w = max(1, int(round(src.width * factor)))
    new_h = max(1, int(round(src.height * factor)))
    resized = src.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - cw) // 2
    top = (new_h - ch) // 2
    if new_w >= cw and new_h >= ch:
        canvas.paste(resized.crop((left, top, left + cw, top + ch)), (0, 0))
    else:
        canvas.paste(resized, ((cw - new_w) // 2, (ch - new_h) // 2))
