"""Phase 4 step 1: draw 60 responses for hand-labelling.

10 per category: 5 the main judge called dark, 5 it called clean. They are spread across
the three models, rotating which model gets the extra item, and come from any epoch.
Within a category each prompt appears at most once. Responses the annotator already saw with their
verdicts (the epoch-1 Small/Saba examples in results/english/disagreements.md) are excluded,
so they can't anchor her labels. Only valid verdicts are drawn
(invalid, judge-failed and errored rows are excluded).
Seed 20261121.

Writes:
  validation/to_label.csv  what the annotator labels: no model name, no judge verdict
  validation/key.csv       item -> model, sample, epoch, main judge verdict (don't open before labelling)
"""

from __future__ import annotations

import pathlib
import random
import re

import pandas as pd
from darkbench.dark_patterns import DARK_PATTERNS
from darkbench.scorer import _get_model_info

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = 20261121
SLUGS = {
    "mistral-small-3.1": "openrouter/mistralai/mistral-small-3.1-24b-instruct",
    "mistral-saba": "openrouter/mistralai/mistral-saba",
    "gemma-3-27b": "openrouter/google/gemma-3-27b-it",
}
MODELS = list(SLUGS)


def definition(category: str, model: str) -> str:
    """The exact category description the judge saw, with {company}/{model} filled the same way."""
    info = _get_model_info(SLUGS[model])
    p = DARK_PATTERNS[category]
    return f"{p.display_name}: " + p.description.format(**info.model_dump())


def main() -> None:
    rng = random.Random(SEED)
    df = pd.read_csv(ROOT / "results/english/samples.csv")
    df = df[df.judge_verdict.isin(["dark", "dark_egregious", "clean"])].copy()
    df["judge_dark"] = df.judge_verdict != "clean"
    seen = set(re.findall(r"^### (\S+)", (ROOT / "results/english/disagreements.md").read_text(), re.M))
    already_seen = (df.epoch == 1) & df.model.isin(["mistral-small-3.1", "mistral-saba"]) & df.sample_id.isin(seen)
    print(f"excluding {already_seen.sum()} responses already shown in disagreements.md")
    df = df[~already_seen]

    picks = []
    for ci, cat in enumerate(sorted(df.category.unique())):
        used: set[str] = set()
        order = MODELS[ci % 3:] + MODELS[: ci % 3]          # rotate which model gets extra items
        slots = [(order[i % 3], True) for i in range(5)] + [(order[(i + 2) % 3], False) for i in range(5)]
        for model, dark in slots:
            for m in [model] + [x for x in MODELS if x != model]:  # fall back if a pool is empty
                pool = df[(df.category == cat) & (df.model == m) & (df.judge_dark == dark) & ~df.sample_id.isin(used)]
                if len(pool):
                    row = pool.iloc[rng.randrange(len(pool))]
                    used.add(row.sample_id)
                    picks.append(row)
                    break
            else:
                raise RuntimeError(f"no candidate for {cat} {model} dark={dark}")

    sel = pd.DataFrame(picks).sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle order
    sel["item_id"] = [f"L{i + 1:02d}" for i in range(len(sel))]
    sel["definition"] = [definition(c, m) for c, m in zip(sel.category, sel.model)]

    out = ROOT / "validation"
    out.mkdir(exist_ok=True)
    sheet = sel[["item_id", "category", "definition", "prompt", "response"]].copy()
    sheet["dark_pattern_yes_no"] = ""
    sheet["note"] = ""
    sheet.to_csv(out / "to_label.csv", index=False, encoding="utf-8-sig")  # BOM so Excel reads UTF-8
    sel[["item_id", "category", "model", "sample_id", "epoch", "judge_verdict", "judge_explanation"]].to_csv(
        out / "key.csv", index=False
    )
    print(sel.groupby(["category", "model", "judge_dark"]).size().unstack(fill_value=0))
    print("\ntotal", len(sel), "| judge dark", int(sel.judge_dark.sum()))


if __name__ == "__main__":
    main()
