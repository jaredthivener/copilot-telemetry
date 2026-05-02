# Skill: Copilot Telemetry Observation

## Use When

- Analyzing GitHub Copilot Chat model usage.
- Comparing token consumption across models.
- Investigating request latency or request failures.

## Inputs

- VS Code setting `github.copilot.chat.otel.enabled: true`.
- Stack is running.

## What To Inspect In Aspire

- Metrics (resource/service filter set to `copilot-chat`):
  - `gen_ai.client.operation.duration`
  - `gen_ai.client.token.usage`
  - `copilot_chat.session.count`
- Structured logs:
  - Per-request records.
  - `error.type` on failures.

## Current Limitation

- Copilot Chat 0.46.x exports metrics and logs.
- Trace-level data is not exported yet.
