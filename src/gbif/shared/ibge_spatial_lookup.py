"""Spatial lookup helpers for assigning IBGE state and municipality."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


IBGE_DIR = Path("data/gbif/00_reference/ibge")
STATES_TABLE_PATH = IBGE_DIR / "tables/states.json"
MUNICIPALITIES_TABLE_PATH = IBGE_DIR / "tables/municipalities.json"
STATES_MESH_PATH = IBGE_DIR / "meshes/states.geojson"
MUNICIPALITIES_MESH_PATH = IBGE_DIR / "meshes/municipalities.geojson"


def _load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(
            f"IBGE reference file not found: {path}. "
            "Run: uv run python -m src.gbif.reference.ibge.download_reference"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _municipality_state(record: dict) -> dict:
    immediate_region = record.get("regiao-imediata") or {}
    intermediate_region = immediate_region.get("regiao-intermediaria") or {}
    uf = intermediate_region.get("UF")
    if uf:
        return uf
    microregion = record.get("microrregiao") or {}
    mesoregion = microregion.get("mesorregiao") or {}
    return mesoregion.get("UF") or {}


def _as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class IBGELocation:
    state_code: int | None
    state_name: str | None
    municipality_code: int | None
    municipality_name: str | None

    def as_record_fields(self) -> dict:
        return {
            "acm_state_code": self.state_code,
            "acm_state_province": self.state_name,
            "acm_municipality_code": self.municipality_code,
            "acm_municipality": self.municipality_name,
        }


class IBGESpatialLookup:
    def __init__(self) -> None:
        self.states = gpd.read_file(STATES_MESH_PATH)
        self.municipalities = gpd.read_file(MUNICIPALITIES_MESH_PATH)
        self.states_by_code = self._load_states_by_code()
        self.municipalities_by_code = self._load_municipalities_by_code()
        self._cache: dict[tuple[float, float], IBGELocation] = {}

    def lookup(self, latitude, longitude) -> IBGELocation:
        if not isinstance(latitude, int | float) or not isinstance(longitude, int | float):
            return IBGELocation(None, None, None, None)

        cache_key = (round(float(latitude), 6), round(float(longitude), 6))
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        point = Point(float(longitude), float(latitude))
        municipality_code = self._find_covering_code(self.municipalities, point)
        municipality = self.municipalities_by_code.get(municipality_code) if municipality_code else None

        if municipality:
            location = IBGELocation(
                state_code=municipality.get("state_code"),
                state_name=municipality.get("state_name"),
                municipality_code=municipality.get("municipality_code"),
                municipality_name=municipality.get("municipality_name"),
            )
        else:
            state_code = self._find_covering_code(self.states, point)
            state = self.states_by_code.get(state_code) if state_code else None
            location = IBGELocation(
                state_code=state.get("state_code") if state else None,
                state_name=state.get("state_name") if state else None,
                municipality_code=None,
                municipality_name=None,
            )

        self._cache[cache_key] = location
        return location

    def _load_states_by_code(self) -> dict[int, dict]:
        return {
            int(record["id"]): {
                "state_code": int(record["id"]),
                "state_abbreviation": record.get("sigla"),
                "state_name": record.get("nome"),
            }
            for record in _load_json(STATES_TABLE_PATH)
        }

    def _load_municipalities_by_code(self) -> dict[int, dict]:
        records = {}
        for record in _load_json(MUNICIPALITIES_TABLE_PATH):
            uf = _municipality_state(record)
            municipality_code = int(record["id"])
            records[municipality_code] = {
                "municipality_code": municipality_code,
                "municipality_name": record.get("nome"),
                "state_code": _as_int(uf.get("id")),
                "state_abbreviation": uf.get("sigla"),
                "state_name": uf.get("nome"),
            }
        return records

    @staticmethod
    def _find_covering_code(frame: gpd.GeoDataFrame, point: Point) -> int | None:
        for index in frame.sindex.query(point):
            row = frame.iloc[int(index)]
            if row.geometry.covers(point):
                return _as_int(row.get("codarea"))
        return None
