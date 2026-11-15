# Przebieg bazowy (E1)

Pierwszy pomiar systemu na złotym zestawie `eval/golden.jsonl` (110 pytań), bez żadnych ulepszeń –
punkt odniesienia dla kolejnych etapów. Retrieval (recall@k, MRR) i generacja odpowiedzi
(`--generate`); poprawność treści odpowiedzi nie jest jeszcze oceniona.

Ustawienia aplikacji (modele, `TOP_K`, chunking, temperature…) są w polu `config` pliku JSON.

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
