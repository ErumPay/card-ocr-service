from datetime import date

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
    assert normalize_expiry_ym("12/29", today=date(2026, 6, 2)) == "202912"


def test_normalize_expiry_ym_when_ocr_text_is_attached_to_label() -> None:
    assert normalize_expiry_ym("Date 12/30CVC 012", today=date(2026, 6, 2)) == "203012"


def test_normalize_expiry_ym_rejects_unrealistic_future_year() -> None:
    assert normalize_expiry_ym("07/77", today=date(2026, 6, 2)) is None


def test_normalize_expiry_ym_rejects_expired_month() -> None:
    assert normalize_expiry_ym("05/26", today=date(2026, 6, 2)) is None


def test_normalize_expiry_ym_ignores_compact_card_codes() -> None:
    text = "BSH1124BS203 5032-683 VALID 12/31 THRU"

    assert normalize_expiry_ym(text, today=date(2026, 6, 2)) == "203112"


def test_normalize_expiry_ym_rejects_compact_month_year() -> None:
    assert normalize_expiry_ym("VALID 1124 THRU", today=date(2026, 6, 2)) is None
