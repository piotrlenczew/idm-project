"""Pobiera korpus dokumentów do `DATA_DIR` (domyślnie `data/raw/`).

Skrypt TYLKO pobiera pliki – wselkie zmiany powinny być realizowane w dalszych etapach.

Korpus:
- Missing Semester 2026 (MIT): 9 notatek w Markdownie z repozytorium na GitHubie
  (przypięty commit `MS_COMMIT`),
- 6.0001 Introduction to Computer Science and Programming in Python (MIT, jesień 2016):
  slajdy 12 wykładów w PDF (pliki .py pominięte gdyż powtarzają zawartość wykładów, również pominięte transkrypcje).

Obie strony udostępniają materiały na licencji CC BY-NC-SA 4.0:
użycie jedynie niekomercyjnie, podając źródło.

Użycie: `uv run python scripts/fetch_corpus.py [--out {DATA_DIR}] [--force]`
"""

from __future__ import annotations

import argparse
import re
import urllib.error
import urllib.request
from pathlib import Path

from rag.config import get_settings

# Przypięta wersja notatek: `master` wciąż się zmienia, a złoty zestaw wskazuje konkretne sekcje.
MS_COMMIT = "1d695c94ccafdce3f06d6b9dfe3e6f106097693a"
MS_RAW_URL = (
    f"https://raw.githubusercontent.com/missing-semester/missing-semester/{MS_COMMIT}/_2026"
)
MS_DIR = "missing-semester"  # podkatalog w `DATA_DIR`
MS_LECTURES = (
    "course-shell",
    "command-line-environment",
    "development-environment",
    "debugging-profiling",
    "version-control",
    "shipping-code",
    "agentic-coding",
    "beyond-code",
    "code-quality",
)

MIT_HOST = "https://ocw.mit.edu"
MIT_BASE = f"{MIT_HOST}/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016"
MIT_DIR = "mit-6-0001"  # podkatalog w `DATA_DIR`
MIT_LECTURES = range(1, 13)


def download(url: str) -> bytes:
    """Pobiera `url` i zwraca zawartość; błąd sieci zamienia na `RuntimeError`."""
    request = urllib.request.Request(url, headers={"User-Agent": "idm-rag-corpus-fetcher"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(
            f"Nie udało się pobrać {url}: {e}. Sprawdź połączenie z internetem i uruchom skrypt "
            "ponownie – pobrane już pliki zostaną pominięte."
        ) from e


def mit_slides_url(lecture: int) -> str:
    """Adres PDF-a ze slajdami wykładu; nazwy plików na stronie MIT mają hash, więc czytamy go ze strony."""
    page = download(f"{MIT_BASE}/resources/mit6_0001f16_lec{lecture}/").decode("utf-8")
    match = re.search(rf'href="([^"]*_MIT6_0001F16_Lec{lecture}\.pdf)"', page)
    if match is None:
        raise RuntimeError(
            f"Nie znalazłem PDF-a ze slajdami wykładu {lecture} na stronie MIT. "
            "Strona mogła się zmienić – sprawdź ją w przeglądarce i zaktualizuj skrypt."
        )
    return MIT_HOST + match.group(1)


def corpus_files() -> dict[str, str]:
    """Pliki korpusu jako {ścieżka względem katalogu docelowego: adres źródła}; bez pobierania."""
    files = {f"{MS_DIR}/{name}.md": f"{MS_RAW_URL}/{name}.md" for name in MS_LECTURES}
    for lecture in MIT_LECTURES:
        files[f"{MIT_DIR}/MIT6_0001F16_Lec{lecture}.pdf"] = mit_slides_url(lecture)
    return files


def main() -> None:
    """Pobiera brakujące pliki korpusu."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # pyright: ignore[reportOptionalMemberAccess]
    parser.add_argument(
        "--out", type=Path, default=Path(get_settings().data_dir), help="katalog docelowy"
    )
    parser.add_argument("--force", action="store_true", help="pobierz ponownie istniejące pliki")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    files = corpus_files()
    for name, url in files.items():
        target = args.out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not args.force:
            print(f"pomijam (już pobrany): {target}")
            continue
        print(f"pobieram: {url}")
        partial = target.with_name(target.name + ".part")  # przerwane pobieranie nie zostaje
        partial.write_bytes(download(url))
        partial.replace(target)
    print(f"Gotowe: {len(files)} plików w {args.out}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        raise SystemExit(f"Błąd: {e}") from e
