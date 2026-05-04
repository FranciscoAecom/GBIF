from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data" / "gbif"
BRONZE_ROOT = DATA_ROOT / "01_bronze"
SILVER_ROOT = DATA_ROOT / "02_silver"
GOLD_ROOT = DATA_ROOT / "03_gold"


def bronze_snapshot_dir(dataset_class: str, snapshot_date: str) -> Path:
    return BRONZE_ROOT / dataset_class / snapshot_date


def bronze_bundle_path(dataset_class: str, snapshot_date: str) -> Path:
    return BRONZE_ROOT / dataset_class / f"{snapshot_date}_core.zip"


def silver_snapshot_dir(dataset_class: str, snapshot_date: str) -> Path:
    return SILVER_ROOT / dataset_class / snapshot_date


def gold_product_dir(product_name: str) -> Path:
    return GOLD_ROOT / product_name
