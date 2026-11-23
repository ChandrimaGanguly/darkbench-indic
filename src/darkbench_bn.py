"""Phase 5 step 4: DarkBench on the approved Bengali prompts (judging method A).

Same as src/darkbench_or.py except for the dataset:
- Prompts come from bengali/prompts_bn_approved.csv (58 human-reviewed Bengali translations).
  The sample id is the original DarkBench id, so results match the English run item by item.
- Everything else is reused unchanged: upstream's fixed English system prompt
  ("You are a helpful assistant."), one generation, the provider-error guard, the generation
  settings from config, and the upstream `overseer` scorer with the main judge.

Method A = this task's scores: the judge sees the Bengali prompt and the Bengali response,
with upstream's English judge template and category definitions.
Method B = src/rescore_bn_translated.py, run afterwards on this task's logs.

Usage:
    inspect eval src/darkbench_bn.py --model openrouter/<slug> \
        -M provider='{"order": ["<provider>"], "allow_fallbacks": false}' \
        [-T sample_ids=a,b,c] --log-dir logs/phase5_bn_A
"""

from __future__ import annotations

import pathlib

import pandas as pd
from darkbench import scorer as upstream_scorer
from darkbench.task import SYSTEM_PROMPT
from darkbench_or import fail_on_provider_error, load_config
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import GenerateConfig, get_model
from inspect_ai.solver import generate, system_message

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "bengali/prompts_bn_approved.csv"


@task
def darkbench_bn(judge: str = "main", sample_ids: str | list[str] | None = None) -> Task:
    cfg = load_config()
    gen = cfg["generation"]
    judge_cfg = cfg["judges"][judge]

    df = pd.read_csv(PROMPTS, encoding="utf-8-sig")
    if sample_ids:
        ids = sample_ids.split(",") if isinstance(sample_ids, str) else list(sample_ids)
        df = df[df.sample_id.isin(ids)]
    dataset = MemoryDataset([
        Sample(id=r.sample_id, input=r.prompt_bn_approved, target=r.category,
               metadata={"category": r.category, "prompt_en": r.prompt_en, "language": "bn"})
        for r in df.itertuples()
    ])

    return Task(
        dataset=dataset,
        solver=[system_message(SYSTEM_PROMPT), generate(tool_calls="none"), fail_on_provider_error()],
        config=GenerateConfig(temperature=gen["temperature"], max_tokens=gen["max_tokens"]),
        scorer=upstream_scorer.overseer(model=get_model(judge_cfg["slug"], provider=judge_cfg["provider"]),
                                        temperature=gen["judge_temperature"]),
        metadata={"judge": judge_cfg["slug"], "judge_provider": judge_cfg["provider"],
                  "method": "A", "prompts": str(PROMPTS.relative_to(ROOT))},
    )
