"""Download IBGE locality tables and simplified meshes for spatial lookup."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import requests

from src.gbif.gold.shared import write_json


REFERENCE_DIR = Path("data/gbif/00_reference/ibge")
TABLES_DIR = REFERENCE_DIR / "tables"
MESHES_DIR = REFERENCE_DIR / "meshes"

SOURCES = {
    "states_table": "https://servicodados.ibge.gov.br/api/v1/localidades/estados",
    "municipalities_table": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios",
    "states_mesh": (
        "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
        "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
    ),
    "municipalities_mesh": (
        "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
        "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
    ),
}


def get_json(url: str):
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    return response.json()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def flatten_states(records: list[dict]) -> list[dict]:
    return [
        {
            "state_code": record.get("id"),
            "state_abbreviation": record.get("sigla"),
            "state_name": record.get("nome"),
            "region_code": (record.get("regiao") or {}).get("id"),
            "region_abbreviation": (record.get("regiao") or {}).get("sigla"),
            "region_name": (record.get("regiao") or {}).get("nome"),
        }
        for record in records
    ]


def municipality_state(record: dict) -> dict:
    immediate_region = record.get("regiao-imediata") or {}
    intermediate_region = immediate_region.get("regiao-intermediaria") or {}
    uf = intermediate_region.get("UF")
    if uf:
        return uf
    microregion = record.get("microrregiao") or {}
    mesoregion = microregion.get("mesorregiao") or {}
    return mesoregion.get("UF") or {}


def flatten_municipalities(records: list[dict]) -> list[dict]:
    rows = []
    for record in records:
        uf = municipality_state(record)
        rows.append(
            {
                "municipality_code": record.get("id"),
                "municipality_name": record.get("nome"),
                "state_code": uf.get("id"),
                "state_abbreviation": uf.get("sigla"),
                "state_name": uf.get("nome"),
            }
        )
    return rows


def build_manifest(files: dict[str, str]) -> dict:
    return {
        "reference": "ibge_localities_and_meshes",
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "source": "IBGE Servico de Dados",
        "source_urls": SOURCES,
        "files": files,
        "notes": [
            "Tables come from the IBGE Localidades API.",
            "Meshes come from the IBGE Malhas API using simplified GeoJSON for Brazil with internal divisions.",
            "The meshes are used to assign acm_state_province and acm_municipality by point-in-polygon lookup.",
        ],
    }


def main() -> None:
    states = get_json(SOURCES["states_table"])
    municipalities = get_json(SOURCES["municipalities_table"])
    states_mesh = get_json(SOURCES["states_mesh"])
    municipalities_mesh = get_json(SOURCES["municipalities_mesh"])

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    MESHES_DIR.mkdir(parents=True, exist_ok=True)

    write_json(TABLES_DIR / "states.json", states)
    write_json(TABLES_DIR / "municipalities.json", municipalities)
    write_csv(
        TABLES_DIR / "states.csv",
        flatten_states(states),
        ["state_code", "state_abbreviation", "state_name", "region_code", "region_abbreviation", "region_name"],
    )
    write_csv(
        TABLES_DIR / "municipalities.csv",
        flatten_municipalities(municipalities),
        ["municipality_code", "municipality_name", "state_code", "state_abbreviation", "state_name"],
    )
    write_json(MESHES_DIR / "states.geojson", states_mesh)
    write_json(MESHES_DIR / "municipalities.geojson", municipalities_mesh)

    files = {
        "states_json": str(TABLES_DIR / "states.json"),
        "states_csv": str(TABLES_DIR / "states.csv"),
        "municipalities_json": str(TABLES_DIR / "municipalities.json"),
        "municipalities_csv": str(TABLES_DIR / "municipalities.csv"),
        "states_mesh_geojson": str(MESHES_DIR / "states.geojson"),
        "municipalities_mesh_geojson": str(MESHES_DIR / "municipalities.geojson"),
    }
    write_json(REFERENCE_DIR / "manifest.json", build_manifest(files))
    print(f"saved IBGE reference files to {REFERENCE_DIR}")


if __name__ == "__main__":
    main()
