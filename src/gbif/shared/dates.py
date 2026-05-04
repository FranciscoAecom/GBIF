from datetime import date, datetime


def parse_snapshot_date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def snapshot_date_iso(value: str) -> str:
    return parse_snapshot_date(value).isoformat()


def reference_month_iso(value: str) -> str:
    parsed = parse_snapshot_date(value)
    return parsed.replace(day=1).isoformat()

