from __future__ import annotations

import re
from datetime import date, datetime

from src.gbif.shared.normalize import clean_text


FULL_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
YEAR_RE = re.compile(r"^\d{4}$")
DATETIME_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[T\s]")
DATE_RANGE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$")


def normalize_event_date(value) -> dict[str, str | None]:
    text = clean_text(value)
    if text is None:
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "MISSING",
            "acm_event_date_issue": "missing_event_date",
        }

    if DATE_RANGE_RE.match(text):
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "RANGE",
            "acm_event_date_issue": "date_range_not_normalized",
        }

    if FULL_DATE_RE.match(text):
        return _normalize_full_date(text, "DAY")

    datetime_match = DATETIME_PREFIX_RE.match(text)
    if datetime_match:
        return _normalize_full_date(datetime_match.group(1), "DATETIME")

    if YEAR_MONTH_RE.match(text):
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "MONTH",
            "acm_event_date_issue": "missing_day",
        }

    if YEAR_RE.match(text):
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "YEAR",
            "acm_event_date_issue": "missing_month_and_day",
        }

    return _try_iso_datetime(text)


def _normalize_full_date(text: str, precision: str) -> dict[str, str | None]:
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "INVALID",
            "acm_event_date_issue": "invalid_calendar_date",
        }
    return {
        "acm_event_date": parsed.isoformat(),
        "acm_event_date_precision": precision,
        "acm_event_date_issue": None,
    }


def _try_iso_datetime(text: str) -> dict[str, str | None]:
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return {
            "acm_event_date": None,
            "acm_event_date_precision": "INVALID",
            "acm_event_date_issue": "unrecognized_event_date_format",
        }
    return {
        "acm_event_date": parsed.date().isoformat(),
        "acm_event_date_precision": "DATETIME",
        "acm_event_date_issue": None,
    }
