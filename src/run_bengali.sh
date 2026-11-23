#!/usr/bin/env bash
# Phase 5 Bengali pilot for every model in config/run_config.yaml, 1 epoch.
# Usage: src/run_bengali.sh <A|B> <a_log_dir> [<b_log_dir>] [extra inspect args...]
#   A: generate Bengali responses + judge them directly      -> <a_log_dir>
#   B: translate method A responses to English, then judge   -> <b_log_dir>
#   e.g. src/run_bengali.sh A logs/phase5_smoke_A -T sample_ids=a,b,c
#        src/run_bengali.sh B logs/phase5_smoke_A logs/phase5_smoke_B
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:?A or B}"; A_DIR="${2:?method A log dir}"; shift 2
if [ "$MODE" = B ]; then B_DIR="${1:?method B log dir}"; shift; LOG_DIR="$B_DIR"; else LOG_DIR="$A_DIR"; fi
set -a; . ./.env; set +a
mkdir -p "$LOG_DIR"

mapfile -t MODELS < <(.venv/bin/python -c '
import json, yaml
cfg = yaml.safe_load(open("config/run_config.yaml"))
for k, m in cfg["models"].items():
    print(k, m["slug"], json.dumps(m["provider"]), sep="\t")
')

pids=()
for row in "${MODELS[@]}"; do
  IFS=$'\t' read -r key slug provider <<< "$row"
  if [ "$MODE" = A ]; then
    args=(src/darkbench_bn.py --model "$slug" -M provider="$provider")
  else
    args=(src/rescore_bn_translated.py --model "$slug" -T a_log_dir="$A_DIR" -T tested="$slug")
  fi
  .venv/bin/inspect eval "${args[@]}" --epochs 1 \
      --retry-on-error=1 --fail-on-error 0.05 --max-retries 6 \
      --log-dir "$LOG_DIR" --display plain "$@" \
      > "$LOG_DIR/$key.stdout" 2>&1 &
  pids+=($!)
  echo "started $MODE $key ($slug) pid $!"
done

status=0
for p in "${pids[@]}"; do wait "$p" || status=1; done
echo "all runs finished, exit status $status"
exit $status
