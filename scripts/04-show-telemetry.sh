#!/usr/bin/env zsh
# Human-readable view of local telemetry files.
# Usage:
#   ./scripts/04-show-telemetry.sh            # show all signals
#   ./scripts/04-show-telemetry.sh traces     # traces only
#   ./scripts/04-show-telemetry.sh logs       # logs only
#   ./scripts/04-show-telemetry.sh metrics    # metrics only
set -euo pipefail

ROOT_DIR="${0:A:h}/.."
TELEMETRY_DIR="$ROOT_DIR/telemetry"
LIB="${0:A:h}/lib/telemetry_view.py"
SIGNAL="all"
PROMPT_FULL=0

RED=$'\e[31m'; RESET=$'\e[0m'

usage() {
  echo "Usage: $0 [traces|logs|metrics|all] [--prompt-full]"
}

for arg in "$@"; do
  case "$arg" in
    traces|logs|metrics|all)
      SIGNAL="$arg"
      ;;
    --prompt-full)
      PROMPT_FULL=1
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

run_signal() {
  local sig="$1" file="$2"
  [[ -f "$file" ]] || { echo "${RED}✗  $(basename "$file") not found${RESET}"; return; }
  if [[ "$sig" == "traces" && "$PROMPT_FULL" -eq 1 ]]; then
    python3 "$LIB" "$sig" "$file" --prompt-full
  else
    python3 "$LIB" "$sig" "$file"
  fi
}

case "$SIGNAL" in
  traces)  run_signal traces  "$TELEMETRY_DIR/traces.jsonl"  ;;
  logs)    run_signal logs    "$TELEMETRY_DIR/logs.jsonl"    ;;
  metrics) run_signal metrics "$TELEMETRY_DIR/metrics.jsonl" ;;
  all)
    run_signal traces  "$TELEMETRY_DIR/traces.jsonl"
    run_signal logs    "$TELEMETRY_DIR/logs.jsonl"
    run_signal metrics "$TELEMETRY_DIR/metrics.jsonl"
    ;;
  *)
    usage
    exit 1
    ;;
esac
