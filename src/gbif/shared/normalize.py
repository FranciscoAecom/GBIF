from __future__ import annotations


MISSING_VALUES = {"", " ", "null", "none", "nan", "n/a", "na", "-"}


def clean_text(value):
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    if text.lower() in MISSING_VALUES:
        return None
    return text


def clean_list(value):
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]

    seen = set()
    cleaned = []
    for item in value:
        normalized = clean_text(item)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)
    return cleaned


def first_present(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and clean_text(value) is None:
            continue
        return value
    return None

