#!/usr/bin/env zsh
# Stop Aspire Dashboard + OTel Collector stack.
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
RED=$'\e[31m'

banner() {
  print ""
  print "${BOLD}${CYAN}  ╔═══════════════════════════════════════════╗${RESET}"
  print "${BOLD}${CYAN}  ║   🛑  Stopping Stack                      ║${RESET}"
  print "${BOLD}${CYAN}  ╚═══════════════════════════════════════════╝${RESET}"
  print ""
}

step() { print "  ${BOLD}${CYAN}▶${RESET}  $*" }
ok()   { print "  ${GREEN}✔${RESET}  $*" }
rule() { print "  ${DIM}────────────────────────────────────────${RESET}" }

# ─────────────────────────────────────────────
banner

step "Stopping containers..."
docker compose -f "$ROOT_DIR/docker-compose.yml" down --rmi all --volumes --remove-orphans 2>&1 \
  | grep -v "^$" \
  | sed "s/^/     /" \
  || true

rule
ok "Stack stopped — containers, images, and storage removed"
print ""
print "  ${DIM}To start again: ${CYAN}zsh scripts/01-start.sh${RESET}"
print ""
