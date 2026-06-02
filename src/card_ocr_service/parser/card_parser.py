import re
from datetime import date

MAX_EXPIRY_YEARS_AHEAD = 10


def find_card_number(text: str) -> str | None:
    for match in re.finditer(r"\b\d{4}(?:[\s-]?\d{4}){3}\b", text):
        card_number = normalize_card_number(match.group())
        if card_number is not None:
            return card_number
    return None


def normalize_card_number(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) != 16:
        return None
    return digits


def normalize_expiry_ym(text: str, today: date | None = None) -> str | None:
    for match in re.finditer(r"(?<!\d)(0[1-9]|1[0-2])\s*/\s*(\d{2}|\d{4})(?!\d)", text):
        month, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"
        if _is_supported_expiry(year=int(year), month=int(month), today=today or date.today()):
            return f"{year}{month}"
    return None


def _is_supported_expiry(year: int, month: int, today: date) -> bool:
    if year < today.year:
        return False
    if year == today.year and month < today.month:
        return False
    return year <= today.year + MAX_EXPIRY_YEARS_AHEAD
