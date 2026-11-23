# darkbench-indic

Does Indic post-training change how often a model uses dark patterns? This repo runs
[DarkBench](https://github.com/apartresearch/darkbench) (Apart Research, ICLR 2025) on two
models built from the same base model:

- `mistralai/mistral-small-3.1-24b-instruct`: general post-training
- `sarvamai/sarvam-m`: post-trained on English and Indic languages

It then runs a 60-prompt Bengali pilot. All inference goes through OpenRouter, with a
$25 credit limit set on the API key.

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
results/english/          tidy CSVs, charts
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
- Nothing is published or pushed to a public remote without the project owner's approval.
