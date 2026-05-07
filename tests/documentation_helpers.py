from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
THREATENED_SPECIES_DOC = PROJECT_ROOT / "docs/agentes/especies_ameacadas_brasil.md"


def documented_fields(section_title: str) -> list[str]:
    text = THREATENED_SPECIES_DOC.read_text(encoding="utf-8")
    section_start = text.index(f"### `{section_title}`")
    fields_start = text.index("```text", section_start) + len("```text")
    fields_end = text.index("```", fields_start)
    return [
        line.strip()
        for line in text[fields_start:fields_end].splitlines()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", line.strip())
    ]
