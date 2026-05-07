"""Manifest helpers for the threatened species Brazil gold product."""

from __future__ import annotations

import json
from datetime import datetime

from src.gbif.gold.shared import write_json
from src.gbif.gold.threatened_species_brazil_schema import (
    DATASETS_PATH,
    GOLD_DIR,
    GPKG_PATH,
    OCCURRENCES_PATH,
    REFERENCE_PATH,
    SPECIES_PATH,
)


MANIFEST_PATH = GOLD_DIR / "manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}


def write_manifest(manifest: dict) -> None:
    write_json(MANIFEST_PATH, manifest)


def refresh_output_paths(manifest: dict) -> dict:
    outputs = manifest.setdefault("outputs", {})
    outputs["species"] = str(SPECIES_PATH) if SPECIES_PATH.exists() else "pending_species_extraction"
    outputs["occurrences"] = str(OCCURRENCES_PATH) if OCCURRENCES_PATH.exists() else "pending_occurrence_extraction"
    outputs["datasets"] = str(DATASETS_PATH) if DATASETS_PATH.exists() else "pending_dataset_extraction"
    outputs["geopackage"] = str(GPKG_PATH) if GPKG_PATH.exists() else "pending_geopackage_extraction"
    outputs["schema"] = str(GOLD_DIR / "schema.json")
    outputs["quality_report"] = str(GOLD_DIR / "quality_report.json")
    return manifest


def base_manifest(snapshot_date: str) -> dict:
    manifest = refresh_output_paths(load_manifest())
    manifest.update(
        {
            "product": "threatened_species_brazil",
            "version_scope": "first_operational_version",
            "threat_reference_decision": "MMA Dados Abertos 2021 CSV used as first-version operational reference",
            "reference_source": "MMA Dados Abertos - Especies Ameacadas",
            "reference_files": [
                "FAUNA - Lista de Especies Ameacadas - 2021.csv",
                "FLORA - Lista de Especies Ameacadas - 2021.csv",
            ],
            "reference_path": str(REFERENCE_PATH),
            "generated_at": datetime.now().replace(microsecond=0).isoformat(),
            "snapshot_date": snapshot_date,
        }
    )
    return manifest


def update_manifest(updates: dict) -> None:
    manifest = refresh_output_paths(load_manifest())
    manifest.setdefault("product", "threatened_species_brazil")
    manifest.update(updates)
    write_manifest(manifest)
