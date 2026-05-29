import re


def normalize_card_number(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) != 16:
        return None
    return digits


def normalize_expiry_ym(text: str) -> str | None:
    match = re.search(r"\b(0[1-9]|1[0-2])\s*[/\-]?\s*(\d{2}|\d{4})\b", text)
    if not match:
        return None

    month, year = match.groups()
    if len(year) == 2:
        year = f"20{year}"
    return f"{year}{month}"

