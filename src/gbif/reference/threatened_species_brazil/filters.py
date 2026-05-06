from __future__ import annotations

import json
from pathlib import Path

from src.gbif.shared.normalize import clean_text


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)
ALLOWED_REFERENCE_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY"}
EXCLUDED_MATCH_STATUSES = {"HIGHERRANK", "NONE"}


def load_reference_records(path: Path = REFERENCE_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_operational_taxon_match(record: dict) -> bool:
    rank = clean_text(record.get("taxon_rank"))
    match_status = clean_text(record.get("gbif_checklist_match_status"))
    if rank not in ALLOWED_REFERENCE_RANKS:
        return False
    if match_status in EXCLUDED_MATCH_STATUSES:
        return False
    return bool(record.get("accepted_taxon_key") or record.get("taxon_key"))


def operational_taxon_keys(records: list[dict], limit: int | None = None) -> list[int]:
    taxon_keys: list[int] = []
    seen: set[int] = set()
    for record in records:
        if not is_operational_taxon_match(record):
            continue
        taxon_key = record.get("accepted_taxon_key") or record.get("taxon_key")
        key = int(taxon_key)
        if key in seen:
            continue
        taxon_keys.append(key)
        seen.add(key)
        if limit and len(taxon_keys) >= limit:
            break
    return taxon_keys


def operational_species_by_taxon_key(records: list[dict]) -> dict[int, dict]:
    species_by_taxon_key = {}
    for record in records:
        if not is_operational_taxon_match(record):
            continue
        for key_name in ["accepted_taxon_key", "taxon_key"]:
            taxon_key = record.get(key_name)
            if taxon_key is not None:
                species_by_taxon_key.setdefault(int(taxon_key), record)
    return species_by_taxon_key
