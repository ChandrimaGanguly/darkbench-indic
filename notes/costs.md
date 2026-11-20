# Measured costs

## Phase 2 smoke test (12 samples per model, judge = claude-haiku-5.5)

Costs were computed from the token counts in the logs (`logs/phase2_smoke/`) × the catalogue prices, then projected to 660 samples.

| Model | Mean output tokens | Generation / 660 | Judge / 660 | **Per epoch** |
| --- | --- | --- | --- | --- |
| Mistral Small 3.1 | 367 | $0.14 | $0.22 | **$0.37** |
| Mistral Saba | 472 | $0.20 | $0.23 | **$0.42** |
| Gemma 3 27B | 850 | $0.09 | $0.32 | **$0.41** |
| **All 3 models** | | | | **$1.20 / epoch, $3.60 for 3 epochs** |

- The Phase 3 budget line is $5.00. The projection of $3.60 fits, with 28% headroom.
- The key's own usage counter rose by $0.0162 for these 36 samples plus judging. The log-based estimate was $0.0218, so the projection is on the conservative side.
- Longest response so far: 1,552 tokens. Nothing hit `max_tokens` = 8,192.

## Running spend (OpenRouter key usage counter)

| After | USD |
| --- | --- |
| Phase 1 | 0.0021 |
| Phase 2 (smoke test, 1 re-run sample, judge test) | ≈ 0.019 |
