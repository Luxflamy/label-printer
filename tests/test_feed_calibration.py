def test_build_auto_feed_gapdetect() -> None:
    from label_printer.tspl.feed_calibration import build_auto_feed_calibration_text

    label = {"width_mm": 50, "height_mm": 30, "gap_mm": 2, "direction": 1}
    text = build_auto_feed_calibration_text(label, media_type="gap", strategy="gapdetect")

    assert "SIZE 50 mm,30 mm" in text
    assert "GAP 2 mm,0 mm" in text
    assert "LIMITFEED 106 mm" in text  # (30+2)*3+10
    assert "GAPDETECT" in text
    assert "GAPDETECT 240" not in text  # 不传参数，避免尺寸偏差导致死循环
    assert "FORMFEED" in text
    assert "SET GAP AUTO" not in text
    assert "HOME" not in text
    assert "PRINT" not in text


def test_build_auto_feed_autodetect_omits_gap() -> None:
    from label_printer.tspl.feed_calibration import build_auto_feed_calibration_text

    label = {"width_mm": 50, "height_mm": 30, "gap_mm": 2, "direction": 1}
    text = build_auto_feed_calibration_text(label, strategy="autodetect")

    assert "AUTODETECT" in text
    assert "AUTODETECT 240" not in text
    assert "GAP " not in text
    assert "LIMITFEED" in text
    assert "FORMFEED" in text
    assert "HOME" not in text


def test_build_auto_feed_blackmark() -> None:
    from label_printer.tspl.feed_calibration import build_auto_feed_calibration_text

    label = {"width_mm": 100, "height_mm": 150, "gap_mm": 2, "direction": 1}
    text = build_auto_feed_calibration_text(label, media_type="blackmark")

    assert "BLINE 3 mm,0 mm" in text
    assert "BLINEDETECT" in text
    assert "BLINEDETECT 1200" not in text
    assert "LIMITFEED 466 mm" in text  # (150+2)*3+10
    assert "FORMFEED" in text
    assert "HOME" not in text
