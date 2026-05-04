from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from src.gbif.shared.quality_checks import build_quality_report


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def backup_existing_files(output_dir: Path, file_names: list[str]) -> Path | None:
    existing = [output_dir / file_name for file_name in file_names if (output_dir / file_name).exists()]
    if not existing:
        return None

    backup_dir = output_dir / "backup" / datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in existing:
        shutil.move(str(path), str(backup_dir / path.name))
    return backup_dir


def infer_json_type(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return "string"


def build_schema(records: list[dict], fields: list[str], title: str) -> dict:
    properties = {}
    for field in fields:
        observed_types = sorted(
            {infer_json_type(record.get(field)) for record in records if record.get(field) is not None}
        )
        properties[field] = {"type": observed_types or ["null"]}

    return {
        "title": title,
        "type": "array",
        "items": {
            "type": "object",
            "properties": properties,
            "required": fields,
        },
    }


def write_gold_product(
    output_dir: Path,
    data_file_name: str,
    records: list[dict],
    fields: list[str],
    schema_title: str,
    extra_quality: dict | None = None,
    manifest: dict | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_existing_files(output_dir, [data_file_name, "schema.json", "quality_report.json", "manifest.json"])

    quality_report = build_quality_report(records, fields)
    if extra_quality:
        quality_report.update(extra_quality)

    write_json(output_dir / data_file_name, records)
    write_json(output_dir / "schema.json", build_schema(records, fields, schema_title))
    write_json(output_dir / "quality_report.json", quality_report)
    if manifest:
        manifest = {
            **manifest,
            "gold_file": str(output_dir / data_file_name),
            "schema_file": str(output_dir / "schema.json"),
            "quality_report_file": str(output_dir / "quality_report.json"),
            "generated_at": datetime.now().replace(microsecond=0).isoformat(),
            "record_count": len(records),
        }
        write_json(output_dir / "manifest.json", manifest)
