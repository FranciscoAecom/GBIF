"""Canonical schema constants for the threatened species Brazil gold product."""

from __future__ import annotations

from pathlib import Path


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)
GOLD_DIR = Path("data/gbif/03_gold/threatened_species_brazil")
SPECIES_PATH = GOLD_DIR / "species.json"
OCCURRENCES_PATH = GOLD_DIR / "occurrences.json"
DATASETS_PATH = GOLD_DIR / "datasets.json"
GPKG_PATH = GOLD_DIR / "threatened_species_occurrences.gpkg"
GPKG_LAYER_NAME = "threatened_species_occurrences"

SPECIES_FIELDS = [
    "species_id",
    "scientific_name",
    "canonical_name",
    "accepted_scientific_name",
    "taxon_rank",
    "taxon_key",
    "accepted_taxon_key",
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "threat_status_br",
    "acm_threat_status_br",
    "threat_status_br_code",
    "threat_status_br_source",
    "threat_status_br_source_document",
    "threat_status_br_year",
    "threat_status_global",
    "threat_status_global_source",
    "is_endemic_to_brazil",
    "biome",
    "state_occurrence",
    "source_reference_path",
    "gbif_checklist_match_status",
    "gbif_taxon_match_confidence",
    "snapshot_date",
]

OCCURRENCE_FIELDS = [
    "record_id",
    "gbif_id",
    "species_id",
    "scientific_name",
    "taxon_key",
    "dataset_key",
    "basis_of_record",
    "occurrence_status",
    "event_date",
    "acm_event_date",
    "year",
    "month",
    "day",
    "country_code",
    "state_province",
    "acm_state_province",
    "municipality",
    "acm_municipality",
    "locality",
    "decimal_latitude",
    "decimal_longitude",
    "coordinate_uncertainty_in_meters",
    "has_coordinate",
    "has_geospatial_issue",
    "acm_decimal_latitude",
    "acm_decimal_longitude",
    "sampling_event_id",
    "sampling_protocol",
    "sampling_effort",
    "license",
    "references",
    "snapshot_date",
    "bronze_file_path",
    "threat_status_br",
    "acm_threat_status_br",
    "threat_status_br_code",
]

DATASET_FIELDS = [
    "dataset_key",
    "dataset_title",
    "dataset_type",
    "publishing_org_key",
    "hosting_org_key",
    "doi",
    "license",
    "homepage",
    "citation",
    "record_count_total",
    "threatened_species_record_count",
    "threatened_species_count",
    "source_occurrence_count",
    "snapshot_date",
    "bronze_file_path",
]

GPKG_ATTRIBUTE_FIELDS = [
    "record_id",
    "gbif_id",
    "species_id",
    "scientific_name",
    "threat_status_br",
    "acm_threat_status_br",
    "threat_status_br_code",
    "taxon_key",
    "dataset_key",
    "basis_of_record",
    "occurrence_status",
    "event_date",
    "acm_event_date",
    "country_code",
    "state_province",
    "acm_state_province",
    "municipality",
    "acm_municipality",
    "references",
]

GPKG_DOCUMENTED_FIELDS = ["fid", "geom", *GPKG_ATTRIBUTE_FIELDS]


def build_product_schema() -> dict:
    return {
        "product": "threatened_species_brazil",
        "reference_decision": "MMA Dados Abertos 2021 CSV",
        "files": {
            "species": {
                "path": str(SPECIES_PATH),
                "fields": SPECIES_FIELDS,
                "unit": "one threatened species reference record",
            },
            "occurrences": {
                "path": str(OCCURRENCES_PATH),
                "fields": OCCURRENCE_FIELDS,
                "unit": "one GBIF occurrence linked to a threatened species reference record",
            },
            "datasets": {
                "path": str(DATASETS_PATH),
                "fields": DATASET_FIELDS,
                "unit": "one GBIF dataset contributing threatened species occurrences",
            },
            "geopackage": {
                "path": str(GPKG_PATH),
                "layer": GPKG_LAYER_NAME,
                "fields": GPKG_DOCUMENTED_FIELDS,
                "crs": "EPSG:4326",
                "unit": "one deduplicated spatial feature per species and coordinate",
            },
        },
    }
