#!/usr/bin/env bash
# Full English DarkBench run for every model in config/run_config.yaml.
# Usage: src/run_english.sh <epochs> <log_dir> [extra inspect args...]
#   e.g. src/run_english.sh 1 logs/phase3_epoch1
# Models run in parallel; they use different providers.
set -euo pipefail
cd "$(dirname "$0")/.."
EPOCHS="${1:?epochs}"; LOG_DIR="${2:?log dir}"; shift 2
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
  .venv/bin/inspect eval src/darkbench_or.py \
      --model "$slug" -M provider="$provider" \
      --epochs "$EPOCHS" \
      --retry-on-error=1 --fail-on-error 0.05 --max-retries 6 \
      --log-dir "$LOG_DIR" --display plain "$@" \
      > "$LOG_DIR/$key.stdout" 2>&1 &
  pids+=($!)
  echo "started $key ($slug) pid $!"
done

status=0
for p in "${pids[@]}"; do wait "$p" || status=1; done
echo "all runs finished, exit status $status"
exit $status
