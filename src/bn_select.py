"""Phase 5 step 1: pick the 60 English prompts for the Bengali pilot.

10 per category, drawn with random.Random(SEED) from the 660 DarkBench prompts. A prompt
is eligible only if all three models have a valid main-judge verdict (dark, dark_egregious
or clean) in all three Phase 3 epochs, so every Bengali item has a complete English
baseline to compare against item by item.

Writes bengali/prompts_en.csv: sample_id, category, prompt, and the English dark rate per
model over the 3 epochs (the matched baseline).
"""

from __future__ import annotations

import pathlib
import random

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = 20261123
PER_CATEGORY = 10
VALID = {"dark", "dark_egregious", "clean"}


def main() -> None:
    df = pd.read_csv(ROOT / "results/english/samples.csv")
    df["valid"] = df.judge_verdict.isin(VALID)
    df["dark"] = df.judge_verdict.isin({"dark", "dark_egregious"})
    per_prompt = df.groupby(["sample_id", "category"]).agg(n=("valid", "size"), n_valid=("valid", "sum"))
    eligible = per_prompt[(per_prompt.n == 9) & (per_prompt.n_valid == 9)].reset_index()
    print(f"eligible prompts: {len(eligible)} of {per_prompt.shape[0]}")

    rng = random.Random(SEED)
    picks = []
    for cat in sorted(eligible.category.unique()):
        ids = sorted(eligible[eligible.category == cat].sample_id)
        picks += rng.sample(ids, PER_CATEGORY)

    sel = df[df.sample_id.isin(picks)]
    rates = sel.pivot_table(index="sample_id", columns="model", values="dark", aggfunc="mean").add_prefix("en_dark_rate_")
    prompts = sel.drop_duplicates("sample_id").set_index("sample_id")[["category", "prompt"]]
    out = prompts.join(rates).loc[picks].reset_index()
    out.to_csv(ROOT / "bengali/prompts_en.csv", index=False, encoding="utf-8-sig")
    print(out.groupby("category").size().to_string())
    print(out.filter(like="en_dark_rate_").mean().round(3).to_string())


if __name__ == "__main__":
    main()
