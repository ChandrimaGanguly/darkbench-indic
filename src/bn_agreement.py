"""Phase 5 step 6: Cece's labels on 20 Bengali responses vs judging methods A and B.

Inputs:  bengali/labels_bn.csv (Cece's yes/no), bengali/key_bn.csv (model, verdicts A/B)
Output:  bengali/agreement_bn.md
Invalid judge verdicts are dropped from that method's comparison and counted.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from agreement import kappa

ROOT = pathlib.Path(__file__).resolve().parent.parent
B = ROOT / "bengali"


def main() -> None:
    lab = pd.read_csv(B / "labels_bn.csv", encoding="utf-8-sig", dtype=str).fillna("")
    key = pd.read_csv(B / "key_bn.csv", encoding="utf-8-sig")
    df = key.merge(lab[["item_id", "dark_pattern_yes_no", "note"]], on="item_id")
    df["human"] = df.dark_pattern_yes_no.str.strip().str.lower().map({"yes": True, "no": False})
    assert df.human.notna().all() and len(df) == 20
    out = ["# Bengali pilot: judge vs human (20 responses)\n",
           f"Cece: {int(df.human.sum())}/20 dark.\n",
           "| Method | n valid | invalid dropped | Agreement | Cohen's κ | judge dark | human dark | human dark / judge clean | human clean / judge dark |",
           "|---|---|---|---|---|---|---|---|---|"]
    for m in ["A", "B"]:
        g = df[df[f"verdict_{m}"] != "invalid"]
        j = g[f"verdict_{m}"] == "dark"
        h = g.human.astype(bool)
        out.append(f"| {m} | {len(g)} | {len(df) - len(g)} | {(j == h).mean():.0%} | {kappa(h, j):.2f} | "
                   f"{int(j.sum())} | {int(h.sum())} | {int((h & ~j).sum())} | {int((~h & j).sum())} |")
    out += ["", "## Disagreements\n",
            df[(df.verdict_A != "invalid") & ((df.verdict_A == "dark") != df.human) |
               (df.verdict_B != "invalid") & ((df.verdict_B == "dark") != df.human)]
            [["item_id", "category", "model", "human", "verdict_A", "verdict_B", "note"]].to_markdown(index=False), ""]
    (B / "agreement_bn.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
