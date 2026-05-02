#!/usr/bin/env zsh
# Start Aspire Dashboard + OTel Collector.
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
MAGENTA=$'\e[35m'

banner() {
  print ""
  print "${BOLD}${CYAN}  ╔═══════════════════════════════════════════╗${RESET}"
  print "${BOLD}${CYAN}  ║   📡  Copilot Telemetry Stack             ║${RESET}"
  print "${BOLD}${CYAN}  ║       Aspire Dashboard · OTel Collector   ║${RESET}"
  print "${BOLD}${CYAN}  ╚═══════════════════════════════════════════╝${RESET}"
  print ""
}

step()    { print "  ${BOLD}${CYAN}▶${RESET}  $*" }
ok()      { print "  ${GREEN}✔${RESET}  $*" }
warn()    { print "  ${YELLOW}⚠${RESET}  $*" }
die()     { print "  ${RED}✖${RESET}  ${BOLD}$*${RESET}"; exit 1 }
rule()    { print "  ${DIM}────────────────────────────────────────${RESET}" }

spin_wait() {
  local label=$1 url=$2 max=${3:-30}
  local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local i=0
  while (( i < max )); do
    curl -s --max-time 1 "$url" >/dev/null 2>&1 && return 0
    printf "\r  ${CYAN}%s${RESET}  %s  " "${frames[$(( i % 10 + 1 ))]}" "$label"
    sleep 1
    (( i++ ))
  done
  printf "\r"
  return 1
}

# ─────────────────────────────────────────────
banner
# ─────────────────────────────────────────────

step "Checking prerequisites..."
for cmd in docker curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    die "Missing required command: '$cmd'"
  fi
done

if ! docker info >/dev/null 2>&1; then
  die "Docker daemon is not running — start Docker Desktop first"
fi
ok "Prerequisites satisfied"
rule

# ─────────────────────────────────────────────
step "Pulling / starting containers..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d --quiet-pull 2>&1 \
  | grep -v "^$" \
  | sed "s/^/     /" \
  || true
ok "Containers started"
rule

# ─────────────────────────────────────────────
step "Waiting for OTel Collector..."
if spin_wait "OTel Collector (health check)" "http://localhost:13133" 30; then
  printf "\r"
  ok "OTel Collector is healthy"
else
  die "OTel Collector did not become healthy in time"
fi

step "Waiting for Aspire Dashboard..."
if spin_wait "Aspire Dashboard UI" "http://localhost:18888" 30; then
  printf "\r"
  ok "Aspire Dashboard is reachable"
else
  die "Aspire Dashboard did not become reachable in time"
fi
rule

# ─────────────────────────────────────────────
print ""
print "  ${BOLD}${GREEN}🚀  Stack is live!${RESET}"
print ""
print "  ${BOLD}Endpoints${RESET}"
endpoints_inner_width=60
endpoints_rule="$(printf '─%.0s' {1..60})"
print_endpoint_row() {
  local icon=$1
  local name=$2
  local url=$3
  local pad_adjust=${4:-0}
  local icon_width=2
  local row_width
  local pad

  row_width=$((2 + icon_width + 2 + 18 + 1 + ${#url}))
  pad=$((endpoints_inner_width - row_width + pad_adjust))
  if (( pad < 0 )); then
    pad=0
  fi

  printf "  ${DIM}│${RESET}  %s  %-18s %s%*s${DIM}│${RESET}\n" "$icon" "$name" "$url" "$pad" ""
}

print "  ${DIM}┌${endpoints_rule}┐${RESET}"
print_endpoint_row "💻" "Aspire Dashboard" "http://localhost:18888"
print_endpoint_row "📤" "OTLP HTTP" "http://localhost:4318"
print_endpoint_row "🔌" "OTLP gRPC" "localhost:4317"
print_endpoint_row "❤️" "Collector Health" "http://localhost:13133" 1
print "  ${DIM}└${endpoints_rule}┘${RESET}"
print ""
print "  ${DIM}VS Code must have github.copilot.chat.otel.enabled: true${RESET}"
print "  ${DIM}Open this workspace folder to activate .vscode/settings.json${RESET}"
print ""
