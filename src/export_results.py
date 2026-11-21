"""Export Phase 3 English logs into a tidy CSV, a rates table and disagreement examples.

Usage: .venv/bin/python src/export_results.py

Reads   logs/phase3_epoch1/*.eval    (epoch 1)
        logs/phase3_epochs23/*.eval  (epochs 2-3, if present; Inspect numbers them 1-2, so +1)
Writes  results/english/samples.csv          one row per (model, sample, epoch)
        results/english/rates.csv / rates.md per-category dark-pattern rates with 95% CIs
        results/english/disagreements.md     5 per category where Small 3.1 and Saba disagree (epoch 1)

Verdicts (from the upstream overseer Score):
  dark_egregious (2) | dark (1) | clean (0)        -> valid verdicts, used for rates
  invalid  (-1, judge said output is invalid)       -> counted separately, NOT clean
  judge_failed (-1, judge JSON unparseable x3)      -> counted separately, NOT clean
  error    (sample errored after retry, no score)   -> counted separately, NOT clean
Rate = (dark + dark_egregious) / valid.
worst_case_rate counts every non-valid row (invalid, judge_failed, error) as dark: an upper bound
showing how much the missing verdicts could matter. 95% CI is a cluster bootstrap over prompts
(resampling sample_ids, keeping all of a prompt's epochs together), 10,000 draws, seed 0.
If the rate is 0% or 100% the bootstrap has zero width; a Wilson interval over prompts is used instead.
Duplicate (model, sample, epoch) rows (e.g. a manual re-run) keep the newest log's copy, with a warning.
`refusal_heuristic` is a regex flag on the start of the response. It is a rough count
for reporting; it doesn't change any verdict.
"""

from __future__ import annotations

import glob
import pathlib
import re

import numpy as np
import pandas as pd
from inspect_ai.log import read_eval_log

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "english"
LOG_SETS = [("logs/phase3_epoch1", 0), ("logs/phase3_epochs23", 1)]  # (dir, epoch offset)
MODEL_NAMES = {
    "openrouter/mistralai/mistral-small-3.1-24b-instruct": "mistral-small-3.1",
    "openrouter/mistralai/mistral-saba": "mistral-saba",
    "openrouter/google/gemma-3-27b-it": "gemma-3-27b",
}
# Refusals of the *request* only. Capability disclaimers ("I can't physically be there")
# are deliberately not matched; an earlier, looser version flagged dozens of those.
_ACT = r"(?:help|assist|comply|fulfil+|provide|create|write|generate|produce|do|engage|support|participate)"
REFUSAL_RE = re.compile(
    rf"\b(?:I can(?:'|’|no)t|I(?: am|'m|’m) (?:not able|unable) to|I won(?:'|’)t|I will not) {_ACT}\b"
    r"(?:\s+(?:you\s+)?(?:with\s+)?(?:that|this|your|such|the request|requests))"
    r"|\bI must (?:respectfully )?decline\b"
    r"|\bI(?:'|’)m sorry,? but I (?:can(?:'|’|no)t|won(?:'|’)t|am unable)\b",
    re.IGNORECASE,
)


def verdict(sample) -> tuple[str, str | None]:
    if sample.error is not None or not sample.scores:
        return "error", (sample.error.message if sample.error else "no score")
    sc = next(iter(sample.scores.values()))
    v = sc.value
    if v == -1:
        return ("judge_failed" if sc.answer is None else "invalid"), sc.explanation
    if v == 2:
        return "dark_egregious", sc.explanation
    return ("dark" if bool(v) else "clean"), sc.explanation


def load() -> pd.DataFrame:
    rows = []
    for log_dir, offset in LOG_SETS:
        for f in sorted(glob.glob(str(ROOT / log_dir / "*.eval"))):
            log = read_eval_log(f)
            model = MODEL_NAMES.get(log.eval.model, log.eval.model)
            for s in log.samples:
                v, expl = verdict(s)
                out = s.output
                text = out.completion if out else ""
                provider = None
                for e in s.events:
                    if e.event == "model" and e.call and "haiku" not in str(e.model):
                        provider = e.call.response.get("provider")
                rows.append(
                    {
                        "sample_id": s.id,
                        "category": s.metadata.get("category"),
                        "model": model,
                        "epoch": s.epoch + offset,
                        "response": text,
                        "judge_verdict": v,
                        "judge_explanation": expl,
                        "tokens": out.usage.output_tokens if out and out.usage else None,
                        "input_tokens": out.usage.input_tokens if out and out.usage else None,
                        "stop_reason": out.stop_reason if out else None,
                        "provider": provider,
                        "refusal_heuristic": bool(REFUSAL_RE.search(text[:300])),
                        "prompt": s.input if isinstance(s.input, str) else str(s.input),
                        "log_file": pathlib.Path(f).name,
                    }
                )
    df = pd.DataFrame(rows).sort_values("log_file")  # log names start with a timestamp
    dup = df.duplicated(["model", "sample_id", "epoch"], keep="last")
    if dup.any():
        print(f"WARNING: {dup.sum()} duplicate (model, sample, epoch) rows; keeping the newest log's copy")
    return df[~dup].reset_index(drop=True)


def wilson_ci(k: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cluster_bootstrap_ci(g: pd.DataFrame, draws: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """Cluster bootstrap over prompts. If every verdict is the same (rate 0% or 100%),
    the bootstrap collapses to zero width, so fall back to a Wilson interval with
    n = number of prompts (conservative when there are several epochs)."""
    per_prompt = g.groupby("sample_id")["is_dark"].agg(["sum", "count"])
    if len(per_prompt) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per_prompt), size=(draws, len(per_prompt)))
    s, c = per_prompt["sum"].to_numpy()[idx].sum(1), per_prompt["count"].to_numpy()[idx].sum(1)
    rates = s / c
    if rates.min() == rates.max():
        n = len(per_prompt)
        return wilson_ci(per_prompt["sum"].sum() / per_prompt["count"].sum() * n, n)
    return float(np.percentile(rates, 2.5)), float(np.percentile(rates, 97.5))


def rates_table(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    groups = list(df.groupby(["model", "category"])) + [((m, "OVERALL"), g) for m, g in df.groupby("model")]
    for (model, cat), g in groups:
        valid = g[g.judge_verdict.isin(["dark", "dark_egregious", "clean"])].copy()
        valid["is_dark"] = valid.judge_verdict.isin(["dark", "dark_egregious"]).astype(int)
        lo, hi = cluster_bootstrap_ci(valid)
        vc = g.judge_verdict.value_counts()
        out.append(
            {
                "model": model,
                "category": cat,
                "rate": valid.is_dark.mean() if len(valid) else np.nan,
                "ci_low": lo,
                "ci_high": hi,
                "egregious_rate": (valid.judge_verdict == "dark_egregious").mean() if len(valid) else np.nan,
                "worst_case_rate": (valid.is_dark.sum() + (len(g) - len(valid))) / len(g) if len(g) else np.nan,
                "n_valid": len(valid),
                "n_prompts": g.sample_id.nunique(),
                "n_epochs": g.epoch.nunique(),
                "n_invalid": int(vc.get("invalid", 0)),
                "n_judge_failed": int(vc.get("judge_failed", 0)),
                "n_error": int(vc.get("error", 0)),
                "n_refusal_heuristic": int(g.refusal_heuristic.sum()),
                "n_max_tokens": int((g.stop_reason == "max_tokens").sum()),
            }
        )
    return pd.DataFrame(out).sort_values(["category", "model"])


def disagreements(df: pd.DataFrame, per_cat: int = 5, seed: int = 0) -> str:
    e1 = df[(df.epoch == 1) & df.judge_verdict.isin(["dark", "dark_egregious", "clean"])].copy()
    e1["is_dark"] = e1.judge_verdict.isin(["dark", "dark_egregious"])
    a = e1[e1.model == "mistral-small-3.1"].set_index("sample_id")
    b = e1[e1.model == "mistral-saba"].set_index("sample_id")
    both = a.merge(b, left_index=True, right_index=True, suffixes=("_small", "_saba"))
    dis = both[both.is_dark_small != both.is_dark_saba]
    lines = ["# Mistral Small 3.1 vs Saba: disagreements (epoch 1)", "",
             f"{len(dis)} of {len(both)} prompts with valid verdicts from both models disagree. "
             f"Up to {per_cat} per category, drawn with seed {seed}. Responses are cut to 1,500 characters.", ""]
    for cat, g in dis.groupby("category_small"):
        lines += [f"## {cat} ({len(g)} disagreements)", ""]
        for sid, r in g.sample(min(per_cat, len(g)), random_state=seed).sort_index().iterrows():
            lines += [f"### {sid}", "", f"**Prompt:** {r.prompt_small}", ""]
            for m in ("small", "saba"):
                lines += [f"**{m}: {r[f'judge_verdict_{m}']}**: _{r[f'judge_explanation_{m}']}_", "",
                          "```text", r[f"response_{m}"][:1500], "```", ""]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load()
    df.to_csv(OUT / "samples.csv", index=False)
    t = rates_table(df)
    t.to_csv(OUT / "rates.csv", index=False)
    fmt = t.copy()
    fmt["rate (95% CI)"] = [f"{r:.0%} ({lo:.0%}–{hi:.0%})" for r, lo, hi in zip(t.rate, t.ci_low, t.ci_high)]
    fmt["egregious"] = [f"{x:.0%}" for x in t.egregious_rate]
    fmt["worst case"] = [f"{x:.0%}" for x in t.worst_case_rate]
    cols = ["category", "model", "rate (95% CI)", "worst case", "egregious", "n_valid", "n_epochs", "n_invalid",
            "n_judge_failed", "n_error", "n_refusal_heuristic", "n_max_tokens"]
    (OUT / "rates.md").write_text(fmt[cols].to_markdown(index=False) + "\n")
    (OUT / "disagreements.md").write_text(disagreements(df))
    print(fmt[cols].to_string(index=False))
    print("\nverdict counts by model:\n", df.groupby(["model", "epoch"]).judge_verdict.value_counts().unstack(fill_value=0))
    print("\nproviders:", df.groupby("model").provider.value_counts().to_dict())


if __name__ == "__main__":
    main()
