"""Interaktywnie buduje zbiór testowych pytań: skrypt losuje bloki, pytania pisze człowiek.

Rozkład pytań jest ustalony w stałych poniżej. Liczba pytań danego typu w korpusie dzieli się między
pliki po równo (resztę dostają pliki z najdłuższym tekstem), a blok w pliku jest losowany.
Korpus to katalog, w którym leży plik. Każde miejsce w rozkładzie ma `id` złożone ze źródła
(`source_name`), typu i numeru (`missing-semester/agentic-coding.md:easy-2`, `out_of_scope-4`),
więc zmiana rozkładu nie zmienia znaczenia już napisanych pytań; pytania spoza nowego rozkładu
zostają w pliku. Dla każdego miejsca można napisać pytanie, wylosować inny blok
albo pominąć je na później.

Stanem jest sam plik wyjściowy: każde napisane pytanie od razu trafia do niego, a kolejne
uruchomienie zaczyna od pierwszego niewypełnionego (np. pominiętego) miejsca.

Użycie: `uv run python scripts/build_golden.py [--out eval/golden.jsonl]`
"""

import argparse
import json
import random
from pathlib import Path

from rag.config import get_settings
from rag.ingest import Block, discover_files, load_file, source_ids_for, source_name

PER_CORPUS = {"easy": 40, "multi": 10}  # liczba pytań danego typu w każdym korpusie
BLOCKS_PER_QUESTION = {"easy": 1, "multi": 2}  # bloki `multi` pochodzą z tego samego pliku
OUT_OF_SCOPE = 10  # pytania spoza materiałów (bez bloku, model powinien odmówić)
OUT_OF_SCOPE_ANSWER = "The materials do not cover this."
MIN_CHARS = 200  # krótsze bloki (strony tytułowe, stopki) nie są losowane


def split_evenly(total: int, lengths: dict[Path, int]) -> dict[Path, int]:
    """Dzieli `total` po równo między pliki; resztę dostają pliki z najdłuższym tekstem."""
    base, remainder = divmod(total, len(lengths))
    counts = dict.fromkeys(lengths, base)
    for path in sorted(lengths, key=lengths.__getitem__, reverse=True)[:remainder]:
        counts[path] += 1
    return counts


def plan_slots(files: dict[Path, list[Block]]) -> dict[str, tuple[Path | None, str]]:
    """Miejsca rozkładu {id: (plik, typ)} w stałej kolejności; plik `None` = poza materiałami."""
    slots: dict[str, tuple[Path | None, str]] = {}
    for corpus in sorted({path.parent.name for path in files}):
        lengths = {
            path: sum(len(b.text) for b in blocks)
            for path, blocks in files.items()
            if path.parent.name == corpus
        }
        counts = {kind: split_evenly(n, lengths) for kind, n in PER_CORPUS.items()}
        for path in sorted(lengths):
            for kind in PER_CORPUS:
                for n in range(1, counts[kind][path] + 1):
                    slots[f"{source_name(path)}:{kind}-{n}"] = (path, kind)
    for n in range(1, OUT_OF_SCOPE + 1):
        slots[f"out_of_scope-{n}"] = (None, "out_of_scope")
    return slots


def ask(prompt: str) -> str:
    """Pyta, dopóki użytkownik nie wpisze niepustej odpowiedzi."""
    while not (answer := input(prompt).strip()):
        pass
    return answer


def main() -> None:
    """Prowadzi użytkownika przez niewypełnione miejsca rozkładu."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # pyright: ignore[reportOptionalMemberAccess]
    parser.add_argument("--out", type=Path, default=Path("eval/golden.jsonl"), help="złoty zestaw")
    args = parser.parse_args()

    files = {path: load_file(path) for path in discover_files([Path(get_settings().data_dir)])}
    slots = plan_slots(files)
    lines = args.out.read_text(encoding="utf-8").splitlines() if args.out.exists() else []
    written = {item["id"]: item for item in map(json.loads, filter(str.strip, lines))}
    used = {sid for item in written.values() for sid in item["source_ids"]}
    todo = [qid for qid in slots if qid not in written]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    for number, qid in enumerate(todo, start=1):
        path, kind = slots[qid]
        blocks: list[Block] = []
        shown: set[str] = set()  # bloki już pokazane dla tego miejsca – redraw ich unika
        while True:
            print(f"\n===== [{number}/{len(todo)}] {qid}")
            if path:
                eligible = [b for b in files[path] if len(b.text) >= MIN_CHARS]
                candidates = [b for b in eligible if source_ids_for(b.metadata)[0] not in used]
                if len(candidates) < BLOCKS_PER_QUESTION[kind]:
                    candidates = eligible  # nieużyte się skończyły – losujemy też już użyte
                if len(candidates) < BLOCKS_PER_QUESTION[kind]:
                    print("Plik ma za mało bloków na to pytanie – pomijam.")
                    break
                fresh = [b for b in candidates if source_ids_for(b.metadata)[0] not in shown]
                if len(fresh) >= BLOCKS_PER_QUESTION[kind]:
                    candidates = fresh
                else:
                    shown.clear()  # wszystkie już były – zaczynamy od nowa
                blocks = random.sample(candidates, BLOCKS_PER_QUESTION[kind])
                shown.update(source_ids_for(b.metadata)[0] for b in blocks)
                for block in blocks:
                    print(f"\n--- {source_ids_for(block.metadata)[0]}\n{block.text}")
            choice = input("\n[w]rite / [r]edraw / [s]kip / [q]uit: ").strip().lower()
            if choice == "q":
                return
            if choice == "s":
                break
            if choice != "w":
                continue
            source_ids = [source_ids_for(b.metadata)[0] for b in blocks]
            question = ask("Question: ")
            answer = OUT_OF_SCOPE_ANSWER if path is None else ask("Answer: ")
            written[qid] = {
                "id": qid,
                "question": question,
                "answer": answer,
                "source_ids": source_ids,
                "tags": [kind, path.parent.name] if path else [kind],
            }
            used.update(source_ids)
            # zapis od razu i w kolejności rozkładu (a nie pisania), żeby plik był czytelny;
            # pytania spoza obecnego rozkładu (po zmianie stałych) zostają na końcu
            ordered = [written[q] for q in slots if q in written]
            ordered += [item for q, item in written.items() if q not in slots]
            args.out.write_text(
                "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered),
                encoding="utf-8",
            )
            break
    print(f"\nKoniec listy. Złoty zestaw: {args.out}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrzerwano – zapisane pytania zostają w pliku.")
