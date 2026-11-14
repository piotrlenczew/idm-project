# idm-project

Aplikacja wspierająca naukę na podstawie dostarczonych materiałów: odpowiada na pytania, opierając
twierdzenia modelu na cytowanych fragmentach źródeł. Działa lokalnie (Ollama + Qdrant) i jest używana
z terminala.

Projekt zespołowy na kurs **Inżynieria dużych modeli językowych** (WEiTI PW).

## Autorzy

- Piotr Lenczewski
- Jakub Pęk

## Cel

Etapy projektu:

1. działający end-to-end na przykładowych materiałach,
2. złoty zestaw pytań i ewaluacja,
3. poprawa jakości (retrieval, chunking, prompt),
4. tool calling (narzędzia do ustalenia).

## Dane

Przykładowy zestaw materiałów do nauki to dwa kursy MIT. Pliki nie są w repozytorium, pobiera je
`scripts/fetch_corpus.py` do katalogu `DATA_DIR` (domyślnie `data/raw/`):

```bash
uv run python scripts/fetch_corpus.py
```

- [Missing Semester 2026](https://missing.csail.mit.edu/2026/) (MIT): 9 wykładów, notatki w Markdownie
  z repozytorium [missing-semester/missing-semester](https://github.com/missing-semester/missing-semester).
- [6.0001 Introduction to Computer Science and Programming in Python](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/)
  (MIT OpenCourseWare, jesień 2016): slajdy 12 wykładów w PDF.

Materiały są udostępnione na licencji
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) i są własnością ich autorów.
Używamy ich wyłącznie niekomercyjnie, do celów tego projektu.

## Zbiór testowy

Plik `eval/golden.jsonl` to zestaw pytań do ewaluacji aplikacji na przykładowych materiałach.
Zawiera 110 pytań po angielsku:

| typ | opis | Missing Semester | MIT 6.0001 | razem |
|---|---|---|---|---|
| `easy` | odpowiedź w jednym fragmencie (sekcji / stronie) | 40 | 40 | 80 |
| `multi` | odpowiedź wymaga dwóch fragmentów z tego samego wykładu | 10 | 10 | 20 |
| `out_of_scope` | odpowiedzi nie ma w materiałach, model powinien odmówić | – | – | 10 |

W każdym kursie pytania danego typu są rozdzielone po równo między wykłady, a pytania, które nie
dzielą się równo, trafiają do wykładów z najdłuższym tekstem.

Jak powstał: skrypt `scripts/build_golden.py` losuje fragment (lub dwa) z wykładu zgodnie z
powyższym rozkładem. Autor czyta go i pisze pytanie oraz odpowiedź własnymi słowami, a jeśli
fragment się nie nadaje, losuje inny albo odkłada go na później. Pytania spoza materiałów
pisze bez losowania.

```bash
uv run python scripts/build_golden.py
```

Format linii: `{"id", "question", "answer", "source_ids", "tags"}`:
- `id` – plik, typ i numer pytania tego typu w pliku, np. `missing-semester/version-control.md:easy-2`,
  `mit-6-0001/MIT6_0001F16_Lec3.pdf:multi-1`, `out_of_scope-4`,
- `source_ids` – fragmenty źródła (np. `missing-semester/version-control.md#Basics`, `mit-6-0001/MIT6_0001F16_Lec3.pdf#p7`),
- `tags` – typ pytania i korpus (`missing-semester` / `mit-6-0001`), np. `["easy", "mit-6-0001"]`;
  pytania `out_of_scope` mają tylko typ.

## Starter

Projekt jest forkiem startera RAG `idm-rag-starter` przygotowanego przez prowadzącego kurs.
Oryginalny README startera: [README.starter.md](README.starter.md).
