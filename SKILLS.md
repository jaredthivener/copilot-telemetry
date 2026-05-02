# SKILLS.md

## Purpose

This catalog defines repeatable skills for observing GitHub Copilot Chat telemetry using a local OTel Collector and Aspire Dashboard.

## Skill 1: Stack Bootstrap

Use when:

- initializing the observation stack from a clean state
- recovering from broken containers or config drift

Inputs:

- Docker daemon running

Commands:

- zsh scripts/01-start.sh
- zsh scripts/02-status.sh

Outputs:

- OTel Collector healthy at localhost:13133
- Aspire UI reachable at localhost:18888

Verify:

- both endpoints report UP in status script

## Skill 2: Copilot Telemetry Observation

Use when:

- analyzing GitHub Copilot Chat model usage
- comparing token consumption across models
- investigating request latency or errors

Inputs:

- VS Code settings with github.copilot.chat.otel.enabled: true
- Stack running (Skill 1)

What is available in Aspire:

- Metrics tab: filter resource = copilot-chat
  - gen_ai.client.operation.duration (per model, histogram)
  - gen_ai.client.token.usage (input/output tokens per model)
  - copilot_chat.session.count
- Structured Logs tab: filter resource = copilot-chat
  - per-request records with error.type on failures

What is NOT available yet:

- Traces (tool calls, agent turns, skill invocations)
- Copilot Chat 0.46.x does not emit OTLP trace data

## Skill 3: Stack Teardown

Use when:

- done observing, freeing resources

Commands:

- zsh scripts/04-stop.sh
- response payload includes usage tokens

## Skill 3: Dense Telemetry Emission

Use when:

- Aspire has insufficient logs/metrics volume
- validating trace, log, and metric ingestion pipelines

Inputs:

- TELEMETRY_SERVICE_NAME
- desired batch count

Commands:

- zsh scripts/05-emit-telemetry.sh demo-local 25

Outputs:

- burst of traces
- structured logs
- counter metrics

Verify:

- script reports accepted batches
- service appears in Aspire with recent data

## Skill 4: Agent Session Instrumentation

Use when:

- analyzing prompt scaffolding and tool orchestration efficiency
- comparing context window and token consumption across approaches

Inputs:

- VS Code Copilot OTel settings
- OTEL_SERVICE_NAME and OTEL_RESOURCE_ATTRIBUTES

Commands:

- zsh scripts/06-open-vscode-with-otel.sh

Outputs:

- Copilot traces with invoke_agent, chat, execute_tool spans
- token usage and latency metrics in backend

Verify:

- traces for active chat turns are visible in Aspire

## Skill 5: Load and Trend Analysis

Use when:

- building baseline latency/token trends
- testing prompt/template changes under repeated traffic

Inputs:

- request count
- target model alias

Commands:

- zsh scripts/07-load-test.sh 20

Outputs:

- repeated gateway calls
- richer telemetry distribution for charting

Verify:

- completion count reported at end of script
- telemetry volume increases in Aspire over time

## Skill 6: Teardown and Reset

Use when:

- cleaning environment between experiments
- reclaiming resources

Commands:

- zsh scripts/04-stop.sh

Outputs:

- compose services stopped and removed
- optional Ollama process stop based on env flag

Verify:

- status script reports services DOWN
