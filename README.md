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

1. **E1 – system bazowy** (zrobione, [opis niżej](#etap-1-system-bazowy)): działający end-to-end
   na przykładowych materiałach, zestaw testowy (110 pytań) i pierwszy pomiar,
2. **E2 – poprawa jakości**: retrieval, chunking, prompt, parsowanie PDF; pomiar na tym samym
   zestawie i porównanie z E1,
3. **E3 – agent z tool callingiem**: model sam wybiera narzędzia; porównanie z E2 na tym samym
   zestawie.

## Uruchomienie

Wymagania: [Ollama](https://ollama.com/) zainstalowana natywnie (nie w Dockerze) z oknem kontekstu
`OLLAMA_CONTEXT_LENGTH=8192` (jak je ustawić:
[README startera](README.starter.md#okno-kontekstu-ollamy--koniecznie-przeczytaj)), Docker (Qdrant)
i [uv](https://docs.astral.sh/uv/).

```bash
make setup                              # zależności (uv) i .env z .env.example
make pull                               # modele Ollamy z .env
make up                                 # Qdrant w Dockerze
make check                              # smoke test: Ollama, modele, Qdrant, embedding, RAG, tool calling
uv run python scripts/fetch_corpus.py   # pobranie materiałów do data/raw/
make ingest                             # chunking, embedding i zapis do Qdranta
make ask Q="What is the difference between git fetch and git pull?"
```

Na słabym GPU z małą ilością VRAM Ollama może przerywać generację błędem
`CUDA error: the launch timed out` (watchdog GPU w Windows). Wtedy pomaga uruchomienie Ollamy
na CPU (`CUDA_VISIBLE_DEVICES=-1` w środowisku usługi Ollamy) – wolniej, ale stabilnie.

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

## Etap 1: system bazowy

### Temat i dane

System pomaga uczyć się z dostarczonych materiałów: student zadaje pytanie po angielsku,
a aplikacja odpowiada na podstawie fragmentów materiałów i wskazuje je jako źródła (`[n]`).
Gdy materiały nie zawierają odpowiedzi, odmawia zamiast zgadywać. Przykładowe materiały to
notatki z 9 wykładów Missing Semester 2026 (Markdown) i slajdy z 12 wykładów MIT 6.0001 (PDF) –
dwa różne formaty i dwa różne style tekstu (ciągła proza vs krótkie punkty na slajdach)
([Dane](#dane)). Projekt nie używa fine-tuningu – modelem bazowym jest
`qwen3.5:4b` z promptem.

### Zadanie agenta w E3

Agent dostaje te same pytania co system bazowy, ale sam decyduje, jak szukać w materiałach.
Planowane narzędzia, każde wymierzone w słabość widoczną w pomiarze bazowym:

| narzędzie | co robi | co ma poprawić |
|---|---|---|
| `search_docs(query, k, course?, lecture?)` | wyszukiwanie semantyczne z opcjonalnym filtrem po kursie / wykładzie | trafienia z niewłaściwego kursu, recall@1 |
| `keyword_search(query)` | wyszukiwanie leksykalne (BM25) | pytania o konkretne komendy i flagi (`git stash`, `-fsanitize=thread`) |
| `read_source(source_id)` | cała sekcja / strona PDF zamiast pojedynczego chunka | pytania `multi`, ucięte chunki |
| `list_sources(course?)` | spis wykładów i sekcji | wybór filtra, odmowa na pytania spoza materiałów |

Porównanie z E2 na tym samym zestawie: te same metryki i ręczna ocena, a dodatkowo liczba
i rodzaj wywołań narzędzi oraz czas odpowiedzi.

### Działający start

Pytanie przechodzi przez cały system zgodnie z [Uruchomieniem](#uruchomienie):
`make check` → `make ingest` (materiały z `data/raw/`, bez próbek startera) → `make ask`.
Zmiany względem startera potrzebne do własnych danych:
- `scripts/fetch_corpus.py` pobiera materiały do `DATA_DIR` (wersja Missing Semester przypięta
  do commita, żeby korpus był powtarzalny),
- ingest obsługuje kilka korpusów w podkatalogach `DATA_DIR`, a `source_ids` zawierają ścieżkę
  względem niego (`mit-6-0001/MIT6_0001F16_Lec1.pdf#p3`); Markdown parsuje biblioteka, a powtórzone
  nagłówki dostają numer (`#Debugging (2)`), żeby źródła były jednoznaczne,
- prompty i komunikaty, które widzi model, są po angielsku – tak jak materiały i pytania,
- `scripts/show_blocks.py` pokazuje wynik parsowania przed chunkingiem (bez Ollamy i Qdranta).

### Przykłady testowe

110 pytań w `eval/golden.jsonl`: 80 łatwych, 20 wymagających dwóch fragmentów i 10 spoza
materiałów ([Zbiór testowy](#zbiór-testowy)). Każde ma oczekiwaną odpowiedź i oczekiwane źródła
(`source_ids`). Pytania powstały przed pierwszym uruchomieniem systemu na tych materiałach,
pisane własnymi słowami, a nie zdaniami z materiałów. Po pomiarze poprawiliśmy tylko usterki
w samym zestawie (ucięte pytania i odpowiedzi, literówki, błędny termin w pytaniu), a nie
oczekiwane wyniki pod odpowiedzi systemu.

### Pomiar bazowy

Przebieg zapisany w [`eval/first_version/`](eval/first_version/README.md) (wyniki, ustawienia
w polu `config`, ręczne oceny i środowisko). Konfiguracja: `qwen3.5:4b`, embedding
`qwen3-embedding:0.6b`, chunking `recursive` (600 znaków, overlap 100), `TOP_K=4`, temperature 0.
To nie są wartości domyślne z `.env.example` (800 / 120 / `TOP_K=5`) – żeby odtworzyć pomiar, ustaw
w `.env` `CHUNK_SIZE=600`, `CHUNK_OVERLAP=100`, `TOP_K=4` i zrób `make ingest ARGS=--recreate`.

Metryki automatyczne:

| | pytań | recall@1 | recall@5 | MRR | refusal_ok | citation_hit | inline_cited | kontekst [znaki] | czas [s] |
|---|---|---|---|---|---|---|---|---|---|
| **wszystkie** | 110 | 0.67 | 0.89 | 0.82 | 0.94 | 0.87 | 0.65 | 1436 | 3.04 |
| easy | 80 | 0.74 | 0.96 | 0.83 | 0.96 | 0.89 | 0.61 | 1466 | 3.14 |
| multi | 20 | 0.38 | 0.60 | 0.79 | 0.90 | 0.80 | 0.80 | 1296 | 3.23 |
| out_of_scope | 10 | – | – | – | 0.80 | – | – | 1478 | 1.83 |
| Missing Semester | 50 | 0.77 | 0.94 | 0.89 | 0.96 | 0.92 | 0.72 | 1650 | 2.99 |
| MIT 6.0001 | 50 | 0.56 | 0.84 | 0.75 | 0.94 | 0.82 | 0.58 | 1214 | 3.33 |

Ręczna ocena poprawności (wszystkie 110 pytań):

| | ocenionych | poprawna | błędna | poprawna odmowa |
|---|---|---|---|---|
| **wszystkie** | 110 | 81 (74%) | 19 (17%) | 10 (9%) |
| easy | 80 | 72 (90%) | 8 (10%) | – |
| multi | 20 | 9 (45%) | 11 (55%) | – |
| out_of_scope | 10 | – | – | 10 (100%) |
| Missing Semester | 50 | 42 (84%) | 8 (16%) | – |
| MIT 6.0001 | 50 | 39 (78%) | 11 (22%) | – |

Wnioski (kierunki dla E2):
- **pytania `multi`** to najsłabszy punkt (45% poprawnych): drugi oczekiwany fragment zwykle nie
  trafia do kontekstu (recall@5 = 0.60); miejsce zajmują strony tytułowe PDF-ów i nakładające się
  chunki z tej samej strony,
- **PDF-y** wypadają gorzej w retrievalu (recall@1 0.56 vs 0.77): parsowanie gubi ligatury
  („Ame” zamiast „time”), indeksy górne (`O(nc)` zamiast O(n^c)) i miesza kolumny,
- **odmowy** są poprawne we wszystkich 10 przypadkach, ale automatyczne `refusal_ok` daje 0.80 –
  model czasem odmawia w tekście, a mimo to podaje cytowania (odmowa jest wykrywana po pustej
  liście cytowań),
- **błędy rozumowania** przy dobrym kontekście są rzadkie (np. odwrócenie kierunku „for → while”),
  a znaczniki `[n]` w tekście ma tylko 65% odpowiedzi.

## Starter

Projekt jest forkiem startera RAG `idm-rag-starter` przygotowanego przez prowadzącego kurs.
Oryginalny README startera: [README.starter.md](README.starter.md).
