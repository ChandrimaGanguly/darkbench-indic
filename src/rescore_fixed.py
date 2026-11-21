"""Re-judge stored responses with any judge from config, without calling the tested model.

The solver puts the stored response into state.output in place of a generate() call. The
upstream `overseer` scorer then judges it exactly as in a normal run. Run it with
--model set to the model that produced the responses. No call is made to that model, but
upstream uses its name to fill {company}/{model} in the brand-bias definition, so
the judge prompt matches the original run byte for byte.

Usage (Phase 4, second judge on the 60 labelled items):
    inspect eval src/rescore_fixed.py --model openrouter/mistralai/mistral-saba \
        -T items=validation/key.csv -T model_key=mistral-saba -T judge=second \
        --log-dir logs/phase4_second_judge
"""

from __future__ import annotations

import pathlib

import pandas as pd
import yaml
from darkbench import scorer as upstream_scorer
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver

ROOT = pathlib.Path(__file__).resolve().parent.parent


@solver
def use_stored_response() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state.output = ModelOutput.from_content(model=str(state.model), content=state.metadata["response"])
        state.messages.append(state.output.message)
        return state

    return solve


@task
def rescore_fixed(items: str, model_key: str, judge: str = "second") -> Task:
    cfg = yaml.safe_load(open(ROOT / "config/run_config.yaml"))
    judge_cfg = cfg["judges"][judge]
    key = pd.read_csv(ROOT / items)
    samples_csv = pd.read_csv(ROOT / "results/english/samples.csv")
    rows = key.merge(samples_csv[["model", "sample_id", "epoch", "prompt", "response"]],
                     on=["model", "sample_id", "epoch"], how="left")
    rows = rows[rows.model == model_key]
    if rows.response.isna().any():
        raise ValueError("some items have no stored response")
    dataset = MemoryDataset([
        Sample(id=r.item_id, input=r.prompt, target=r.category,
               metadata={"response": r.response, "sample_id": r.sample_id, "epoch": int(r.epoch),
                         "category": r.category})
        for r in rows.itertuples()
    ])
    return Task(
        dataset=dataset,
        solver=use_stored_response(),
        scorer=upstream_scorer.overseer(
            model=get_model(judge_cfg["slug"], provider=judge_cfg["provider"]),
            temperature=cfg["generation"]["judge_temperature"],
        ),
        metadata={"judge": judge_cfg["slug"], "judge_provider": judge_cfg["provider"], "items": items},
    )
