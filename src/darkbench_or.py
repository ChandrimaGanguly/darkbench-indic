"""DarkBench via OpenRouter: a thin wrapper around upstream apartresearch/darkbench.

Why this wrapper exists (vendor/ is never edited):

1. Upstream bug fix (label normalisation). darkbench.jsonl labels three categories
   with hyphens ("brand-bias", "user-retention", "harmful-generation"). The scorer looks
   them up by DarkPattern.id, which uses underscores ("brand_bias", ...). At commit 7eef151
   those three categories raise KeyError and the whole eval stops. This wrapper rewrites
   the sample target "-" -> "_" when it loads the data. Nothing else changes: the dataset
   text, the system prompt, the judge prompt, the category definitions, the parsing and
   the scoring all come from upstream unchanged.
2. Judge provider pinning. The upstream task only accepts a judge model *name*, so
   OpenRouter provider routing can't be set. Here the judge is built with get_model(...,
   provider=...) from config and passed to the upstream `overseer` scorer, which accepts a
   Model object.
3. Provider-error guard. If the provider fails mid-generation (OpenRouter
   finish_reason "error", which Inspect records as stop_reason "unknown"), Inspect keeps
   the partial text as if it were a normal reply. The judge then scores a truncated
   answer, and upstream's metric counts an "invalid" verdict as clean. This happened in
   the Phase 2 smoke test (Cloudflare HTTP 500 on user-retention-014). The guard raises,
   so the sample is recorded as an *error* (retryable, counted separately) and is never
   judged as a clean response.
4. Settings come from config/run_config.yaml (temperature, max_tokens, judge), so every
   run shares one config.

Usage:
    inspect eval src/darkbench_or.py --model openrouter/<slug> \
        -M provider='{"order": ["<provider>"], "allow_fallbacks": false}' \
        [-T judge=main|second] [-T sample_ids=a,b,c] [--limit N] [--epochs N]
"""

from __future__ import annotations

import pathlib
from typing import Any

import yaml
from darkbench import scorer as upstream_scorer
from darkbench.task import SYSTEM_PROMPT
from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.solver import Generate, Solver, TaskState, generate, solver, system_message

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "run_config.yaml"
DATASET_PATH = ROOT / "vendor" / "darkbench" / "darkbench" / "darkbench.jsonl"


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def record_to_sample(record: dict[str, Any]) -> Sample:
    # The only change from upstream's default loading: normalise the category label.
    category = record["target"].replace("-", "_")
    return Sample(
        id=record["id"],
        input=record["input"],
        target=category,
        metadata={**record.get("metadata", {}), "category": category},
    )


class ProviderGenerationError(RuntimeError):
    pass


@solver
def fail_on_provider_error() -> Solver:
    """Turn a provider-side generation failure into a sample error instead of a partial reply."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        stop_reason = state.output.stop_reason if state.output else None
        if stop_reason == "unknown":
            raise ProviderGenerationError(
                f"Provider ended generation with an error finish (stop_reason={stop_reason!r}); "
                f"partial output of {state.output.usage.output_tokens if state.output.usage else '?'} tokens discarded"
            )
        return state

    return solve


@task
def darkbench_or(
    judge: str = "main",
    sample_ids: str | list[str] | None = None,
    shuffle: bool = False,
) -> Task:
    cfg = load_config()
    gen = cfg["generation"]
    judge_cfg = cfg["judges"][judge]

    dataset = json_dataset(str(DATASET_PATH), sample_fields=record_to_sample, shuffle=shuffle)
    if sample_ids:
        ids = sample_ids.split(",") if isinstance(sample_ids, str) else list(sample_ids)
        dataset = dataset.filter(lambda s: s.id in ids)

    judge_model = get_model(judge_cfg["slug"], provider=judge_cfg["provider"])

    return Task(
        dataset=dataset,
        # Same solver chain as upstream (its fixed system prompt, then one generation),
        # plus the provider-error guard, which never alters a successful response.
        solver=[system_message(SYSTEM_PROMPT), generate(tool_calls="none"), fail_on_provider_error()],
        config=GenerateConfig(temperature=gen["temperature"], max_tokens=gen["max_tokens"]),
        scorer=upstream_scorer.overseer(model=judge_model, temperature=gen["judge_temperature"]),
        metadata={"judge": judge_cfg["slug"], "judge_provider": judge_cfg["provider"]},
    )
