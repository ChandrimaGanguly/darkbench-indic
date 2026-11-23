"""Phase 5 step 5, judging method B: translate each Bengali response into English, then judge.

Reads the method A logs (src/darkbench_bn.py) for one tested model. For every sample that
has a response, the solver translates the stored Bengali response into English with
TRANSLATOR (reasoning switched off, temperature 0), then the upstream `overseer` scorer
judges it with the ORIGINAL ENGLISH prompt, so the judge sees an all-English conversation,
just as in Phase 3. No call is made to the tested model: --model is only there so upstream
fills {company}/{model} in the brand-bias definition exactly as in method A.

The English translation is stored in the sample metadata (response_en) and the log.

Usage:
    inspect eval src/rescore_bn_translated.py --model openrouter/mistralai/mistral-saba \
        -T a_log_dir=logs/phase5_bn_A -T tested=openrouter/mistralai/mistral-saba --log-dir logs/phase5_bn_B
"""

from __future__ import annotations

import glob
import pathlib

from darkbench import scorer as upstream_scorer
from darkbench_or import load_config
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig, ModelOutput, get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRANSLATOR = "openrouter/google/gemini-3-flash-preview"
TRANSLATE_PROMPT = """Translate the following chatbot reply from Bengali into English. Translate faithfully and \
completely: keep the meaning, tone, claims, hedges, emotional language, formatting (lists, headings, bold) and \
any brand or product names. Do not summarise, add, correct or comment. If parts are already in English, keep \
them as they are. Output only the translation.

{text}"""


@solver
def translate_stored_response() -> Solver:
    translator = get_model(TRANSLATOR, config=GenerateConfig(
        temperature=0, max_tokens=16000, extra_body={"reasoning": {"enabled": False}}))

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        out = await translator.generate(TRANSLATE_PROMPT.format(text=state.metadata["response_bn"]))
        if out.stop_reason not in ("stop", None):
            raise RuntimeError(f"translator stop_reason={out.stop_reason}")
        state.metadata["response_en"] = out.completion
        state.metadata["translator_usage"] = out.usage.model_dump() if out.usage else None
        state.output = ModelOutput.from_content(model=str(state.model), content=out.completion)
        state.messages.append(state.output.message)
        return state

    return solve


@task
def rescore_bn_translated(a_log_dir: str, tested: str, judge: str = "main") -> Task:
    cfg = load_config()
    judge_cfg = cfg["judges"][judge]
    samples = []
    for f in sorted(glob.glob(str(ROOT / a_log_dir / "*.eval"))):
        log = read_eval_log(f)
        if log.eval.model != tested:
            continue
        for s in log.samples or []:
            if s.error or not s.output or not s.output.completion:
                continue
            samples.append((log.eval.model, s))
    if not samples:
        raise ValueError(f"no method A samples for {tested} in {a_log_dir}")
    dataset = MemoryDataset([
        Sample(id=s.id, input=s.metadata["prompt_en"], target=s.target,
               metadata={**s.metadata, "tested_model": model, "response_bn": s.output.completion})
        for model, s in samples
    ])
    return Task(
        dataset=dataset,
        solver=translate_stored_response(),
        scorer=upstream_scorer.overseer(model=get_model(judge_cfg["slug"], provider=judge_cfg["provider"]),
                                        temperature=cfg["generation"]["judge_temperature"]),
        metadata={"judge": judge_cfg["slug"], "method": "B", "translator": TRANSLATOR, "a_log_dir": a_log_dir},
    )
