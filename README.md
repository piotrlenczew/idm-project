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
- `source_ids` – fragmenty źródła (np. `missing-semester/version-control.md#Basics`, `mit-6-0001/MIT6_0001F16_Lec3.pdf#p7`);
  sekcja, której nagłówek powtarza się w pliku, ma numer (`debugging-profiling.md#Debugging (2)`),
- `tags` – typ pytania i korpus (`missing-semester` / `mit-6-0001`), np. `["easy", "mit-6-0001"]`;
  pytania `out_of_scope` mają tylko typ.

## Ewaluacja

Działanie aplikacji mierzymy na zbiorze testowym na trzech poziomach: czy retrieval znajduje
właściwe fragmenty, jak model korzysta z kontekstu i czy odpowiedź jest poprawna.

```bash
make eval ARGS=--generate   # uv run rag eval --generate
```

Dla każdego pytania przebieg zapisuje odpowiedź modelu, numery cytowanych fragmentów, pobrane
fragmenty (źródło, podobieństwo i położenie w tekście) oraz metryki:

| metryka | co mierzy |
|---|---|
| `recall@k` (k = 1, 3, 5) | jaka część oczekiwanych źródeł jest wśród k pobranych fragmentów |
| `mrr` | 1 / pozycja pierwszego fragmentu z oczekiwanego źródła (0, gdy go nie ma) |
| `ctx_chars` | ile znaków kontekstu dostaje model (przy porównaniach recall ma sens tylko obok tego budżetu) |
| `refusal_ok` | czy model odpowiedział na pytanie z materiałów i odmówił na pytanie spoza nich (odmowa = brak cytowań) |
| `citation_hit` | czy wśród cytowanych fragmentów jest oczekiwane źródło |
| `inline_cited` | czy odpowiedź ma w tekście znaczniki źródeł `[n]` |
| `latency_s` | czas retrievalu i generacji |

Metryki retrievalu i cytowań liczone są tylko dla pytań z materiałów. Wyniki trafiają do
`eval/results/<czas>_<zbiór>_<kolekcja>_<model>.json` (wszystko, razem z ustawieniami w polu
`config`) i `.md` (tabela): najpierw średnie – łącznie i dla każdego tagu (typ pytania i korpus) –
potem wyniki pytań. Przebiegi, które zostają w repozytorium, leżą w osobnych katalogach
w `eval/` (np. `eval/first_version/`) z krótkim `README.md` opisującym przebieg i środowisko.

Poprawność odpowiedzi oceniają ludzie, porównując odpowiedź modelu z oczekiwaną:
`poprawna` / `błędna` / `poprawna_odmowa` (odmowa na pytanie spoza materiałów; odmowa na pytanie,
na które materiały odpowiadają, jest `błędna`). Skrypt pokazuje pytanie, oczekiwaną odpowiedź,
odpowiedź modelu i tekst cytowanych fragmentów:

```bash
uv run python scripts/grade_answers.py eval/first_version/<wyniki>.json
```

Oceny trafiają od razu do pliku obok wyników (`<wyniki>.grades.jsonl`, linia
`{"id", "grade", "note"}`), a kolejne uruchomienie pokazuje tylko pytania jeszcze nieocenione. `--summary` zlicza oceny łącznie i dla każdego tagu.

## Starter

Projekt jest forkiem startera RAG `idm-rag-starter` przygotowanego przez prowadzącego kurs.
Oryginalny README startera: [README.starter.md](README.starter.md).
