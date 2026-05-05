from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests


BASE_URL = "https://api.gbif.org/v1"


class GbifApiClient:
    def __init__(self, base_url: str = BASE_URL, timeout: int = 60, sleep_seconds: float = 0.25):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.session = requests.Session()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params or {}, timeout=self.timeout)
        if response.status_code == 429:
            time.sleep(max(self.sleep_seconds, 2.0))
            response = self.session.get(url, params=params or {}, timeout=self.timeout)
        response.raise_for_status()
        time.sleep(self.sleep_seconds)
        return response.json()

    def post(
        self,
        path: str,
        payload: dict[str, Any],
        auth: tuple[str, str] | None = None,
    ) -> str:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.post(url, json=payload, auth=auth, timeout=self.timeout)
        if response.status_code == 429:
            time.sleep(max(self.sleep_seconds, 2.0))
            response = self.session.post(url, json=payload, auth=auth, timeout=self.timeout)
        response.raise_for_status()
        time.sleep(self.sleep_seconds)
        return response.text.strip().strip('"')

    def download_file(self, url: str, output_path: Path, max_attempts: int = 5) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path = output_path.with_suffix(output_path.suffix + ".part")

        if output_path.exists() and not partial_path.exists():
            output_path.replace(partial_path)

        for attempt in range(1, max_attempts + 1):
            downloaded_bytes = partial_path.stat().st_size if partial_path.exists() else 0
            headers = {"Range": f"bytes={downloaded_bytes}-"} if downloaded_bytes else {}
            mode = "ab" if downloaded_bytes else "wb"

            try:
                with self.session.get(url, stream=True, timeout=self.timeout, headers=headers) as response:
                    if response.status_code == 416 and partial_path.exists():
                        partial_path.replace(output_path)
                        return output_path
                    if response.status_code == 200 and downloaded_bytes:
                        mode = "wb"
                    elif response.status_code not in {200, 206}:
                        response.raise_for_status()

                    with partial_path.open(mode) as file:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                file.write(chunk)

                partial_path.replace(output_path)
                time.sleep(self.sleep_seconds)
                return output_path
            except requests.RequestException:
                if attempt == max_attempts:
                    raise
                time.sleep(max(self.sleep_seconds, 1.0) * attempt)

        time.sleep(self.sleep_seconds)
        return output_path

    def paged_search(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        page_size: int = 300,
    ):
        offset = 0
        collected = 0
        base_params = dict(params or {})

        while True:
            request_limit = page_size
            if limit is not None:
                remaining = limit - collected
                if remaining <= 0:
                    break
                request_limit = min(request_limit, remaining)

            page_params = {**base_params, "limit": request_limit, "offset": offset}
            page = self.get(path, page_params)
            results = page.get("results", [])
            yield page_params, page

            collected += len(results)
            if page.get("endOfRecords") or not results:
                break
            offset += len(results)
