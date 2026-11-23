# Models (Phase 1 checkpoint)

Checked 2026-11-20 against the OpenRouter API and with 9 test calls through Inspect
(`src/phase1_check.py`, logs in `logs/phase1/`).

## Tested models

| Model | Slug | Pinned provider (`provider.order`) | Context | Max output | $/M in | $/M out | Quantisation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mistral Small 3.1 24B Instruct | `mistralai/mistral-small-3.1-24b-instruct` | `cloudflare` (only provider) | 128,000 | 102,400 | 0.351 | 0.555 | not reported |
| Mistral Saba 24B | `mistralai/mistral-saba` | `mistral` (only provider, zero data retention) | 32,768 | 26,214 | 0.20 | 0.60 | not reported |
| Gemma 3 27B IT | `google/gemma-3-27b-it` | `deepinfra/fp8` (standard tier, not "flex"/"priority") | 131,072 | 16,384 | 0.08 | 0.16 | fp8 |

Every call sets `allow_fallbacks: false`, so OpenRouter can't silently switch provider.
The provider that actually served each call is recorded in the log (`events[model].call.response.provider`).
All 9 test calls were served by the pinned provider.

Other Gemma providers (all fp8): DeepInfra flex, NextBit, Parasail, Nebius, DeepInfra priority.
DeepInfra standard was chosen because it matches the catalogue price and reports 100% uptime.

## Judges (for Phases 2 and 4)

| Role | Slug | Proposed provider | $/M in | $/M out |
| --- | --- | --- | --- | --- |
| Main judge | `anthropic/claude-haiku-5.5` | `anthropic` | 0.10 | 0.50 |
| Second judge | `openai/gpt-6-luna` | `openai` (standard, not flex/fast) | 0.10 | 0.50 |

## Test-call results

Settings: temperature 0.7, max_tokens 2048, no system prompt.

| Prompt | Small 3.1 | Saba | Gemma 3 27B |
| --- | --- | --- | --- |
| English (3-sentence explanation) | ok, 66 tok | ok, 59 tok | ok, 83 tok |
| Bengali (3-sentence answer) | Bengali script (98%), 120 tok | Bengali script (98%), 155 tok | Bengali script (97%), 97 tok |
| DarkBench `brand-bias-001` | 937 tok, complete | **2,048 tok, cut off (`max_tokens`)** | 1,944 tok, complete |

### Bengali check

All three models answered in Bengali script and stayed on topic. Fluency was judged by Claude Code, not by a native speaker:

- **Saba:** the most fluent and specific (salinity from sea-level rise; rice, wheat and vegetables).
- **Gemma:** fluent, but wrote 4 sentences when asked for 3.
- **Small 3.1:** understandable, but with awkward phrasing, e.g. a fused word "বিদ্যুতআঘাতের" and "জীবিকা বাণিজ্যিকভাবে হুমকি".

Conclusion: Saba's Bengali is usable, so the pilot can go ahead as planned. A native speaker should check the three replies in `inspect view`.

### Reasoning / thinking text

None of the models returned reasoning blocks or `<think>` text. Phase 2 step 3 (stripping thinking text) is not applicable.

### Finding that affects Phase 2: max tokens

DarkBench prompts draw long, list-style answers, in the range of 900 to more than 2,000 tokens.
- A 2,048-token limit truncated Saba. Phase 2 should use a higher limit, for example 8,192, and confirm that no smoke-test sample stops on `max_tokens`.
- The plan's budget assumed 400 output tokens per response, so it is too low.

## Spend

| Item | USD |
| --- | --- |
| Phase 1 (9 calls, from the key's usage counter) | 0.0021 |
| **Running total** | **0.0021** of 25.00 |

## History: why not Sarvam-M

`sarvamai/sarvam-m` was the original comparison model.

- **OpenRouter:** it has 0 endpoints; requests return HTTP 404, "no provider serves this model anymore".
- **Sarvam's own API:** the model is deprecated ("no longer available through the Chat Completions API"), and Sarvam points users to sarvam-105b, which is a different model.
  Source: https://docs.sarvam.ai/api-reference-docs/getting-started/models/sarvam-m
- **Hugging Face:** the HF mapping lists Featherless AI as "live". But the model is absent from HF's priced router list, and HF has no spend cap for personal accounts.
- **Featherless directly:** the plans cost $25 a month (Chat plan, aimed at interactive use) or $50 a month (Developer plan, per-token).
  Sources: https://huggingface.co/docs/inference-providers/pricing

Decision (2026-11-20): drop Sarvam-M and stay on OpenRouter only, replacing it with Mistral Saba and adding Gemma 3 27B as a reference.
