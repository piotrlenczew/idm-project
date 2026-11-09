# AGENTS.md

Kontekst dla agentów kodujących (Claude Code, Codex, Cursor, Copilot…) pracujących w tym repo.
Czytaj w całości przed zmianami. Instrukcje dla ludzi: `README.md`.

## Cel projektu

Aplikacja wspierająca naukę na podstawie dostarczonych materiałów: odpowiada na pytania opierając
twierdzenia modelu na cytowanych fragmentach źródeł. Projekt zespołowy (2 osoby) na kurs
„Inżynieria dużych modeli językowych” (WEiTI PW), zbudowany na starterze RAG od prowadzącego.
Działa lokalnie (Ollama + Qdrant) i jest używana z terminala – bez frontendu.

Wykłady Missing Semester 2026 i MIT 6.0001 to przykładowy zestaw materiałów do nauki używany do oceny jakości aplikacji
(pobierany przez `scripts/fetch_corpus.py`).

Etapy projektu:
1. działający end-to-end na przykładowych materiałach,
2. złoty zestaw pytań i ewaluacja,
3. poprawa jakości (retrieval, chunking, prompt),
4. tool calling (narzędzia do ustalenia).

Wybieraj proste, jawne rozwiązania zamiast sprytnych abstrakcji. Repo musi działać na laptopach 8–16 GB
(macOS/Windows/Linux).

## Architektura

```
cli.py ──► ingest.py ──► normalize.py ──► chunking.py ──► embeddings.py ──► store.py (Qdrant)
   │
   ├─► generate.py ──► retrieve.py ──► embeddings.py, store.py
   │        └────────► structured.py ──► llm.py (OpenAI SDK, base_url z .env)
   ├─► agent.py ────► retrieve.py (narzędzie search_docs), llm.py
   ├─► eval.py ─────► retrieve.py, generate.py
   └─► check.py ────► wszystko powyżej (smoke test)
config.py – jedyne źródło ustawień (dataclass `Settings` z .env)
```

Dane i skrypty:
- `data/raw/<źródło>/` – korpus pobierany przez `scripts/fetch_corpus.py` (poza repozytorium);
  to domyślny `DATA_DIR`, który indeksuje `make ingest`.
- `data/sample/` – mały zestaw do testów (używa go `eval/golden_sample.jsonl`). **Nie indeksuj go
  razem z korpusem.**
- `scripts/` – `fetch_corpus.py` (tylko pobiera pliki), `show_blocks.py` (wynik parsowania przed
  chunkingiem).

Kluczowe kontrakty:
- **Chunk payload** w Qdrancie: `text`, `source`, `page`|`section`, `source_ids` (lista), `chunking`,
  `chunk_index`, `embed_model`. Wektor nazwany `dense` (miejsce na sparse `bm25`).
- **`source_ids`** są niezależne od chunkingu (`plik.pdf#p3`, `plik.md#Sekcja`, `plik.txt`);
  złote zbiory w `eval/*.jsonl` się do nich odwołują. Zmiana formatu = aktualizacja złotych zbiorów.
- **Cytowania**: model zwraca numery fragmentów kontekstu (`Answer.citations`), mapowanie na źródła
  robi kod (`RagResult.cited_hits`). Nie każ modelowi przepisywać nazw plików.
- **Structured output**: zawsze przez `structured.complete_structured()` (`auto`: native → prompt;
  `tool` tylko jawnie w `.env`). Nie wywołuj `response_format` bezpośrednio – nie działa na Ollamie z runnerem MLX.

## Komendy

```bash
make setup | pull | up | down          # środowisko
make check                             # smoke test (wymaga Ollamy i Qdranta)
make ingest [DATA=...] [ARGS=...]      # uv run rag ingest (domyślnie DATA_DIR=data/raw)
make ask Q="..." | make agent Q="..."  # uv run rag ask / agent
uv run python scripts/fetch_corpus.py  # pobranie korpusu do data/raw/
uv run python scripts/show_blocks.py [ścieżki] [--full]  # wynik parsowania, bez Ollamy i Qdranta
make eval [ARGS=--generate]            # uv run rag eval
make test                              # pytest, bez sieci – uruchamiaj po każdej zmianie
make lint                              # ruff check + ruff format --check
```

Przed zakończeniem pracy: `make lint && make test`. Jeśli zmieniasz retrieval, chunking albo prompt –
także `make eval` i porównaj z poprzednim wynikiem w `eval/results/`.

## Konwencje

- Python 3.12, `uv` (zależności tylko przez `uv add`), typy w sygnaturach, docstring w każdym
  module i publicznej funkcji. Ruff (`line-length = 100`).
- Docstringi, komentarze i komunikaty dla użytkownika **po polsku**, ale terminy techniczne
  **po angielsku**: embedding, chunk, chunking, retrieval, reranking, bag of words, prompt, tool calling.
  Nie tłumacz ich („osadzenie”, „fragmentacja” – źle).
- Małe moduły o jednej odpowiedzialności; nowe techniki jako osobne funkcje włączane flagą/ustawieniem,
  a nie przepisanie istniejących.
- Nowe ustawienie = pole w `Settings` + wpis w `.env.example` z komentarzem + wiersz w README.
- Testy jednostkowe nie mogą wymagać sieci, Ollamy ani Qdranta (atrapy jak w `tests/test_structured.py`,
  Qdrant `:memory:`).
- Błędy dla użytkownika: `RuntimeError`/`ValueError` z komunikatem „co się stało + jak naprawić”
  (CLI wypisuje je bez tracebacka).
- Commity małe i logiczne, opis po polsku lub angielsku, bez sekretów.

## Czego NIE robić

- **Nie uruchamiaj Ollamy w Dockerze** – na Macu brak dostępu do Metal (GPU). `docker-compose.yml`
  jest tylko dla Qdranta.
- **Nie dodawaj LangChaina, LlamaIndexa ani innych frameworków RAG/agentowych** – cały sens repo
  to jawny, zrozumiały kod. LLM i embeddingi wyłącznie przez SDK `openai` z `base_url`.
- **Nie instaluj niczego globalnie** (`pip install`, `brew install`, `npm -g`) bez pytania użytkownika.
- **Nie commituj** `.env`, kluczy API, `data/raw/*` (poza `manifest.json`/`.gitkeep`), `eval/results/*`, `.qdrant/`.
- Nie zmieniaj `EMBED_MODEL` w kodzie ani domyślnych wartości bez ponownego ingestu i aktualizacji README.
- Nie ustawiaj domyślnie thinkingu (`LLM_REASONING_EFFORT`) na nic innego niż `none` – qwen3.5
  z thinkingiem odpowiada ~100× wolniej.
- Nie zakładaj, że `response_format` / `tool_choice` są respektowane przez każdy serwer.
- Nie wstawiaj do kodu twardych adresów usług (LLM, embeddingi, Qdrant), kluczy ani nazw modeli poza
  `config.py` / `.env`. Adresy źródeł korpusu mieszkają tylko w `scripts/fetch_corpus.py`.
