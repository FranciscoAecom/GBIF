"""Validate threatened species Brazil gold outputs."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from src.gbif.gold.threatened_species_brazil_schema import (
    DATASET_FIELDS,
    DATASETS_PATH,
    GPKG_ATTRIBUTE_FIELDS,
    GPKG_LAYER_NAME,
    GPKG_PATH,
    GOLD_DIR,
    OCCURRENCE_FIELDS,
    OCCURRENCES_PATH,
    SPECIES_FIELDS,
    SPECIES_PATH,
)
from src.gbif.shared.json_stream import iter_json_array


SCHEMA_PATH = GOLD_DIR / "schema.json"
MANIFEST_PATH = GOLD_DIR / "manifest.json"


class ValidationError(RuntimeError):
    pass


def read_json(path: Path):
    if not path.exists():
        raise ValidationError(f"missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def first_json_record(path: Path) -> dict:
    try:
        return next(iter_json_array(path))
    except StopIteration as exc:
        raise ValidationError(f"empty JSON array: {path}") from exc


def assert_record_fields(path: Path, expected_fields: list[str]) -> None:
    record = first_json_record(path)
    missing = [field for field in expected_fields if field not in record]
    extra = [field for field in record if field not in expected_fields]
    if missing or extra:
        raise ValidationError(f"{path} field mismatch. missing={missing} extra={extra}")


def assert_schema_fields(schema: dict) -> None:
    expected = {
        "species": SPECIES_FIELDS,
        "occurrences": OCCURRENCE_FIELDS,
        "datasets": DATASET_FIELDS,
        "geopackage": ["fid", "geom", *GPKG_ATTRIBUTE_FIELDS],
    }
    files = schema.get("files") or {}
    for name, fields in expected.items():
        observed = (files.get(name) or {}).get("fields")
        if observed != fields:
            raise ValidationError(f"schema fields mismatch for {name}")


def geopackage_columns() -> list[str]:
    if not GPKG_PATH.exists():
        raise ValidationError(f"missing required file: {GPKG_PATH}")
    with sqlite3.connect(GPKG_PATH) as connection:
        table_exists = connection.execute(
            "select count(*) from sqlite_master where type='table' and name=?",
            (GPKG_LAYER_NAME,),
        ).fetchone()[0]
        if not table_exists:
            raise ValidationError(f"missing GeoPackage layer: {GPKG_LAYER_NAME}")
        return [row[1] for row in connection.execute(f"pragma table_info({GPKG_LAYER_NAME})")]


def assert_geopackage_fields() -> None:
    columns = geopackage_columns()
    expected_fields = ["fid", "geom", *GPKG_ATTRIBUTE_FIELDS]
    missing = [field for field in expected_fields if field not in columns]
    audit_only = {
        "locality",
        "decimal_latitude",
        "decimal_longitude",
        "acm_decimal_latitude",
        "acm_decimal_longitude",
        "coordinate_uncertainty_in_meters",
        "has_geospatial_issue",
        "license",
    }
    leaked = sorted(audit_only & set(columns))
    if missing or leaked:
        raise ValidationError(f"GeoPackage field mismatch. missing={missing} leaked_audit_fields={leaked}")


def assert_manifest_outputs(manifest: dict) -> None:
    outputs = manifest.get("outputs") or {}
    expected = {
        "species": str(SPECIES_PATH),
        "occurrences": str(OCCURRENCES_PATH),
        "datasets": str(DATASETS_PATH),
        "geopackage": str(GPKG_PATH),
        "schema": str(SCHEMA_PATH),
    }
    for key, path in expected.items():
        observed = outputs.get(key)
        if observed != path:
            raise ValidationError(f"manifest output mismatch for {key}: expected={path} observed={observed}")


def validate() -> None:
    schema = read_json(SCHEMA_PATH)
    manifest = read_json(MANIFEST_PATH)

    assert_record_fields(SPECIES_PATH, SPECIES_FIELDS)
    assert_record_fields(OCCURRENCES_PATH, OCCURRENCE_FIELDS)
    assert_record_fields(DATASETS_PATH, DATASET_FIELDS)
    assert_schema_fields(schema)
    assert_geopackage_fields()
    assert_manifest_outputs(manifest)
    print("threatened_species_brazil validation OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    validate()


if __name__ == "__main__":
    main()
