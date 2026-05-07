"""Build a GeoPackage with georeferenced threatened-species occurrences."""

from __future__ import annotations

import argparse

import geopandas as gpd
from shapely.geometry import Point

from src.gbif.gold.threatened_species_brazil_manifest import update_manifest as update_product_manifest
from src.gbif.gold.shared import write_json
from src.gbif.gold.threatened_species_brazil_schema import (
    GPKG_ATTRIBUTE_FIELDS,
    GPKG_LAYER_NAME,
    GPKG_PATH,
    GOLD_DIR,
    OCCURRENCES_PATH,
)
from src.gbif.shared.coordinate_normalization import BRAZIL_BBOX
from src.gbif.shared.json_stream import iter_json_array


def is_valid_coordinate(record: dict) -> bool:
    lat = record.get("acm_decimal_latitude")
    lon = record.get("acm_decimal_longitude")
    return isinstance(lat, int | float) and isinstance(lon, int | float)


def spatial_duplicate_key(record: dict) -> str:
    return "|".join(
        [
            str(record.get("species_id")),
            f"{record.get('acm_decimal_latitude'):.6f}",
            f"{record.get('acm_decimal_longitude'):.6f}",
        ]
    )


def quality_sort_key(record: dict) -> tuple:
    uncertainty = record.get("coordinate_uncertainty_in_meters")
    if not isinstance(uncertainty, int | float):
        uncertainty = float("inf")
    return (
        record.get("acm_event_date") is None,
        uncertainty,
        record.get("references") is None,
        record.get("gbif_id") or float("inf"),
    )


def build_geopackage_row(record: dict) -> dict:
    return {field: record.get(field) for field in GPKG_ATTRIBUTE_FIELDS}


def build_best_records_by_spatial_key() -> tuple[dict[str, dict], dict[str, int], int, int]:
    best_records: dict[str, dict] = {}
    duplicate_counts: dict[str, int] = {}
    total_records = 0
    candidate_records = 0

    print(f"reading occurrence records from {OCCURRENCES_PATH}")
    for record in iter_json_array(OCCURRENCES_PATH):
        total_records += 1
        if not is_valid_coordinate(record):
            continue

        candidate_records += 1
        duplicate_key = spatial_duplicate_key(record)
        duplicate_counts[duplicate_key] = duplicate_counts.get(duplicate_key, 0) + 1
        current_best = best_records.get(duplicate_key)
        if current_best is None or quality_sort_key(record) < quality_sort_key(current_best):
            best_records[duplicate_key] = record

    return best_records, duplicate_counts, total_records, candidate_records


def write_batch(rows: list[dict], geometries: list[Point], append: bool) -> None:
    gdf = gpd.GeoDataFrame(rows, geometry=geometries, crs="EPSG:4326")
    gdf.to_file(GPKG_PATH, layer=GPKG_LAYER_NAME, driver="GPKG", mode="a" if append else "w")


def update_manifest(
    total_records: int,
    candidate_records: int,
    spatial_records: int,
    duplicate_groups: int,
    duplicate_features_removed: int,
) -> None:
    update_product_manifest(
        {
            "geopackage_layer": GPKG_LAYER_NAME,
            "geopackage_crs": "EPSG:4326",
            "geopackage_coordinate_filters": {
                "valid_lat_lon": True,
                "exclude_gbif_geospatial_issues": "except_when_coordinate_swap_falls_inside_brazil_bbox",
                "brazil_approximate_bbox": BRAZIL_BBOX,
            },
            "geopackage_source": str(OCCURRENCES_PATH),
            "geopackage_source_record_count": total_records,
            "geopackage_candidate_feature_count_before_deduplication": candidate_records,
            "geopackage_feature_count": spatial_records,
            "geopackage_deduplication": {
                "enabled": True,
                "key": "species_id + acm_decimal_latitude + acm_decimal_longitude rounded to 6 decimals",
                "duplicate_groups": duplicate_groups,
                "duplicate_features_removed": duplicate_features_removed,
                "kept_record_priority": [
                    "acm_event_date filled",
                    "smallest coordinate_uncertainty_in_meters",
                    "references filled",
                    "smallest gbif_id",
                ],
                "json_outputs_keep_all_records": True,
            },
        }
    )


def build_geopackage(args: argparse.Namespace) -> None:
    if GPKG_PATH.exists() and args.overwrite:
        GPKG_PATH.unlink()
    rows = []
    geometries = []
    append = False
    best_records, duplicate_counts, total_records, candidate_records = build_best_records_by_spatial_key()
    spatial_records = len(best_records)
    duplicate_groups = sum(1 for count in duplicate_counts.values() if count > 1)
    duplicate_features_removed = sum(count - 1 for count in duplicate_counts.values() if count > 1)

    print(f"writing GeoPackage layer {GPKG_LAYER_NAME} to {GPKG_PATH}")
    for duplicate_key, record in sorted(best_records.items()):
        rows.append(build_geopackage_row(record))
        geometries.append(Point(record["acm_decimal_longitude"], record["acm_decimal_latitude"]))

        if len(rows) >= args.batch_size:
            write_batch(rows, geometries, append=append)
            append = True
            rows = []
            geometries = []

    if rows:
        write_batch(rows, geometries, append=append)

    update_manifest(total_records, candidate_records, spatial_records, duplicate_groups, duplicate_features_removed)
    print(f"saved {spatial_records} features to {GPKG_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true", default=True)
    parser.add_argument("--batch-size", type=int, default=50000)
    build_geopackage(parser.parse_args())


if __name__ == "__main__":
    main()
