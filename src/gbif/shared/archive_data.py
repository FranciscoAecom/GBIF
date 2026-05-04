from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


def pack_snapshot(snapshot_dir: Path, bundle_path: Path, remove_source: bool = True) -> Path:
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_path.exists():
        bundle_path.unlink()

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in snapshot_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(snapshot_dir))

    if remove_source:
        shutil.rmtree(snapshot_dir)
    return bundle_path


def unpack_snapshot(bundle_path: Path, snapshot_dir: Path) -> Path:
    if snapshot_dir.exists():
        return snapshot_dir
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle_path, "r") as archive:
        archive.extractall(snapshot_dir)
    return snapshot_dir

