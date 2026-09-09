"""TSPL 命令构建单元测试。"""

from label_printer.tspl.bitmap import BitmapPayload
from label_printer.tspl.commands import LabelJob
from label_printer.utils.units import mm_to_dots


def test_mm_to_dots() -> None:
    assert mm_to_dots(10) == 80
    assert mm_to_dots(40) == 320


def test_label_job_hello() -> None:
    job = LabelJob(width_mm=40, height_mm=30, gap_mm=2)
    job.text(x_mm=2.5, y_mm=2.5, content="USB TEST", font="3")
    data = job.build()
    assert b"SIZE 40 mm,30 mm" in data
    assert b"GAP 2 mm,0 mm" in data
    assert b'TEXT 20,20,"3",0,1,1,"USB TEST"' in data
    assert b"PRINT 1" in data
    assert data.endswith(b"\r\n")


def test_label_job_barcode_and_qrcode() -> None:
    job = LabelJob(width_mm=50, height_mm=30)
    job.barcode(x_mm=3, y_mm=16, content="123456", symbology="128", height_mm=12)
    job.qrcode(x_mm=30, y_mm=5, content="hello")
    data = job.build_text()
    assert 'BARCODE 24,128,"128",96,1,0,2,4,"123456"' in data
    assert 'QRCODE 240,40,M,4,A,0,"hello"' in data


def test_label_job_escapes_quotes() -> None:
    job = LabelJob(width_mm=40, height_mm=30)
    job.text(x_mm=0, y_mm=0, content='say "hi"')
    assert "say 'hi'" in job.build_text()


def test_label_job_gap_offset() -> None:
    job = LabelJob(width_mm=40, height_mm=30, gap_mm=2, gap_offset_mm=0.5, reference=(4, -2))
    data = job.build_text()
    assert "GAP 2 mm,0.5 mm" in data
    assert "REFERENCE 4,-2" in data


def test_label_job_box() -> None:
    job = LabelJob(width_mm=40, height_mm=30)
    job.box(1, 1, 39, 29, thickness=2)
    assert "BOX 8,8,312,232,2" in job.build_text()


def test_label_job_bitmap_keeps_binary_data() -> None:
    job = LabelJob(width_mm=40, height_mm=30)
    payload = BitmapPayload(width_bytes=1, height_dots=2, data=b"\x00\xff")
    job.bitmap(1, 2, payload)

    data = job.build()
    assert b"BITMAP 8,16,1,2,0,\x00\xff\r\n" in data
    assert "BITMAP 8,16,1,2,0,<2 binary bytes>" in job.build_text()


def test_label_job_multiple_copies() -> None:
    job = LabelJob(width_mm=40, height_mm=30)
    assert b"PRINT 5" in job.build(copies=5)
