# Przebieg bazowy (E1)

Pierwszy pomiar systemu na złotym zestawie `eval/golden.jsonl` (110 pytań), bez żadnych ulepszeń –
punkt odniesienia dla kolejnych etapów. Retrieval (recall@k, MRR), generacja odpowiedzi
(`--generate`) i ręczna ocena poprawności odpowiedzi (`*.grades.jsonl`,
`scripts/grade_answers.py`). Wyniki i wnioski: [README – Pomiar bazowy](../../README.md#pomiar-bazowy).

Ustawienia aplikacji (modele, `TOP_K`, chunking, temperature…) są w polu `config` pliku JSON.

Dwa pytania (`missing-semester/debugging-profiling.md:multi-1`,
`mit-6-0001/MIT6_0001F16_Lec12.pdf:multi-1`) w pierwszym przebiegu skończyły się błędem Ollamy
(„model runner has unexpectedly stopped”). Uruchomiono je ponownie (`--golden` z tymi dwoma
pytaniami, commit `8a8f440` – bez zmian w retrievalu, prompcie i chunkingu, ten sam indeks
i `config`) i ich wiersze zastąpiły wiersze z błędem; średnie przeliczono.

Po poprawkach w złotym zestawie (commity `6865165`, `b820353`) cztery pytania zmieniły treść:
`mit-6-0001/MIT6_0001F16_Lec2.pdf:multi-1` i `Lec8.pdf:multi-1` (były ucięte), `Lec12.pdf:multi-1`
(„bisection sort” → „bisection search”) i `Lec6.pdf:multi-1` (literówki, „additional step” →
„addition step”). Uruchomiono je ponownie z aktualną treścią (commit `efb3d27`, bez zmian
w retrievalu, prompcie i chunkingu, ten sam indeks i `config`), ich wiersze zastąpiły poprzednie,
średnie przeliczono, a wszystkie cztery odpowiedzi oceniono (`Lec2` i `Lec8` po raz pierwszy,
`Lec12` i `Lec6` ponownie).

## Środowisko

| co | wartość |
|---|---|
| commit kodu | `14068d4` |
| Ollama | 0.40.15 |
| LLM | `qwen3.5:4b` (Q4_K_M), digest `d8b0f5e9760c` |
| embedding | `qwen3-embedding:0.6b` (Q8_0), digest `ac6da0dfba84` |
| okno kontekstu (`OLLAMA_CONTEXT_LENGTH`) | 8192 |
| sprzęt | GPU NVIDIA (CUDA) z 6 GB VRAM, 8 GB RAM dla WSL2 |
| system | Windows 11 + WSL2 (Ubuntu 24.04) |
