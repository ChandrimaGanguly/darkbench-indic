"""Phase 6 steps 1-2: charts and the paired Small 3.1 vs Saba test.

Inputs:  results/english/rates.csv, results/english/samples.csv, bengali/samples_bn.csv
Outputs: results/charts/english_rates.png     rate per category per model, 95% CI whiskers
         results/charts/bengali_vs_english.png matched English vs Bengali (method A) rates
         results/mcnemar.md                    Small 3.1 vs Saba, per category

McNemar (exact, two-sided): each prompt is one pair. A model's verdict on a prompt is the
majority of its valid verdicts over the 3 epochs; prompts with a tie (e.g. 1 dark, 1 clean,
1 invalid) or no valid verdict for either model are dropped and counted. Only the discordant
prompts (one model dark, the other clean) carry information; p = exact binomial test of
those against 50/50. Six categories are tested, so p-values are reported as context, with a
Holm-adjusted column, not as the headline.
"""

from __future__ import annotations

import math
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHARTS = ROOT / "results/charts"
MODELS = ["mistral-small-3.1", "mistral-saba", "gemma-3-27b"]
LABEL = {"mistral-small-3.1": "Mistral Small 3.1", "mistral-saba": "Mistral Saba", "gemma-3-27b": "Gemma 3 27B"}
COLOR = {"mistral-small-3.1": "#2a78d6", "mistral-saba": "#eb6834", "gemma-3-27b": "#1baf7a"}  # validated slots 1-3
INK, MUTED, GRID, SURFACE = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
CATS = ["anthropomorphization", "brand_bias", "harmful_generation", "sneaking", "sycophancy", "user_retention"]
CAT_LABEL = {c: c.replace("_", " ").capitalize() for c in CATS}


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def english_chart() -> None:
    r = pd.read_csv(ROOT / "results/english/rates.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=SURFACE)
    style(ax)
    x = np.arange(len(CATS) + 1)
    cats = ["OVERALL"] + CATS
    w = 0.26
    for i, m in enumerate(MODELS):
        g = r[r.model == m].set_index("category").loc[cats]
        pos = x + (i - 1) * (w + 0.02)
        ax.bar(pos, g.rate * 100, width=w, color=COLOR[m], label=LABEL[m], edgecolor=SURFACE, linewidth=1)
        ax.errorbar(pos, g.rate * 100, yerr=[(g.rate - g.ci_low) * 100, (g.ci_high - g.rate) * 100],
                    fmt="none", ecolor=INK, elinewidth=1, capsize=2.5)
        for p, v in zip(pos[:1], g.rate[:1]):  # label only the overall bars
            ax.text(p, v * 100 + 6, f"{v:.0%}", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_xticks(x, ["Overall"] + [CAT_LABEL[c] for c in CATS], fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Responses judged dark (%)", color=MUTED)
    ax.set_title("English DarkBench: dark-pattern rate by category (660 prompts × 3 epochs, 95% CI)",
                 loc="left", color=INK, fontsize=11)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "english_rates.png", dpi=160)
    plt.close(fig)


def bengali_chart() -> None:
    df = pd.read_csv(ROOT / "bengali/samples_bn.csv", encoding="utf-8-sig")
    # English: all matched rows (as in bengali/rates.md); Bengali: invalid verdicts excluded.
    rows = [(LABEL[m], g) for m, g in df.groupby("model")] + [("", None)] + \
           [(CAT_LABEL[c], g) for c, g in df.groupby("category")]
    rows = [r for r in rows if r[1] is None or len(r[1])]
    fig, ax = plt.subplots(figsize=(8, 5.6), facecolor=SURFACE)
    style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ys = np.arange(len(rows))[::-1]
    for y, (name, g) in zip(ys, rows):
        if g is None:
            continue
        v = g[g.verdict_A != "invalid"]
        en, bn = g.en_rate.mean() * 100, (v.verdict_A == "dark").mean() * 100
        ax.plot([en, bn], [y, y], color=GRID, linewidth=2, zorder=1)
        ax.scatter(en, y, s=70, facecolor=SURFACE, edgecolor=MUTED, linewidth=2, zorder=3,
                   label="English" if y == ys[0] else None)
        ax.scatter(bn, y, s=70, color="#2a78d6", edgecolor=SURFACE, linewidth=2, zorder=3,
                   label="Bengali (judge reads Bengali)" if y == ys[0] else None)
        ax.text(max(en, bn) + 2.5, y, f"{en:.0f}% → {bn:.0f}%", va="center", fontsize=8.5, color=MUTED)
    ax.set_yticks(ys, [n for n, _ in rows], fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Responses judged dark (%)", color=MUTED)
    ax.set_title("Bengali pilot: matched items, English vs Bengali\n"
                 "(58 prompts; English = 3 epochs, Bengali = 1; ~10 prompts per category per model)",
                 loc="left", color=INK, fontsize=10.5)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS / "bengali_vs_english.png", dpi=160)
    plt.close(fig)


def binom_two_sided(k: int, n: int) -> float:
    if n == 0:
        return float("nan")
    pk = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    return min(1.0, sum(p for p in pk if p <= pk[k] * (1 + 1e-9)))


def mcnemar() -> None:
    s = pd.read_csv(ROOT / "results/english/samples.csv")
    s = s[s.model.isin(["mistral-small-3.1", "mistral-saba"]) & s.judge_verdict.isin(["dark", "dark_egregious", "clean"])]
    s["dark"] = s.judge_verdict != "clean"
    agg = s.groupby(["category", "sample_id", "model"]).dark.agg(["sum", "count"]).reset_index()
    agg["maj"] = np.where(agg["sum"] * 2 > agg["count"], 1, np.where(agg["sum"] * 2 < agg["count"], 0, -1))
    wide = agg.pivot_table(index=["category", "sample_id"], columns="model", values="maj").reset_index()
    rows = []
    for cat in CATS:
        g = wide[wide.category == cat]
        ok = g.dropna()
        ok = ok[(ok["mistral-small-3.1"] >= 0) & (ok["mistral-saba"] >= 0)]
        b = int(((ok["mistral-saba"] == 1) & (ok["mistral-small-3.1"] == 0)).sum())
        c = int(((ok["mistral-saba"] == 0) & (ok["mistral-small-3.1"] == 1)).sum())
        rows.append({"category": cat, "prompts": len(ok), "dropped": 110 - len(ok),
                     "Small dark": int(ok["mistral-small-3.1"].sum()), "Saba dark": int(ok["mistral-saba"].sum()),
                     "only Saba dark": b, "only Small dark": c, "p": binom_two_sided(min(b, c), b + c)})
    t = pd.DataFrame(rows)
    order = t.p.sort_values().index
    holm, running = pd.Series(index=t.index, dtype=float), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, t.p[i] * (len(t) - rank)))
        holm[i] = running
    t["p (Holm)"] = holm
    t["direction"] = np.select([t["only Saba dark"] > t["only Small dark"], t["only Saba dark"] < t["only Small dark"]],
                               ["Saba higher", "Small higher"], "equal")
    fmt = t.copy()
    for col in ("p", "p (Holm)"):
        fmt[col] = fmt[col].map(lambda p: "<0.001" if p < 0.001 else f"{p:.3f}")
    n_diff = int((t["p (Holm)"] < 0.05).sum())
    text = ("# Mistral Small 3.1 vs Mistral Saba: paired test per category (English)\n\n"
            "Each prompt is one pair; a model's verdict is its majority over 3 epochs (ties dropped). "
            "Exact McNemar on the discordant prompts. 110 prompts per category.\n\n"
            + fmt.to_markdown(index=False)
            + f"\n\n{n_diff} of 6 categories show a difference that survives a Holm correction at 0.05.\n")
    (ROOT / "results/mcnemar.md").write_text(text)
    print(text)


def main() -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    english_chart()
    bengali_chart()
    mcnemar()


if __name__ == "__main__":
    main()
