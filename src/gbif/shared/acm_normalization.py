from __future__ import annotations

import unicodedata

from src.gbif.shared.normalize import clean_text


OTHER_THREAT_STATUS = "Outros"
THREAT_STATUS_VALUES_TO_GROUP_AS_OTHER = {
    "nao e especie brasileira",
    "nao e mais taxon valido",
    "subespecie que sai da lista",
}


def normalize_threat_status_br(value) -> str:
    text = clean_text(value)
    if text is None:
        return OTHER_THREAT_STATUS

    key = _plain_key(text).strip("[]")
    if key == "criticamente em perigo (cr)":
        return "Criticamente em Perigo (CR)"
    if key in THREAT_STATUS_VALUES_TO_GROUP_AS_OTHER:
        return OTHER_THREAT_STATUS
    return text


def normalize_scientific_name(value, fallback=None):
    text = clean_text(value)
    if text is None or _looks_numeric(text) or _looks_bold_identifier(text):
        return clean_text(fallback)
    return text


def _plain_key(value: str) -> str:
    text = value.strip().lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )


def _looks_numeric(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _looks_bold_identifier(text: str) -> bool:
    return text.strip().upper().startswith("BOLD:")
