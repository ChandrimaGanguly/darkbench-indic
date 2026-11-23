"""Phase 4 steps 3-5: agreement between the human annotator, the main judge and the second judge.

Inputs:  validation/to_label.csv   (the annotator's yes/no in column dark_pattern_yes_no)
         validation/key.csv        (main judge verdicts)
         logs/phase4_second_judge/ (second judge verdicts)
Output:  validation/agreement_numbers.md (tables), and the same printed to stdout.

Binary verdicts: dark = judge value 1 or 2; clean = 0. Items where a judge returned
invalid or failed are dropped from that pair's comparison and counted.
Cohen's kappa = (p_o - p_e) / (1 - p_e). With 10 items per category, per-category kappa
is very noisy: treat it as a flag, not a measurement.
"""

from __future__ import annotations

import glob
import pathlib

import pandas as pd
from inspect_ai.log import read_eval_log

ROOT = pathlib.Path(__file__).resolve().parent.parent
YES = {"yes", "y", "1", "true", "dark"}
NO = {"no", "n", "0", "false", "clean"}


def kappa(a: pd.Series, b: pd.Series) -> float:
    a, b = a.astype(bool), b.astype(bool)
    n = len(a)
    if n == 0:
        return float("nan")
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def second_judge() -> pd.DataFrame:
    rows = []
    for f in glob.glob(str(ROOT / "logs/phase4_second_judge/*.eval")):
        for s in read_eval_log(f).samples:
            sc = next(iter(s.scores.values()))
            rows.append({"item_id": s.id, "second_value": sc.value, "second_explanation": sc.explanation})
    return pd.DataFrame(rows)


def to_bool(v) -> bool | None:
    if v in (-1,):
        return None
    return bool(v) if v in (0, 1, 2, True, False) else None


def load() -> pd.DataFrame:
    key = pd.read_csv(ROOT / "validation/key.csv")
    key["main"] = key.judge_verdict.map({"dark": True, "dark_egregious": True, "clean": False})
    df = key.merge(second_judge(), on="item_id", how="left")
    df["second"] = df.second_value.map(to_bool)
    labels = pd.read_csv(ROOT / "validation/to_label.csv", encoding="utf-8-sig")
    lab = labels.dark_pattern_yes_no.map(lambda v: "" if pd.isna(v) else str(v)).str.strip().str.lower()
    labels["human"] = lab.map(lambda x: True if x in YES else False if x in NO else None)
    return df.merge(labels[["item_id", "human", "note", "prompt", "response"]], on="item_id")


def pair_table(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    out = []
    for cat, g in [("OVERALL", df)] + list(df.groupby("category")):
        g = g.dropna(subset=[a, b])
        out.append({"category": cat, "n": len(g),
                    "agreement": (g[a].astype(bool) == g[b].astype(bool)).mean() if len(g) else float("nan"),
                    "kappa": kappa(g[a], g[b]),
                    f"{a}_dark": int(g[a].astype(bool).sum()), f"{b}_dark": int(g[b].astype(bool).sum())})
    return pd.DataFrame(out)


def fmt(t: pd.DataFrame) -> str:
    t = t.copy()
    t["agreement"] = t.agreement.map(lambda x: f"{x:.0%}")
    t["kappa"] = t.kappa.map(lambda x: f"{x:.2f}")
    return t.to_markdown(index=False)


def main() -> None:
    df = load()
    n_lab = df.human.notna().sum()
    parts = [f"# Judge agreement numbers\n\nHuman labels filled: {n_lab}/60. "
             f"Second judge invalid/failed: {df.second.isna().sum()}.\n"]
    if n_lab:
        parts += ["## Human vs main judge (claude-haiku-5.5)\n", fmt(pair_table(df, "human", "main")), ""]
        parts += ["## Human vs second judge (gpt-6-luna)\n", fmt(pair_table(df, "human", "second")), ""]
    parts += ["## Main judge vs second judge\n", fmt(pair_table(df, "main", "second")), ""]
    text = "\n".join(parts)
    (ROOT / "validation/agreement_numbers.md").write_text(text)
    print(text)
    if n_lab:
        dis = df[df.human.notna() & (df.human != df.main)]
        dis[["item_id", "category", "model", "human", "main", "second", "note", "judge_explanation"]].to_csv(
            ROOT / "validation/disagreements_human_vs_main.csv", index=False)
        print(f"{len(dis)} human-vs-main disagreements -> validation/disagreements_human_vs_main.csv")


if __name__ == "__main__":
    main()
