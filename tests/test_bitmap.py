"""位图打包单元测试。"""

from PIL import Image

from label_printer.tspl.bitmap import (
    pack_monochrome_image,
    rasterize_for_label,
    render_text_bitmap,
)


def test_pack_monochrome_single_black_pixel() -> None:
    img = Image.new("1", (8, 1), 255)
    pixels = img.load()
    pixels[0, 0] = 0
    payload = pack_monochrome_image(img)
    assert payload.width_bytes == 1
    assert payload.height_dots == 1
    # TSC: bit0=印黑；左上黑点 → MSB=0，其余=1
    assert payload.data == bytes([0x7F])


def test_pack_monochrome_all_white_and_black() -> None:
    white = pack_monochrome_image(Image.new("1", (8, 1), 255))
    black = pack_monochrome_image(Image.new("1", (8, 1), 0))
    assert white.data == bytes([0xFF])
    assert black.data == bytes([0x00])


def test_pack_monochrome_white_canvas_black_block() -> None:
    """白底黑块：打印机应在中央印黑，四周留白。"""
    img = Image.new("1", (8, 8), 255)
    for x in range(2, 6):
        for y in range(2, 6):
            img.putpixel((x, y), 0)
    payload = pack_monochrome_image(img)
    assert payload.data[0] == 0xFF
    assert payload.data[2] == 0xC3
    assert payload.data[3] == 0xC3
    assert payload.data[4] == 0xC3
    assert payload.data[5] == 0xC3


def test_rasterize_for_label_centers_content() -> None:
    src = Image.new("L", (40, 20), 0)
    out = rasterize_for_label(src, 80, 80, scale=1.0)
    assert out.size == (80, 80)
    assert out.getpixel((40, 40)) == 0


def test_rasterize_scale_enlarges_content() -> None:
    src = Image.new("L", (40, 20), 0)
    base = rasterize_for_label(src, 80, 80, scale=1.0)
    enlarged = rasterize_for_label(src, 80, 80, scale=1.2)
    base_ink = sum(1 for p in base.getdata() if p == 0)
    enlarged_ink = sum(1 for p in enlarged.getdata() if p == 0)
    assert enlarged_ink > base_ink


def test_render_chinese_text_bitmap_has_ink() -> None:
    image = render_text_bitmap(
        "海外仓发货",
        width_dots=720,
        height_dots=200,
        font_size_dots=128,
    )

    assert image.mode == "1"
    assert image.size == (720, 200)
    assert any(pixel == 0 for pixel in image.getdata())


def test_render_text_bitmap_wraps_long_title() -> None:
    title = (
        "MooMee Duvet Cover Set Heathered Dark Grey King Soft Comfy Breathable"
    )
    image = render_text_bitmap(
        title,
        width_dots=360,  # ~45mm @ 8 dots/mm
        height_dots=60,  # ~7.5mm
        font_size_dots=20,
        wrap=True,
        max_lines=2,
    )
    assert image.mode == "1"
    assert image.size == (360, 60)
    # 上下两行都应有墨点（换行生效）
    top_ink = any(image.getpixel((x, y)) == 0 for y in range(0, 28) for x in range(360))
    bottom_ink = any(image.getpixel((x, y)) == 0 for y in range(32, 60) for x in range(360))
    assert top_ink
    assert bottom_ink
