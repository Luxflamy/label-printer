"""单色位图 → TSPL BITMAP 命令数据。"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class BitmapPayload:
    width_bytes: int
    height_dots: int
    data: bytes


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
