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
`scripts/fetch_corpus.py` do `data/raw/`:

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

## Starter

Projekt jest forkiem startera RAG `idm-rag-starter` przygotowanego przez prowadzącego kurs.
Oryginalny README startera: [README.starter.md](README.starter.md).
