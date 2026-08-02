"""Construye data/colombia_normas/constitucion.json desde texto oficial."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from legal_ui.iley_service import (  # noqa: E402
    CONSTITUCION_JSON,
    CORPUS_VERSION,
    _parse_constitution,
    _read_constitution_source,
)

SOURCE_URL = "https://www1.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125"


def main() -> None:
    raw = _read_constitution_source()
    corpus = _parse_constitution(raw)
    corpus["fuente"] = SOURCE_URL
    CONSTITUCION_JSON.parent.mkdir(parents=True, exist_ok=True)
    CONSTITUCION_JSON.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Versión: {CORPUS_VERSION}")
    print(f"Artículos: {len(corpus['articulos'])} -> {CONSTITUCION_JSON}")


if __name__ == "__main__":
    main()
