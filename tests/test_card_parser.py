from card_ocr_service.parser.card_parser import normalize_card_number, normalize_expiry_ym


def test_normalize_card_number() -> None:
    assert normalize_card_number("8100 0012 3456 7890") == "8100001234567890"


def test_normalize_expiry_ym() -> None:
    assert normalize_expiry_ym("12/29") == "202912"

