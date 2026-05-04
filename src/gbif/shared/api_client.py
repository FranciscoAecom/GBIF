from __future__ import annotations

import time
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

