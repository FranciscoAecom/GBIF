"""Build a GeoPackage with georeferenced threatened-species occurrences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

from src.gbif.gold.shared import write_json


GOLD_DIR = Path("data/gbif/03_gold/threatened_species_brazil")
OCCURRENCES_PATH = GOLD_DIR / "occurrences.json"
GPKG_PATH = GOLD_DIR / "threatened_species_occurrences.gpkg"
LAYER_NAME = "threatened_species_occurrences"

GPKG_FIELDS = [
    "record_id",
    "gbif_id",
    "species_id",
    "scientific_name",
    "threat_status_br",
    "threat_status_br_code",
    "taxon_key",
    "dataset_key",
    "basis_of_record",
    "occurrence_status",
    "event_date",
    "country_code",
    "state_province",
    "municipality",
    "locality",
    "decimal_latitude",
    "decimal_longitude",
    "coordinate_uncertainty_in_meters",
    "has_geospatial_issue",
    "license",
    "references",
]


def is_valid_coordinate(record: dict) -> bool:
    lat = record.get("decimal_latitude")
    lon = record.get("decimal_longitude")
    return isinstance(lat, int | float) and isinstance(lon, int | float) and -90 <= lat <= 90 and -180 <= lon <= 180


def update_manifest(total_records: int, spatial_records: int) -> None:
    manifest_path = GOLD_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.setdefault("outputs", {})
    manifest["outputs"]["geopackage"] = str(GPKG_PATH)
    manifest["geopackage_layer"] = LAYER_NAME
    manifest["geopackage_crs"] = "EPSG:4326"
    manifest["geopackage_source"] = str(OCCURRENCES_PATH)
    manifest["geopackage_source_record_count"] = total_records
    manifest["geopackage_feature_count"] = spatial_records
    write_json(manifest_path, manifest)


def build_geopackage(args: argparse.Namespace) -> None:
    records = json.loads(OCCURRENCES_PATH.read_text(encoding="utf-8"))
    spatial_records = [record for record in records if is_valid_coordinate(record)]

    rows = []
    geometries = []
    for record in spatial_records:
        rows.append({field: record.get(field) for field in GPKG_FIELDS})
        geometries.append(Point(record["decimal_longitude"], record["decimal_latitude"]))

    gdf = gpd.GeoDataFrame(rows, geometry=geometries, crs="EPSG:4326")
    if GPKG_PATH.exists() and args.overwrite:
        GPKG_PATH.unlink()
    gdf.to_file(GPKG_PATH, layer=LAYER_NAME, driver="GPKG")
    update_manifest(len(records), len(spatial_records))
    print(f"saved {len(spatial_records)} features to {GPKG_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", default=True)
    build_geopackage(parser.parse_args())


if __name__ == "__main__":
    main()

