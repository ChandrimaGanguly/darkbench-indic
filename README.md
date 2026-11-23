# darkbench-indic

Does a model tuned for South Asian languages show dark patterns at different rates from a
general-purpose model of the same size from the same lab, and do the rates change when the
prompts are in Bengali? This repo runs
[DarkBench](https://github.com/apartresearch/darkbench) (Apart Research, ICLR 2025) on three
models:

- `mistralai/mistral-small-3.1-24b-instruct`: general-purpose
- `mistralai/mistral-saba`: Mistral's model tuned for South Asian and Middle Eastern languages
- `google/gemma-3-27b-it`: a different lab, as a reference point

It then runs a 58-prompt Bengali pilot, with human-reviewed translations. All inference goes
through OpenRouter, with a $25 credit limit set on the API key (total spend: $6.36).

The original plan compared Mistral Small 3.1 with Sarvam-M, which is post-trained from the
same base model. Sarvam-M is no longer served anywhere we could reach on this budget, so it was
replaced (see `notes/models.md`). Saba's base model and training are not published, so the
Small-vs-Saba comparison is descriptive, not causal.

## Results in brief

Full write-up, with methods and limitations: **[REPORT.md](REPORT.md)**.

| Model | English dark-pattern rate (95% CI) | Bengali pilot vs matched English |
|---|---|---|
| Mistral Small 3.1 | 20% (18–23%) | 21% → 47% |
| Mistral Saba | 34% (31–37%) | 43% → 58% |
| Gemma 3 27B | 51% (48–54%) | 60% → 59% |

- Saba is higher than Small in 4 of 6 categories (anthropomorphization, user retention, brand
  bias, sycophancy) and level on harmful generation and sneaking.
- The LLM judge is more lenient than a human annotator (κ 0.17 blind, 0.37 after review), so
  rates are best read as lower bounds.
- The Bengali pilot is small (about 10 prompts per category per model, 1 epoch): a direction
  to follow up, not a result.

## Setup

Requirements: [`uv`](https://docs.astral.sh/uv/), git, and an OpenRouter API key with a
$25 credit limit.

```bash
git clone --recurse-submodules <this-repo> darkbench-indic
cd darkbench-indic

# 1. Python 3.12 virtualenv
uv venv --python 3.12 .venv
source .venv/bin/activate

# 2. Pinned dependencies, plus upstream DarkBench as an editable install
uv pip install -r requirements.lock

# 3. API key (.env is git-ignored; never commit it)
cp .env.example .env    # then edit .env and set OPENROUTER_API_KEY

# 4. Sanity checks
inspect --version
git submodule status    # shows the pinned DarkBench commit
```

If you cloned without `--recurse-submodules`, run `git submodule update --init` before step 2.

## Pinned versions

| Component | Version |
| --- | --- |
| Python | 3.12 |
| inspect-ai | 0.3.291 |
| openai | 3.57.0 |
| DarkBench (`vendor/darkbench`, git submodule) | `7eef15102b37df2a15a6031cbbed6be488de7fbe` |

`requirements.lock` lists every package version.

## Layout

```
config/run_config.yaml    models, providers, judge, settings, commits
vendor/darkbench/         upstream, untouched, pinned commit (git submodule)
src/                      wrappers, Bengali task, analysis scripts
notes/                    model notes, how DarkBench scores
logs/                     Inspect .eval logs (all of them are kept)
results/english/          tidy CSVs, rate tables
results/charts/           charts used in REPORT.md
results/mcnemar.md        paired Small 3.1 vs Saba test
validation/               hand labels, judge agreement
bengali/                  prompts, translations, results
```

## Reproduce

```bash
./run_all.sh          # $0: rebuild every table, chart and agreement number from the committed logs and labels
./run_all.sh full     # ~$4: re-run all inference (English + Bengali A/B); old logs are archived first
```

Human steps (hand labels, translation review) are not re-run; `full` mode leaves the
agreement numbers describing the committed responses. Results are written up in `REPORT.md`.

## Rules

- Upstream code in `vendor/` is never edited. Any change in behaviour goes in `src/` as a wrapper.
