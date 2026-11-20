# DarkBench: general vs South-Asia-tuned models (revised plan, v2)

Nov 20, 2026 · @Cece · **Approved by Cece on 2026-11-20**

## What changed from v1, and why

Sarvam-M can't be reached on our budget:

- OpenRouter: no provider serves it any more (HTTP 404).
- Sarvam's own API: deprecated.
- The one other host (Featherless, through Hugging Face) needs a $25–50/month second account.

Details and sources are in `notes/models.md`. v2 stays on **OpenRouter only**, using the $25 of credit already bought.

| | v1 | v2 |
| --- | --- | --- |
| Comparison | Mistral Small 3.1 vs Sarvam-M (same base, Indic post-training) | Mistral Small 3.1 vs **Mistral Saba** (same lab and size, South-Asia-focused training), plus **Gemma 3 27B** as an outside reference |
| Claim strength | "Indic post-training changes X": close to causal, because the base is shared | "A regionally tuned model differs from its general sibling": descriptive only. Saba's base and training recipe aren't published |
| Thinking-text handling | Required (Sarvam-M is a hybrid reasoner) | Probably not needed. Check in Phase 1 |
| Phase 3 budget | $10 | $5 (measured prices are lower than v1 assumed) |

Phases 0 (done), 2, 4 and 6 are unchanged except where marked **[v2]**.

## Purpose

**Question:** does a model tuned for South Asian languages show dark patterns at different rates from a general-purpose model of the same size from the same lab, and do the rates shift when the prompts are in Bengali?

We run DarkBench on three models:

- Mistral Small 3.1 24B Instruct (general)
- Mistral Saba 24B (regionally tuned)
- Gemma 3 27B (open-weight, different lab, a reference point)

**Why:** this is a training run for Cece's own multilingual climate eval for South Asia. It practises every step that eval will need: running Inspect, checking an LLM judge against human labels, translating prompts, and writing up results.

**Done means:**

- Per-category dark-pattern rates for all three models in English, with confidence intervals
- A judge-agreement number from about 60 hand-labelled samples
- A 60-prompt Bengali pilot, with rates per model
- A short write-up and a reproducible repo, all under $25 in API spend

## Fixed decisions

These decisions are already made. Don't change them without asking Cece.

| Decision | Value |
| --- | --- |
| Compute | No GPU. Hosted inference only |
| API provider | OpenRouter only, one key (`OPENROUTER_API_KEY`) |
| Tested models **[v2]** | `mistralai/mistral-small-3.1-24b-instruct`, `mistralai/mistral-saba`, `google/gemma-3-27b-it` |
| Judge | A closed model that isn't from the Mistral or Gemma families, reached through OpenRouter. Proposed: `anthropic/claude-haiku-5.5` (confirmed in Phase 2) |
| Second judge (Phase 4) | A different family from the main judge. Proposed: `openai/gpt-6-luna` |
| Pilot language | Bengali |
| Total API budget | $25 hard cap, enforced as the credit limit on the OpenRouter key (verified: limit 25) |
| Framework | Inspect (`inspect-ai`), using Apart Research's DarkBench package |

**[v2] Prices on OpenRouter (2026-11-20, USD per million tokens):**

| Model | Input | Output | Context | Weights |
| --- | --- | --- | --- | --- |
| mistral-small-3.1-24b-instruct | 0.351 | 0.555 | 128K | open |
| mistral-saba | 0.20 | 0.60 | 32K | closed |
| gemma-3-27b-it | 0.08 | 0.16 | 131K | open |
| claude-haiku-5.5 (judge) | 0.10 | 0.50 | 1M | closed |
| gpt-6-luna (2nd judge) | 0.10 | 0.50 | 1M | closed |

The Gemma judge-family exclusion exists so that no tested model's own lab grades it.
Using Claude as the judge rather than Gemini also follows from this.

## Background for Claude Code

DarkBench ([paper](https://arxiv.org/abs/2503.10728), ICLR 2025) has 660 adversarial prompts in six dark-pattern categories:

- brand bias
- user retention
- sycophancy
- anthropomorphism
- harmful generation
- sneaking

Each model response is scored by an LLM annotator (the judge) as either showing the pattern or not.

- **Code:** [apartresearch/darkbench](https://github.com/apartresearch/darkbench), pinned at `7eef151` as a git submodule in `vendor/darkbench`.
- **Data:** [apart/darkbench](https://huggingface.co/datasets/apart/darkbench) on Hugging Face (also bundled as `vendor/darkbench/darkbench/darkbench.jsonl`).
- **Judge:** the README doesn't say how the judge model is set. Find out by reading the task and scorer code. Don't guess.
- **[v2] Mistral Saba:** a 24B model from Mistral for Middle Eastern and South Asian languages, and API-only.
  - Which South Asian languages it covers best is not confirmed here. Bengali quality is checked in Phase 1.
  - Its base model and training data aren't published, so the Small-vs-Saba comparison can't separate regional training from other differences.
- **Reference results:** the paper reports overall dark-pattern rates of 30% for Claude 3.5 Sonnet, 56% for Mixtral 8x7b and 61% for GPT-3.5 Turbo. Expect results in that range.

## Phase 0: Environment and accounts ✅ done

The `uv` venv (Python 3.12) is set up and `inspect-ai` 0.3.291 is installed. DarkBench is pinned as a submodule at `7eef151`, all versions are pinned in `requirements.lock`, `.env` is git-ignored, and the key's $25 limit is verified.

## Phase 1: Verify the models [v2]

Goal: confirm all three models respond, record providers and prices, and check that Saba handles Bengali. Cost: under $0.10.

1. ✅ Slugs and prices confirmed from `/api/v1/models` (table above). Still to do: record which providers serve Saba and Gemma 3 27B, from the `/endpoints` API.
2. Send 3 test prompts to each model through Inspect (`--model openrouter/<slug>`): one English prompt, one Bengali prompt, and one DarkBench-style prompt. That's 9 calls in total.
3. **Bengali check:** do the Bengali replies come back in Bengali script, and are they on-topic? Note this, without scoring it. If Saba can't produce usable Bengali, stop and ask. That would change what the pilot can say.
4. Check whether any model returns reasoning text (`<think>` blocks or reasoning fields). Expected: none of them.
5. If OpenRouter offers several providers for a model, pin one so every run uses the same provider. Record the choice.

**Stop and ask Cece if:**

- any model is unavailable or keeps failing
- Saba's Bengali output is unusable
- any price differs from the table by more than 25%

**Checkpoint:** `notes/models.md` updated with providers, the outcome of the Bengali check, and the reasoning-text check.

## Phase 2: Smoke test and judge setup

Goal: one 10-sample run per model that you've checked end to end, plus a measured cost per sample. Cost: about $0.50.

1. **Read the task code.** Write a short explanation in `notes/how_darkbench_scores.md` covering:
   - how the dataset is loaded
   - which solver runs
   - the judge prompt, word for word
   - how the judge model is chosen (hardcoded, a `-T` argument, or `--model-role grader=`)
   - what the score means
2. **Confirm the judge** (proposed: `claude-haiku-5.5`). If the upstream code hardcodes a judge, override it through Inspect's options rather than editing vendor code. If editing is unavoidable, put the change in `src/` and explain it.
3. **[v2] Handle thinking text**, only if Phase 1 found any. Otherwise record "not applicable".
4. **Fix the generation settings.** Use temperature 0.7 and a max-tokens limit that doesn't cut answers short (check; Saba's context is 32K). Use the same system prompt for all three models, defaulting to none, as in upstream. Store these in `config/run_config.yaml`.
5. **Run** `--limit 10` on each model and open the logs in `inspect view`.
6. **Measure cost.** Read the token counts from the logs, then project the cost of a full 660-sample run for each model, including the judge.

**Checkpoint:** Cece reads all 30 transcripts and judge verdicts in `inspect view` and approves the judge choice and the projected costs before Phase 3.

## Phase 3: Full English runs

Goal: per-category rates for all three models on all 660 prompts. Budget: $5.

1. Run all 660 samples on each model, one epoch first. Use `inspect eval-set` or separate runs that share the same config.
2. If the measured spend after epoch 1 leaves enough room, run 2 more epochs (`--epochs 3`) so variance can be reported. If not, run the extra epochs on a stratified subset of 30 prompts per category (180 total) and say so in the write-up.
3. Retry failed or errored samples once. Log the final count of errors and refusals per model, because a refusal is not the same as passing.
4. Export a tidy CSV with columns `sample_id, category, model, epoch, response, judge_verdict, judge_explanation, tokens` to `results/english/`.

**Checkpoint:** a table with per-category rates and 95% confidence intervals for all three models, the actual spend so far, and 5 example transcripts per category where Small 3.1 and Saba disagree.

## Phase 4: Judge validation

Goal: find out whether the judge's scores can be trusted. Budget: $2.

1. **Build a labelling sheet.** Draw 60 responses: 10 per category, mixed across all three models, balanced between judge "yes" and "no". Write them to `validation/to_label.csv` with the prompt, the response, and the category definition. Hide the judge's verdict.
2. **Cece labels them by hand.** She marks each as dark pattern yes or no, with an optional note. Claude Code waits for this step.
3. **Compute agreement** between Cece and the judge: overall and per category, as % agreement and Cohen's kappa.
4. **Run a second judge** from a different family (proposed: `gpt-6-luna`) on the same 60 responses. Report how often the two judges agree with each other.
5. **Flag weak categories.** Any category with kappa below 0.4 is unreliable and gets reported with a caveat, not as a headline number.

**Checkpoint:** `validation/agreement.md` with the numbers and the 5 worst disagreements, each with a one-line note on why the judge got it wrong.

## Phase 5: Bengali pilot

Goal: 60 Bengali prompts (10 per category) run on all three models, and a first answer to whether the language changes the rates. Budget: $3.

1. **Pick the prompts.** Choose 60 English prompts that ran in Phase 3, 10 per category, with a fixed random seed. Keep the matching English results so the comparison is item by item.
2. **Translate.** Use one strong model to translate each prompt into Bengali. Tell it to keep any brand names, the tone, and the adversarial intent of the prompt. Then back-translate into English with a different model, and flag items whose meaning drifted. **[v2]** Don't use any of the three tested models as the translator.
3. **Human review.** Cece, or a native Bengali speaker she chooses, reviews all 60 translations in `bengali/translations_review.csv` and fixes or approves each one. Claude Code waits for this step. Some harmful-generation prompts may be refused by the translator model; log those instead of working around the refusal.
4. **Build the task.** Write a small Inspect task in `src/darkbench_bn.py` that reuses the upstream scorer and loads the approved Bengali prompts.
5. **Run** all three models on the 60 prompts. Score with two judging methods:
   - **A:** the judge reads the Bengali response directly.
   - **B:** the response is translated into English first, then judged.
6. **Validate.** Cece hand-labels 20 of the Bengali responses (or reuses labels from step 3's reviewer), so both judging methods can be checked against people.

**Checkpoint:** a table showing the English vs Bengali rate per category and model on the matched 60 items, how well methods A and B agree with the human labels, and a note on which judging method to trust. With 10 items per category the confidence intervals will be wide. Present the pilot as a direction to follow up, not a result.

## Phase 6: Analysis and write-up

Goal: a 2–3 page write-up Cece can share, plus a repo anyone can re-run. Cost: $0.

1. **Charts.** Make a grouped bar chart of rate per category per model (English, with confidence-interval whiskers), and a matched English vs Bengali chart for the pilot.
2. **Significance.** Test each category's Small 3.1 vs Saba difference with a paired test on the same prompts, e.g. McNemar. Report how many categories show a difference without leaning on p-values.
3. **Write `REPORT.md`.** Sections:
   - question
   - setup (models, providers, judge, settings, commits)
   - English results
   - judge validity
   - Bengali pilot
   - limitations: one judge family, the translation pipeline, 60-item pilot, provider-side filtering. **[v2]** Add: Saba is closed-weight and its training is undisclosed, so the comparison is descriptive, not causal. Also say why Sarvam-M was dropped.
   - next steps: e.g. revisit the same-base comparison if Sarvam-M becomes hostable again
4. **Reproduce.** Add a single `make reproduce` (or `run_all.sh`) that re-runs everything from the config.

**Checkpoint:** Cece reviews `REPORT.md`. Nothing is published or shared without her approval.

## Budget [v2]

These are rough estimates. They assume about 60 prompt tokens and 400 response tokens per sample, and about 1,500 input and 250 output tokens per judge call. Replace them with measured costs after Phase 2.

- Generation: about $0.16 (Small 3.1), $0.17 (Saba) and $0.05 (Gemma) per 660-sample epoch.
- Judge (Haiku 5.5): about $0.18 per model-epoch.
- So 3 models × 3 epochs comes to about $2.75.

| Phase | Budget (USD) | Main cost |
| --- | --- | --- |
| 1. Verify models | 0.10 | 9 test calls |
| 2. Smoke test | 0.50 | 30 samples + judge |
| 3. English runs | 5.00 | 1,980 responses per epoch-set + judge |
| 4. Judge validation | 2.00 | second judge on 60 responses |
| 5. Bengali pilot | 3.00 | translation, back-translation, 180 responses, two judging methods |
| Reserve | 14.40 | retries, reruns |
| **Total** | **25.00** |  |

**Cost controls:**

- The OpenRouter key has a $25 credit limit, so overspending fails safely.
- After every phase, Claude Code reports the actual spend from the OpenRouter usage API or the log token counts, plus the running total.
- If a phase's projection goes more than 25% over its line, stop and ask before running it.
- Always use `--limit` before a full run. Never re-run a full eval just to fix a bug in scoring: re-score existing logs with `inspect score` instead.

## Rules for Claude Code

Unchanged from v1.

Work one phase at a time. Stop at every checkpoint and wait for Cece's go-ahead. Cece is learning to build evals, so explain each step briefly as you do it.

**Always:**

- Explain what each Inspect concept is doing (task, solver, scorer, model roles, epochs, logs) the first time it comes up, in two or three lines.
- Keep every `.eval` log. Record the model slugs, providers, judge, settings, and commit hashes in `config/run_config.yaml`.
- Put any change to upstream behaviour in `src/` as a wrapper, and leave `vendor/` untouched.
- Report spend after each phase.

**Stop and ask Cece before:**

- changing a fixed decision (models, provider, judge family, budget)
- any step that waits on her (labelling, translation review)
- spending more than a phase's budget line, or adding a second API account
- any choice that changes what the numbers mean (dropping samples, changing the judge prompt)

**Never:**

- commit `.env` or put the API key in a file that gets committed
- edit the judge prompt to get "better" numbers
- report refusals or errors as clean (non-dark) responses
- push to a public remote or share results without Cece's approval

## Deliverables and repo layout

Unchanged from v1. The project folder keeps the name `darkbench-indic/`.
