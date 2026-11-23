"""Phase 5 step 2: translate the 60 pilot prompts into Bengali and check for meaning drift.

Pipeline, per prompt in bengali/prompts_en.csv:
  1. Forward: FORWARD model translates English -> Bengali. Brand names, tone and the
     adversarial intent of the prompt are kept.
  2. Back: BACK model (a different family) translates the Bengali -> English, without
     seeing the original.
  3. Drift check: BACK model compares the original with the back-translation and rates
     drift ok / minor / major, with a one-line reason.

Neither model is one of the three tested models. Refusals are logged, never worked around:
if the forward model doesn't return Bengali text, the item is marked translator_refused and
skipped for steps 2-3.

Writes:
  bengali/translations_review.csv   what the human reviewer fills (review_status, prompt_bn_final, reviewer_note)
  logs/phase5_translate/calls.jsonl raw request/response metadata for every API call, incl. cost

Run:  .venv/bin/python src/bn_translate.py
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORWARD = "anthropic/claude-opus-5.5"
BACK = "google/gemini-2.5-pro"
LOG = ROOT / "logs/phase5_translate/calls.jsonl"
OUT = ROOT / "bengali/translations_review.csv"
BENGALI = re.compile(r"[ঀ-৿]")

FORWARD_PROMPT = """You are translating prompts from an AI-safety benchmark (DarkBench) into Bengali, so that the \
same test can be run on chatbots in Bengali. Translate the user prompt below into natural, fluent Bengali \
(Bangladesh/West Bengal standard written register) as a native speaker would actually type it to a chatbot.

Rules:
- Keep the meaning, tone, register and any adversarial or manipulative intent exactly. Do not soften, \
strengthen, add or remove anything.
- Keep brand, product, company and model names (e.g. ChatGPT, Mistral, Google) in their original Latin spelling.
- If the prompt asks the chatbot to rephrase, summarise or edit a quoted text, translate the quoted text too.
- Output only the Bengali translation, with no preamble, notes or quotation marks around it.

Prompt to translate:
{text}"""

BACK_PROMPT = """Translate the following Bengali text into English as literally as possible while staying \
grammatical. Keep names as written. Output only the English translation.

{text}"""

DRIFT_PROMPT = """An English prompt was translated into Bengali and then back into English by a different \
translator. Compare the ORIGINAL with the BACK-TRANSLATION. Judge whether the Bengali version would test \
the same thing: same request, same meaning, same tone, same adversarial or manipulative intent, same \
brand names. Ignore harmless wording differences.

ORIGINAL:
{orig}

BACK-TRANSLATION:
{back}

Reply with JSON only: {{"drift": "ok" | "minor" | "major", "reason": "<one short sentence>"}}"""


def client() -> OpenAI:
    if "OPENROUTER_API_KEY" not in os.environ:
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                os.environ["OPENROUTER_API_KEY"] = line.split("=", 1)[1].strip().strip('"')
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])


def call(c: OpenAI, model: str, prompt: str, step: str, sample_id: str) -> str:
    for attempt in range(4):
        try:
            r = c.chat.completions.create(
                model=model, temperature=0, max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"usage": {"include": True}},
            )
            text = (r.choices[0].message.content or "").strip()
            u = r.usage.model_dump() if r.usage else {}
            with LOG.open("a") as f:
                f.write(json.dumps({"sample_id": sample_id, "step": step, "model": model,
                                    "provider": getattr(r, "provider", None),
                                    "finish_reason": r.choices[0].finish_reason, "usage": u,
                                    "output": text}, ensure_ascii=False) + "\n")
            return text
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  retry {sample_id} {step}: {type(e).__name__}: {e}")
            time.sleep(2 ** attempt * 3)
    return ""


def one(c: OpenAI, row: pd.Series) -> dict:
    sid, en = row.sample_id, row.prompt
    bn = call(c, FORWARD, FORWARD_PROMPT.format(text=en), "forward", sid)
    refused = len(BENGALI.findall(bn)) < max(5, len(en) // 20)
    out = {"sample_id": sid, "category": row.category, "prompt_en": en, "prompt_bn": bn,
           "translator_refused": refused, "back_translation_en": "", "drift": "", "drift_reason": ""}
    if refused:
        out["drift"] = "n/a"
        out["drift_reason"] = "forward translator did not return Bengali (logged, not worked around)"
        return out
    back = call(c, BACK, BACK_PROMPT.format(text=bn), "back", sid)
    out["back_translation_en"] = back
    raw = call(c, BACK, DRIFT_PROMPT.format(orig=en, back=back), "drift", sid)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        d = {}
    out["drift"] = d.get("drift", "parse_error")
    out["drift_reason"] = d.get("reason", raw[:200])
    return out


def main() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit(f"{OUT} already exists; it may hold review edits. Move it away to re-run.")
    prompts = pd.read_csv(ROOT / "bengali/prompts_en.csv", encoding="utf-8-sig")
    c = client()
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(lambda r: one(c, r), (r for _, r in prompts.iterrows())))
    df = pd.DataFrame(rows)
    df["review_status"] = ""     # reviewer: approve / fixed / reject
    df["prompt_bn_final"] = ""   # reviewer: corrected Bengali if fixed (leave blank if approved)
    df["reviewer_note"] = ""
    order = {"major": 0, "parse_error": 1, "n/a": 2, "minor": 3, "ok": 4}
    df = df.assign(_o=df.drift.map(order).fillna(1)).sort_values(["_o", "category", "sample_id"]).drop(columns="_o")
    df.to_csv(OUT, index=False, encoding="utf-8-sig")

    calls = [json.loads(line) for line in LOG.read_text().splitlines()]
    cost = sum((x["usage"] or {}).get("cost") or 0 for x in calls)
    print(df.drift.value_counts().to_string())
    print(f"refused: {int(df.translator_refused.sum())}  |  API calls: {len(calls)}  |  cost: ${cost:.4f}")


if __name__ == "__main__":
    main()
