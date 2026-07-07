"""位图打包单元测试。"""

from PIL import Image

from label_printer.tspl.bitmap import pack_monochrome_image, rasterize_for_label


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
