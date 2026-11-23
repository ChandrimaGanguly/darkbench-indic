"""Phase 5: English vs Bengali dark-pattern rates on the matched pilot items, and the
Bengali hand-labelling sheet.

Inputs:  bengali/prompts_en.csv          English baseline per item and model (mean of 3 epochs)
         bengali/prompts_bn_approved.csv the 58 approved items
         logs/phase5_bn_A/, logs/phase5_bn_B/
Outputs: bengali/samples_bn.csv          one row per item x model: Bengali response, English
                                         translation, verdicts A and B
         bengali/rates.md                rate tables
         bengali/to_label_bn.csv         20 Bengali responses for the annotator (no model, no verdicts)
         bengali/key_bn.csv              item -> model, sample, verdicts (don't open before labelling)

Verdicts: dark = 1 or 2, clean = 0, invalid = -1 (judge said the output looks invalid, or
failed). Invalid rows are excluded from rates and counted, as in the English analysis.
Only the 58 approved items enter the comparison; English rates are restricted to the same items.
"""

from __future__ import annotations

import glob
import pathlib
import random
import sys

import pandas as pd
from inspect_ai.log import read_eval_log

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = ROOT / "bengali"
SEED = 20261124
N_LABEL = 20
SHORT = {"mistral-small-3.1-24b-instruct": "mistral-small-3.1", "mistral-saba": "mistral-saba",
         "gemma-3-27b-it": "gemma-3-27b"}


def verdict(v) -> str:
    return "invalid" if v == -1 else "dark" if v in (1, 2, True) else "clean"


def load(method: str) -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(str(ROOT / f"logs/phase5_bn_{method}/*.eval"))):
        log = read_eval_log(f)
        model = SHORT[log.eval.model.split("/")[-1]]
        for s in log.samples:
            sc = next(iter(s.scores.values()))
            rows.append({"sample_id": s.id, "model": model, f"verdict_{method}": verdict(sc.value),
                         f"explanation_{method}": sc.explanation,
                         **({"response_bn": s.output.completion} if method == "A" else
                            {"response_en": s.metadata.get("response_en", "")})})
    return pd.DataFrame(rows)


def rate(s: pd.Series) -> str:
    v = s[s != "invalid"]
    return f"{(v == 'dark').mean():.0%} ({(v == 'dark').sum()}/{len(v)})" if len(v) else "n/a"


def main() -> None:
    items = pd.read_csv(B / "prompts_bn_approved.csv", encoding="utf-8-sig")
    en = pd.read_csv(B / "prompts_en.csv", encoding="utf-8-sig")
    en = en[en.sample_id.isin(items.sample_id)]
    en_long = en.melt(id_vars=["sample_id", "category"], value_vars=[c for c in en if c.startswith("en_dark_rate_")],
                      var_name="model", value_name="en_rate")
    en_long["model"] = en_long.model.str.replace("en_dark_rate_", "")

    df = load("A").merge(load("B"), on=["sample_id", "model"], how="outer")
    df = df.merge(items[["sample_id", "category", "prompt_en", "prompt_bn_approved"]], on="sample_id")
    df = df.merge(en_long[["sample_id", "model", "en_rate"]], on=["sample_id", "model"])
    df.to_csv(B / "samples_bn.csv", index=False, encoding="utf-8-sig")

    out = ["# Bengali pilot: English vs Bengali dark-pattern rates\n",
           f"{df.sample_id.nunique()} matched items x 3 models, 1 Bengali epoch. English = mean of the 3 "
           "Phase 3 epochs on the same items. Bengali A = judge reads Bengali; B = response translated to "
           "English (gemini-3-flash, reasoning off) and judged with the original English prompt. "
           "Invalid verdicts excluded and counted. ~10 items per cell: read as direction, not result.\n"]

    def table(group_cols: list[str]) -> str:
        rows = []
        groups = [("ALL", df)] if not group_cols else list(df.groupby(group_cols))
        for key, g in groups:
            rows.append({**({c: k for c, k in zip(group_cols, key if isinstance(key, tuple) else (key,))}
                            if group_cols else {"scope": "ALL"}),
                         "English": f"{g.en_rate.mean():.0%}",
                         "Bengali A": rate(g.verdict_A), "Bengali B": rate(g.verdict_B),
                         "invalid A/B": f"{(g.verdict_A == 'invalid').sum()}/{(g.verdict_B == 'invalid').sum()}"})
        return pd.DataFrame(rows).to_markdown(index=False)

    out += ["## Overall\n", table([]), "", "## By model\n", table(["model"]), "",
            "## By category\n", table(["category"]), "", "## By model and category\n",
            table(["model", "category"]), ""]
    both = df[(df.verdict_A != "invalid") & (df.verdict_B != "invalid")]
    agree = (both.verdict_A == both.verdict_B).mean()
    out += [f"## Method A vs method B\n\nAgreement on {len(both)} items where both are valid: {agree:.0%}. "
            f"A dark / B clean: {((both.verdict_A == 'dark') & (both.verdict_B == 'clean')).sum()}; "
            f"A clean / B dark: {((both.verdict_A == 'clean') & (both.verdict_B == 'dark')).sum()}.\n"]
    (B / "rates.md").write_text("\n".join(out))
    print("\n".join(out))

    # Hand-labelling sheet: 20 responses, spread over categories and models, drawn at random.
    # Written once. Re-drawing would orphan the existing hand labels, so it needs --new-sheet.
    if (B / "key_bn.csv").exists() and "--new-sheet" not in sys.argv:
        print("labelling sheet exists (bengali/key_bn.csv); not redrawn. Pass --new-sheet to redraw.")
        return
    rng = random.Random(SEED)
    cats, models = sorted(df.category.unique()), sorted(df.model.unique())
    slots = [(cats[i % len(cats)], models[(i + i // len(cats)) % len(models)]) for i in range(N_LABEL)]
    picks, used = [], set()
    for cat, model in slots:
        pool = df[(df.category == cat) & (df.model == model) & ~df.sample_id.isin(used)]
        r = pool.loc[rng.choice(list(pool.index))]
        used.add(r.sample_id)
        picks.append(r)
    lab = pd.DataFrame(picks).reset_index(drop=True)
    lab["item_id"] = [f"B{i + 1:02d}" for i in range(len(lab))]
    lab = lab.sample(frac=1, random_state=SEED).reset_index(drop=True)
    from build_label_sheet import definition
    lab["definition"] = [definition(c, m) for c, m in zip(lab.category, lab.model)]
    sheet = lab[["item_id", "category", "definition", "prompt_bn_approved", "response_bn"]].rename(
        columns={"prompt_bn_approved": "prompt_bn"})
    sheet["dark_pattern_yes_no"] = ""
    sheet["note"] = ""
    sheet.to_csv(B / "to_label_bn.csv", index=False, encoding="utf-8-sig")
    lab[["item_id", "category", "model", "sample_id", "verdict_A", "verdict_B", "en_rate"]].to_csv(
        B / "key_bn.csv", index=False, encoding="utf-8-sig")
    print(f"labelling sheet: {len(sheet)} items -> bengali/to_label_bn.csv")


if __name__ == "__main__":
    main()
