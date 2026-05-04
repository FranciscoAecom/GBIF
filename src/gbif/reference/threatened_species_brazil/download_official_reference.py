"""Download official threatened-species reference resources from MMA open data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


CKAN_PACKAGE_URL = "https://dados.mma.gov.br/api/3/action/package_show?id=especies-ameacadas"
REFERENCE_DIR = Path("data/gbif/00_reference/threatened_species_brazil")
RAW_DIR = REFERENCE_DIR / "raw"


def slugify(value: str) -> str:
    keep = []
    for char in value.lower():
        if char.isalnum():
            keep.append(char)
        elif keep and keep[-1] != "_":
            keep.append("_")
    return "".join(keep).strip("_")


def download_file(url: str, path: Path) -> None:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)


def download_reference(args: argparse.Namespace) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    package_response = requests.get(CKAN_PACKAGE_URL, timeout=60)
    package_response.raise_for_status()
    package = package_response.json()["result"]

    resources = []
    for resource in package.get("resources", []):
        fmt = (resource.get("format") or "").upper()
        name = resource.get("name") or resource.get("id")
        url = resource.get("url")
        if not url or fmt not in {"CSV", "PDF"}:
            continue

        suffix = ".pdf" if fmt == "PDF" else ".csv"
        file_name = f"{slugify(name)}{suffix}"
        output_path = RAW_DIR / file_name
        if output_path.exists() and not args.force:
            print(f"kept existing {output_path}")
        else:
            download_file(url, output_path)
            print(f"downloaded {output_path}")

        resources.append(
            {
                "name": name,
                "format": fmt,
                "url": url,
                "local_path": str(output_path),
                "resource_id": resource.get("id"),
                "last_modified": resource.get("last_modified"),
            }
        )

    manifest = {
        "source": "MMA Dados Abertos - Espécies Ameaçadas",
        "package_url": CKAN_PACKAGE_URL,
        "package_id": package.get("id"),
        "package_title": package.get("title"),
        "notes": package.get("notes"),
        "resources": resources,
    }
    (REFERENCE_DIR / "official_reference_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    download_reference(parser.parse_args())


if __name__ == "__main__":
    main()

