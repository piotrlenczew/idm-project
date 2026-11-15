"""Interaktywna ręczna ocena odpowiedzi z przebiegu ewaluacji (`rag eval --generate`).

Dla każdego pytania skrypt pokazuje pytanie, oczekiwaną odpowiedź (ze złotego zestawu, po `id`),
odpowiedź modelu i tekst cytowanych chunków (odtworzony z korpusu na podstawie `start`/`length`).
Oceniający wybiera jedną z ocen:
- `poprawna` – odpowiedź zgodna z oczekiwaną,
- `błędna` – odpowiedź zła, niepełna albo odmowa na pytanie, na które materiały odpowiadają,
- `poprawna_odmowa` – odmowa na pytanie spoza materiałów (tylko pytania `out_of_scope`),
albo pomija pytanie na później.

Stanem jest sam plik ocen obok wyników (`<wyniki>.grades.jsonl`): każda ocena od razu trafia do
niego (w kolejności pytań z wyników), a kolejne uruchomienie pokazuje tylko pytania jeszcze
nieocenione. `--summary` wypisuje zestawienie ocen, łącznie i dla każdego tagu.

Użycie:
    uv run python scripts/grade_answers.py eval/first_version/<wyniki>.json
    uv run python scripts/grade_answers.py eval/first_version/<wyniki>.json --summary
"""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from rag.ingest import discover_files, load_file, normalize_blocks, source_ids_for

GRADES = {"p": "poprawna", "b": "błędna", "o": "poprawna_odmowa"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Wiersze pliku JSONL (puste linie pomijane; brak pliku = pusta lista)."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def block_texts(data_dir: Path) -> dict[str, str]:
    """Tekst bloków korpusu po `source_id` – ten sam, w którym liczone są `start`/`length`."""
    texts = {}
    for path in discover_files([data_dir]):
        for block in normalize_blocks(load_file(path)):
            texts[source_ids_for(block.metadata)[0]] = block.text
    return texts


def chunk_text(chunk: dict[str, Any], texts: dict[str, str]) -> str:
    """Tekst chunka odtworzony z korpusu (albo komunikat, gdy się nie da)."""
    block = texts.get(chunk["source_ids"][0])
    if block is None or chunk.get("start") is None:
        return "(nie da się odtworzyć tekstu – brak bloku w korpusie albo `start`)"
    return block[chunk["start"] : chunk["start"] + chunk["length"]]


def show(row: dict[str, Any], gold: dict[str, Any], top_k: int, texts: dict[str, str]) -> None:
    """Wypisuje wszystko, czego potrzeba do oceny jednego pytania."""
    print(f"\nPytanie: {row['question']}")
    print(f"\nOczekiwana odpowiedź: {gold['answer']}")
    print(f"Oczekiwane źródła: {', '.join(gold['source_ids']) or '– (spoza materiałów)'}")
    print(f"\nOdpowiedź modelu: {row['answer']}")
    context = row["retrieved"][:top_k]  # model widział pierwsze TOP_K chunków
    for n, chunk in enumerate(context, start=1):
        cited = n in row["citations"]
        print(f"\n[{n}] {', '.join(chunk['source_ids'])}{' (cytowany)' if cited else ''}")
        if cited:
            print(chunk_text(chunk, texts))


def summary(grades: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> None:
    """Zestawienie ocen: wszystkie pytania i osobno każdy tag."""
    tags = sorted({tag for row in rows for tag in row["tags"]})
    groups = [("wszystkie", rows), *((t, [r for r in rows if t in r["tags"]]) for t in tags)]
    for name, group in groups:
        counts = Counter(grades[r["id"]]["grade"] for r in group if r["id"] in grades)
        graded = sum(counts.values())
        parts = [f"{g} {counts[g]} ({counts[g] / graded:.0%})" for g in GRADES.values() if graded]
        print(f"{name}: ocenione {graded}/{len(group)}" + "".join(f" · {p}" for p in parts))


def main() -> None:
    """Prowadzi oceniającego przez nieocenione odpowiedzi albo wypisuje zestawienie."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # pyright: ignore[reportOptionalMemberAccess]
    parser.add_argument("results", type=Path, help="plik wyników `rag eval --generate` (.json)")
    parser.add_argument("--golden", type=Path, default=Path("eval/golden.jsonl"))
    parser.add_argument("--summary", action="store_true", help="tylko zestawienie ocen")
    args = parser.parse_args()

    data = json.loads(args.results.read_text(encoding="utf-8"))
    rows = data["rows"]
    out = args.results.with_name(f"{args.results.stem}.grades.jsonl")
    grades = {g["id"]: g for g in read_jsonl(out)}
    if args.summary:
        summary(grades, rows)
        return

    gold = {item["id"]: item for item in read_jsonl(args.golden)}
    texts = block_texts(Path(data["config"]["data_dir"]))
    todo = [r for r in rows if r["id"] not in grades]
    for number, row in enumerate(todo, start=1):
        print(f"\n===== [{number}/{len(todo)}] {row['id']}  ({', '.join(row['tags'])})")
        if row.get("error"):
            print(f"Brak odpowiedzi (błąd: {row['error']}) – pomijam.")
            continue
        show(row, gold[row["id"]], data["config"]["top_k"], texts)
        out_of_scope = not gold[row["id"]]["source_ids"]
        keys = "[p]oprawna / [b]łędna / " + ("p[o]prawna odmowa / " if out_of_scope else "")
        while True:
            choice = input(f"\n{keys}[s]kip / [q]uit: ").strip().lower()
            if choice in ("p", "b", "s", "q") or (choice == "o" and out_of_scope):
                break
        if choice == "q":
            break
        if choice == "s":
            continue
        note = input("Uwaga (opcjonalnie, Enter = brak): ").strip()
        grades[row["id"]] = {"id": row["id"], "grade": GRADES[choice], "note": note}
        # zapis od razu i w kolejności pytań z wyników (a nie oceniania), żeby plik był czytelny
        ordered = [grades[r["id"]] for r in rows if r["id"] in grades]
        out.write_text(
            "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in ordered), encoding="utf-8"
        )
    print()
    summary(grades, rows)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrzerwano – zapisane oceny zostają w pliku.")
