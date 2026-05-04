"""Build a normalized threatened-species reference from MMA CSV resources."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from pathlib import Path


REFERENCE_DIR = Path("data/gbif/00_reference/threatened_species_brazil")
RAW_DIR = REFERENCE_DIR / "raw"
OUTPUT_PATH = REFERENCE_DIR / "threatened_species_brazil_reference.json"


STATUS_CODE_PATTERN = re.compile(r"\(([^()]+)\)")


def read_csv(path: Path) -> list[dict]:
    content = path.read_bytes()
    text = content.decode("utf-8-sig", errors="replace")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    return list(csv.DictReader(io.StringIO(text), dialect=dialect))


def clean_text(value) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


def extract_status_code(value: str | None, row: dict) -> str | None:
    text = clean_text(value)
    if text:
        match = STATUS_CODE_PATTERN.search(text)
        if match:
            return match.group(1).strip().upper().replace(",", "")

    for code in ["EX", "EW", "CR", "EN", "VU", "RE"]:
        if clean_text(row.get(code)) or clean_text(row.get(f"{code},")):
            return code
    return None


def detect_group(path: Path, row: dict) -> str:
    name = path.name.lower()
    if "fauna" in name:
        return "fauna"
    if "flora" in name:
        return "flora"
    if "grupo taxon" in " ".join(row.keys()).lower():
        return "fauna"
    return "unknown"


def normalize_row(path: Path, row: dict) -> dict | None:
    scientific_name = clean_text(
        row.get("Espécie ou Subespécie")
        or row.get("Espécie (FB 2020)")
        or row.get("Espécie ou Subespécie/Variedade")
        or row.get("Nome Científico")
    )
    if not scientific_name:
        return None

    group = detect_group(path, row)
    status_text = clean_text(row.get("Sugestão de Categoria 2021") or row.get("Categoria") or row.get("Categoria em 2014"))
    status_code = extract_status_code(status_text, row)

    return {
        "species_id": f"MMA_{group}_{scientific_name}".replace(" ", "_"),
        "scientific_name": scientific_name,
        "canonical_name": None,
        "accepted_scientific_name": None,
        "taxon_rank": None,
        "taxon_key": None,
        "accepted_taxon_key": None,
        "kingdom": "Plantae" if group == "flora" else None,
        "phylum": None,
        "class": None,
        "order": clean_text(row.get("Ordem")),
        "family": clean_text(row.get("Família") or row.get("Família (FB 2020)")),
        "genus": scientific_name.split()[0] if scientific_name else None,
        "species": None,
        "threat_status_br": status_text,
        "threat_status_br_code": status_code,
        "threat_status_br_source": "MMA",
        "threat_status_br_source_document": "MMA Dados Abertos - Espécies Ameaçadas",
        "threat_status_br_year": 2021,
        "threat_status_global": None,
        "threat_status_global_source": None,
        "is_endemic_to_brazil": None,
        "biome": [],
        "state_occurrence": [],
        "taxonomic_group": clean_text(row.get("Grupo taxonômico")) or group,
        "source_reference_path": str(path),
        "source_row_number": clean_text(row.get("#")),
        "gbif_checklist_match_status": None,
        "gbif_taxon_match_confidence": None,
        "snapshot_date": None,
    }


def build_reference(args: argparse.Namespace) -> None:
    included_status_codes = set(args.include_status_codes.split(",")) if args.include_status_codes else None
    records = []
    for path in sorted(RAW_DIR.glob("*.csv")):
        if args.only and args.only.lower() not in path.name.lower():
            continue
        for row in read_csv(path):
            normalized = normalize_row(path, row)
            if normalized and (included_status_codes is None or normalized["threat_status_br_code"] in included_status_codes):
                records.append(normalized)

    seen = set()
    deduped = []
    for record in records:
        key = (record["scientific_name"], record["taxonomic_group"], record["threat_status_br_code"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(deduped)} threatened-species reference records to {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Optional substring to filter raw CSV file names.")
    parser.add_argument(
        "--include-status-codes",
        help="Optional comma-separated status codes to keep. By default all observed categories are kept.",
    )
    build_reference(parser.parse_args())


if __name__ == "__main__":
    main()
