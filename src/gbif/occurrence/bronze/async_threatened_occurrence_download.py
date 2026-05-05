"""Manage asynchronous GBIF occurrence downloads for Brazilian threatened species."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.gbif.shared.api_client import BASE_URL, GbifApiClient
from src.gbif.shared.paths import bronze_snapshot_dir


REFERENCE_PATH = Path(
    "data/gbif/00_reference/threatened_species_brazil/threatened_species_brazil_reference_gbif_matched.json"
)
REQUEST_ENDPOINT = "occurrence/download/request"
DOWNLOAD_ENDPOINT = "occurrence/download"
DOWNLOAD_FILE_BASE_URL = "https://api.gbif.org/occurrence/download/request"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_dir(snapshot_date: str) -> Path:
    return bronze_snapshot_dir("occurrence", snapshot_date) / "download_requests"


def downloaded_dir(snapshot_date: str) -> Path:
    return bronze_snapshot_dir("occurrence", snapshot_date) / "downloads"


def download_file_url(download_key: str) -> str:
    return f"{DOWNLOAD_FILE_BASE_URL}/{download_key}.zip"


def read_credentials() -> tuple[str, str, str]:
    username = os.getenv("GBIF_USERNAME")
    password = os.getenv("GBIF_PASSWORD")
    email = os.getenv("GBIF_EMAIL")
    missing = [
        name
        for name, value in {
            "GBIF_USERNAME": username,
            "GBIF_PASSWORD": password,
            "GBIF_EMAIL": email,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing GBIF environment variables: {', '.join(missing)}")
    return username or "", password or "", email or ""


def unique_taxon_keys(species_limit: int | None = None) -> list[int]:
    records = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    taxon_keys: list[int] = []
    seen: set[int] = set()
    for record in records:
        taxon_key = record.get("accepted_taxon_key") or record.get("taxon_key")
        if not taxon_key or taxon_key in seen:
            continue
        taxon_keys.append(int(taxon_key))
        seen.add(int(taxon_key))
        if species_limit and len(taxon_keys) >= species_limit:
            break
    return taxon_keys


def build_predicate(taxon_keys: list[int], include_absent: bool, has_coordinate: bool | None) -> dict[str, Any]:
    predicates: list[dict[str, Any]] = [
        {"type": "equals", "key": "COUNTRY", "value": "BR"},
        {"type": "in", "key": "TAXON_KEY", "values": [str(key) for key in taxon_keys]},
    ]
    if not include_absent:
        predicates.append({"type": "equals", "key": "OCCURRENCE_STATUS", "value": "PRESENT"})
    if has_coordinate is not None:
        predicates.append({"type": "equals", "key": "HAS_COORDINATE", "value": str(has_coordinate).lower()})
    return {"type": "and", "predicates": predicates}


def build_request_payload(
    username: str,
    email: str,
    taxon_keys: list[int],
    download_format: str,
    include_absent: bool,
    has_coordinate: bool | None,
) -> dict[str, Any]:
    return {
        "creator": username,
        "notificationAddresses": [email],
        "sendNotification": True,
        "format": download_format,
        "predicate": build_predicate(taxon_keys, include_absent, has_coordinate),
    }


def prepare(args: argparse.Namespace) -> Path:
    username = os.getenv("GBIF_USERNAME") or "<GBIF_USERNAME>"
    email = os.getenv("GBIF_EMAIL") or "<GBIF_EMAIL>"
    taxon_keys = unique_taxon_keys(args.species_limit)
    payload = build_request_payload(
        username=username,
        email=email,
        taxon_keys=taxon_keys,
        download_format=args.format,
        include_absent=args.include_absent,
        has_coordinate=args.has_coordinate,
    )
    output_path = request_dir(args.date) / "threatened_species_occurrence_download_request.json"
    write_json(output_path, payload)
    write_json(
        request_dir(args.date) / "threatened_species_occurrence_download_manifest.json",
        {
            "created_at": utc_now(),
            "status": "PREPARED_NOT_SUBMITTED",
            "source_reference": str(REFERENCE_PATH),
            "request_file": str(output_path),
            "gbif_endpoint": f"{BASE_URL}/{REQUEST_ENDPOINT}",
            "format": args.format,
            "country": "BR",
            "taxon_key_count": len(taxon_keys),
            "include_absent": args.include_absent,
            "has_coordinate": args.has_coordinate,
            "credential_source": "environment variables GBIF_USERNAME, GBIF_PASSWORD, GBIF_EMAIL",
        },
    )
    print(f"prepared request with {len(taxon_keys)} taxon keys: {output_path}")
    return output_path


def submit(args: argparse.Namespace) -> str:
    username, password, email = read_credentials()
    request_path = Path(args.request_file) if args.request_file else prepare(args)
    payload = read_json(request_path)
    payload["creator"] = username
    payload["notificationAddresses"] = [email]

    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)
    download_key = client.post(REQUEST_ENDPOINT, payload, auth=(username, password))
    manifest_path = request_path.parent / "threatened_species_occurrence_download_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    manifest.update(
        {
            "submitted_at": utc_now(),
            "status": "SUBMITTED",
            "download_key": download_key,
            "status_endpoint": f"{BASE_URL}/{DOWNLOAD_ENDPOINT}/{download_key}",
            "download_url": download_file_url(download_key),
            "request_file": str(request_path),
        }
    )
    write_json(manifest_path, manifest)
    print(f"submitted GBIF download request: {download_key}")
    return download_key


def status(args: argparse.Namespace) -> dict[str, Any]:
    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)
    payload = client.get(f"{DOWNLOAD_ENDPOINT}/{args.download_key}")
    output_path = request_dir(args.date) / f"{args.download_key}_status.json"
    write_json(output_path, payload)
    print(json.dumps({"key": args.download_key, "status": payload.get("status"), "doi": payload.get("doi")}, indent=2))
    return payload


def download(args: argparse.Namespace) -> Path:
    client = GbifApiClient(timeout=args.timeout, sleep_seconds=args.sleep_seconds)
    info = client.get(f"{DOWNLOAD_ENDPOINT}/{args.download_key}")
    if info.get("status") != "SUCCEEDED":
        raise RuntimeError(f"Download {args.download_key} is not ready. Current status: {info.get('status')}")

    output_path = downloaded_dir(args.date) / f"{args.download_key}.zip"
    source_url = info.get("downloadLink") or download_file_url(args.download_key)
    client.download_file(source_url, output_path, max_attempts=args.max_attempts)
    write_json(
        downloaded_dir(args.date) / f"{args.download_key}_download_manifest.json",
        {
            "downloaded_at": utc_now(),
            "download_key": args.download_key,
            "source_url": source_url,
            "output_path": str(output_path),
            "gbif_status": info.get("status"),
            "doi": info.get("doi"),
            "citation": info.get("citation"),
        },
    )
    print(f"downloaded GBIF archive: {output_path}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_request = argparse.ArgumentParser(add_help=False)
    common_request.add_argument("--date", required=True, help="Snapshot date in YYYYMMDD format.")
    common_request.add_argument("--species-limit", type=int, help="Optional limit for tests.")
    common_request.add_argument("--format", default="DWCA", choices=["DWCA", "SIMPLE_CSV", "SPECIES_LIST"])
    common_request.add_argument("--include-absent", action="store_true", help="Include ABSENT records.")
    common_request.add_argument("--has-coordinate", action=argparse.BooleanOptionalAction)

    prepare_parser = subparsers.add_parser("prepare", parents=[common_request])
    prepare_parser.set_defaults(func=prepare)

    submit_parser = subparsers.add_parser("submit", parents=[common_request])
    submit_parser.add_argument("--request-file", help="Use a prepared request JSON instead of creating one.")
    submit_parser.add_argument("--timeout", type=int, default=120)
    submit_parser.add_argument("--sleep-seconds", type=float, default=0.25)
    submit_parser.set_defaults(func=submit)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--date", required=True, help="Snapshot date in YYYYMMDD format.")
    status_parser.add_argument("--download-key", required=True)
    status_parser.add_argument("--timeout", type=int, default=60)
    status_parser.add_argument("--sleep-seconds", type=float, default=0.25)
    status_parser.set_defaults(func=status)

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--date", required=True, help="Snapshot date in YYYYMMDD format.")
    download_parser.add_argument("--download-key", required=True)
    download_parser.add_argument("--timeout", type=int, default=300)
    download_parser.add_argument("--sleep-seconds", type=float, default=0.25)
    download_parser.add_argument("--max-attempts", type=int, default=5)
    download_parser.set_defaults(func=download)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
