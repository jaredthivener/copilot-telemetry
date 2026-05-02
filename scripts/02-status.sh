#!/usr/bin/env zsh
# Show status of Aspire + OTel Collector stack.
set -euo pipefail

ROOT_DIR="${0:A:h}/.."

# ─────────────────────────────────────────────
#  Colors & symbols
# ─────────────────────────────────────────────
RESET=$'\e[0m'
BOLD=$'\e[1m'
DIM=$'\e[2m'
GREEN=$'\e[32m'
CYAN=$'\e[36m'
YELLOW=$'\e[33m'
RED=$'\e[31m'

banner() {
  print ""
  print "${BOLD}${CYAN}  ╔═══════════════════════════════════════════╗${RESET}"
  print "${BOLD}${CYAN}  ║   📊  Stack Status                        ║${RESET}"
  print "${BOLD}${CYAN}  ╚═══════════════════════════════════════════╝${RESET}"
  print ""
}

rule() { print "  ${DIM}────────────────────────────────────────${RESET}" }

check() {
  local label=$1 url=$2
  if curl -s --max-time 2 "$url" >/dev/null 2>&1; then
    print "  ${GREEN}●${RESET}  ${BOLD}UP${RESET}    ${label}  ${DIM}${url}${RESET}"
  else
    print "  ${RED}●${RESET}  ${BOLD}DOWN${RESET}  ${label}  ${DIM}${url}${RESET}"
  fi
}

check_tcp() {
  local label=$1 host=$2 port=$3
  if nc -z -w 2 "$host" "$port" >/dev/null 2>&1; then
    print "  ${GREEN}●${RESET}  ${BOLD}UP${RESET}    ${label}  ${DIM}${host}:${port}${RESET}"
  else
    print "  ${RED}●${RESET}  ${BOLD}DOWN${RESET}  ${label}  ${DIM}${host}:${port}${RESET}"
  fi
}

# ─────────────────────────────────────────────
banner

print "  ${BOLD}Containers${RESET}"
rule
docker compose -f "$ROOT_DIR/docker-compose.yml" ps \
  --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
  | while IFS= read -r line; do
      if [[ "$line" == *"running"* ]] || [[ "$line" == *"Up"* ]]; then
        print "  ${GREEN}▸${RESET}  $line"
      elif [[ "$line" == NAME* ]]; then
        print "  ${DIM}  $line${RESET}"
      else
        print "  ${RED}▸${RESET}  $line"
      fi
    done
print ""

print "  ${BOLD}Endpoint Health${RESET}"
rule
check "OTel Collector " "http://localhost:13133"
check "Aspire UI      " "http://localhost:18888"
check "OTLP HTTP      " "http://localhost:4318"
check_tcp "OTLP gRPC      " "localhost" "4317"
check "Collector Metrics" "http://localhost:8888/metrics"
print ""

print "  ${DIM}Open Aspire Dashboard → ${CYAN}http://localhost:18888${RESET}"
print ""
