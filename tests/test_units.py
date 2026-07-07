from label_printer.utils.units import dots_to_mm, mm_to_dots


def test_roundtrip() -> None:
    assert dots_to_mm(mm_to_dots(25)) == 25.0
