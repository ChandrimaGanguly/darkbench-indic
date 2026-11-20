# Models (Phase 1, in progress)

Checked 2026-11-20 against the OpenRouter API (`/api/v1/models` and `/api/v1/models/{slug}/endpoints`).

## mistralai/mistral-small-3.1-24b-instruct: available

| Field | Value |
| --- | --- |
| Slug | `mistralai/mistral-small-3.1-24b-instruct` |
| Context length | 128,000 |
| Price | $0.351 / M input tokens, $0.555 / M output tokens |
| Providers | Cloudflare only (max output 102,400, quantization not reported) |
| Supported params | temperature, max_tokens, seed, top_p, stop, ... |

There is only one provider, so the provider is effectively pinned already.
It will still be pinned explicitly in the run config.

## sarvamai/sarvam-m: NOT available (blocker)

- The model page still exists ("Sarvam AI: Sarvam-M"), but it has **0 endpoints** for both
  `sarvamai/sarvam-m` and `sarvamai/sarvam-m:free`.
- A test request returns HTTP 404: "sarvamai/sarvam-m is no longer available on OpenRouter:
  no provider serves this model anymore."
- This is not caused by account privacy settings: the model has no endpoints at all.
- Searching the full catalogue (442 models) for "sarvam", "indic", "hindi" and "bengali"
  finds no other Indic fine-tune.

### Fallback check (2026-11-20)

- **Sarvam's own API: not possible.** The Sarvam-M page in Sarvam's docs is titled "Sarvam-M (Deprecated)". It says the model is "no longer available through the Chat Completions API" and points users to `sarvam-105b`. No deprecation date is given.
  Sarvam-105B is a different model, not a fine-tune of Mistral-Small-3.1-24B-Base, so it can't stand in for Sarvam-M in the base-vs-fine-tune comparison.
  Sources: https://docs.sarvam.ai/api-reference-docs/getting-started/models/sarvam-m, https://docs.sarvam.ai/api/pricing.md
- **Hugging Face Inference Providers: one live host.** On Hugging Face, `sarvamai/sarvam-m` is Apache-2.0, and its base model is `mistralai/Mistral-Small-3.1-24B-Base-2503`.
  The HF API (`/api/models/sarvamai/sarvam-m?expand[]=inferenceProviderMapping`) lists `featherless-ai` as `"status": "live"` for conversational use.
  Not yet checked: pricing, spend caps, and whether calls actually succeed. Using this host means a second account (an HF token).

- **HF route, billing check (2026-11-20).**
  - Sarvam-M is **not** in the HF router's public chat-model list (`GET https://router.huggingface.co/v1/models`, 161 models), even though the model page's mapping says "live".
  - HF passes provider prices through with no markup. Free accounts get no monthly credits and must buy credits; PRO accounts get $2/month.
  - HF only documents spending limits for Team and Enterprise organisations, not for personal accounts. So there is no equivalent of the OpenRouter key cap.
  - The Featherless pricing page (https://featherless.ai/pricing) could not be fetched (header overflow), so its plan structure is unknown.
  - Sources: https://huggingface.co/docs/inference-providers/pricing, https://huggingface.co/docs/inference-providers/providers/featherless-ai

Status: waiting for Cece to choose a fallback (see the plan, Phase 1, "Stop and ask").

## Spend

$0.00 (catalogue queries are free; the failed requests were not billed).
