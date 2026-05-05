from __future__ import annotations


def count_missing(records: list[dict], fields: list[str]) -> dict[str, int]:
    counts = {field: 0 for field in fields}
    for record in records:
        for field in fields:
            value = record.get(field)
            if value is None or value == "" or value == []:
                counts[field] += 1
    return counts


def build_quality_report(records: list[dict], fields: list[str]) -> dict:
    return {
        "record_count": len(records),
        "missing_by_field": count_missing(records, fields),
    }


def empty_quality_counts(fields: list[str]) -> dict:
    return {
        "record_count": 0,
        "missing_by_field": {field: 0 for field in fields},
    }


def update_quality_counts(counts: dict, record: dict, fields: list[str]) -> None:
    counts["record_count"] += 1
    for field in fields:
        value = record.get(field)
        if value is None or value == "" or value == []:
            counts["missing_by_field"][field] += 1
