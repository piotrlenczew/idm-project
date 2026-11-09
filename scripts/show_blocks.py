"""Pokazuje wynik parsowania dokumentów: bloki (sekcje Markdowna, strony PDF) przed chunkingiem.

Użycie: `uv run python scripts/show_blocks.py [ścieżki...] [--full]`
Domyślnie czyta `DATA_DIR` z `.env`; bez `--full` pokazuje tylko początek każdego bloku.
"""

import argparse
from pathlib import Path

from rag.config import get_settings
from rag.ingest import discover_files, load_file, source_ids_for

parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # pyright: ignore[reportOptionalMemberAccess]
parser.add_argument("paths", nargs="*", help="pliki lub katalogi")
parser.add_argument("--full", action="store_true", help="pokaż cały tekst bloków")
args = parser.parse_args()

for path in discover_files([Path(p) for p in args.paths or [get_settings().data_dir]]):
    for block in load_file(path):
        text = block.text if args.full else block.text[:100].replace("\n", " ")
        print(f"--- {source_ids_for(block.metadata)[0]} ({len(block.text)} znaków)\n{text}")
