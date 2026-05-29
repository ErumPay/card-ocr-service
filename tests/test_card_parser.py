from card_ocr_service.parser.card_parser import (
    find_card_number,
    normalize_card_number,
    normalize_expiry_ym,
)


def test_normalize_card_number() -> None:
    assert normalize_card_number("8100 0012 3456 7890") == "8100001234567890"


def test_find_card_number_in_mixed_text() -> None:
    assert find_card_number("valid thru 12/29 8100 0012 3456 7890") == "8100001234567890"


def test_normalize_expiry_ym() -> None:
    assert normalize_expiry_ym("12/29") == "202912"


def test_normalize_expiry_ym_when_ocr_text_is_attached_to_label() -> None:
    assert normalize_expiry_ym("Date 12/30CVC 012") == "203012"
