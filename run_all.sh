#!/usr/bin/env bash
# Reproduce the project.
#
#   ./run_all.sh            (default: "analysis", $0, ~1 min)
#       Rebuilds every table, chart and agreement number from the committed Inspect logs
#       and the committed human labels. Deterministic: afterwards `git status` should show
#       no changes to results/, validation/ or bengali/.
#
#   ./run_all.sh full       (~$4 of OpenRouter credit, ~1-2 h; needs .env with OPENROUTER_API_KEY)
#       Re-runs all inference from config/run_config.yaml: English (3 models x 660 prompts x
#       3 epochs) and the Bengali pilot (methods A and B) on the committed, human-approved
#       Bengali prompts. The existing logs are moved to logs/archive_<timestamp>/ first, so
#       nothing is lost; `git diff` then shows how the new numbers differ.
#       Not re-run, because they need people: the Phase 4/5 hand labels, the Bengali
#       translation review, and the second judge (it rescores the hand-labelled items).
#       The agreement numbers are therefore NOT rebuilt in full mode; they describe the
#       committed responses.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
MODE="${1:-analysis}"

if [ "$MODE" = full ]; then
  ts=$(date +%Y%m%dT%H%M%S); arch="logs/archive_$ts"; mkdir -p "$arch"
  for d in phase3_epoch1 phase3_epochs23 phase5_bn_A phase5_bn_B; do
    [ -d "logs/$d" ] && mv "logs/$d" "$arch/"
  done
  echo "== old logs moved to $arch"
  src/run_english.sh 1 logs/phase3_epoch1
  src/run_english.sh 2 logs/phase3_epochs23
  src/run_bengali.sh A logs/phase5_bn_A
  src/run_bengali.sh B logs/phase5_bn_A logs/phase5_bn_B
elif [ "$MODE" != analysis ]; then
  echo "usage: $0 [analysis|full]" >&2; exit 2
fi

echo "== English results (results/english/)";           $PY src/export_results.py
if [ "$MODE" = analysis ]; then
  echo "== Judge agreement, English (validation/)";      $PY src/agreement.py
fi
echo "== Bengali rates (bengali/rates.md)";              (cd src && ../$PY bn_analyze.py)
if [ "$MODE" = analysis ]; then
  echo "== Judge agreement, Bengali (bengali/)";         (cd src && ../$PY bn_agreement.py)
fi
echo "== Charts and McNemar (results/)";                 $PY src/analysis.py
echo "== done"
git status --short results validation bengali || true
