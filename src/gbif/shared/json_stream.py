from __future__ import annotations

import json
from pathlib import Path


def write_json_array(path: Path, records, on_record=None) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as file:
        file.write("[\n")
        first = True
        for record in records:
            if not first:
                file.write(",\n")
            file.write(json.dumps(record, ensure_ascii=False, indent=2))
            if on_record:
                on_record(record)
            count += 1
            first = False
        file.write("\n]\n")
    return count


def iter_json_array(path: Path):
    decoder = json.JSONDecoder()
    buffer = ""
    started = False

    with path.open("r", encoding="utf-8") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk and not buffer.strip():
                break
            buffer += chunk

            while True:
                stripped = buffer.lstrip()
                if not started:
                    if not stripped:
                        break
                    if stripped[0] != "[":
                        raise ValueError(f"Expected JSON array in {path}")
                    buffer = stripped[1:]
                    started = True
                    continue

                stripped = buffer.lstrip()
                if stripped.startswith("]"):
                    return
                if stripped.startswith(","):
                    buffer = stripped[1:]
                    continue
                if not stripped:
                    break

                try:
                    item, index = decoder.raw_decode(stripped)
                except json.JSONDecodeError:
                    if not chunk:
                        raise
                    break

                yield item
                buffer = stripped[index:]
