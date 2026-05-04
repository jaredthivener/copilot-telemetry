# Scripts Guide

This folder contains helper scripts for running the local Copilot telemetry stack and viewing exported telemetry in a readable terminal format.

## Scripts

- `01-start.sh`: Starts Aspire Dashboard + OpenTelemetry Collector via Docker Compose.
- `02-status.sh`: Checks stack status and endpoint reachability.
- `03-stop.sh`: Stops the stack.
- `04-show-telemetry.sh`: Pretty terminal viewer for traces, logs/events, and metrics from `telemetry/*.jsonl`.

## Telemetry Viewer

`04-show-telemetry.sh` renders local telemetry export files written by the collector:

- `telemetry/traces.jsonl`
- `telemetry/logs.jsonl`
- `telemetry/metrics.jsonl`

### Usage

```sh
./scripts/04-show-telemetry.sh [traces|logs|metrics|all] [--prompt-full]
```

Examples:

```sh
# Show all sections
./scripts/04-show-telemetry.sh

# Show traces only
./scripts/04-show-telemetry.sh traces

# Show traces with full wrapped prompt text per trace
./scripts/04-show-telemetry.sh traces --prompt-full

# Show all sections and enable full trace prompts
./scripts/04-show-telemetry.sh all --prompt-full
```

### What You Will See

- `traces`: Per-trace table with span tree, aligned durations, and prompt context.
- `logs`: Session-grouped event lines with event icons and token bars.
- `metrics`: Namespace-grouped metric cards with counters and histogram summaries.

### Prompt Modes

- default: one-line prompt preview per trace
- `--prompt-full`: wraps prompt across multiple lines for full context

## Typical Flow

```sh
./scripts/01-start.sh
./scripts/02-status.sh
./scripts/04-show-telemetry.sh all
```

Generate Copilot chat activity in VS Code first so telemetry files contain data.

## Troubleshooting

- If a section says `*.jsonl not found`, start the stack and ensure the collector file exporters are enabled.
- If output is empty, generate a few Copilot interactions (include at least one tool call), then rerun the viewer.
- Use `./scripts/02-status.sh` to confirm collector (`4318`, `4317`, `13133`) and Aspire UI (`18888`) are up.
