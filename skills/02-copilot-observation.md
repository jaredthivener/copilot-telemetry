# Skill: Copilot Telemetry Observation

## Use When

- Analyzing GitHub Copilot Chat model usage.
- Comparing token consumption across models.
- Investigating request latency or request failures.

## Inputs

- VS Code setting `github.copilot.chat.otel.enabled: true`.
- Stack is running.

## Quick CLI View

Use the local viewer script for terminal-first inspection:

```sh
./scripts/04-show-telemetry.sh all
```

For traces with expanded prompt context:

```sh
./scripts/04-show-telemetry.sh traces --prompt-full
```

## What To Inspect In Aspire

- Traces (resource/service filter set to `copilot-chat`):
  - `invoke_agent`
  - `chat`
  - `execute_tool`
- Metrics (resource/service filter set to `copilot-chat`):
  - `gen_ai.client.operation.duration`
  - `gen_ai.client.token.usage`
  - `copilot_chat.tool.call.count`
  - `copilot_chat.tool.call.duration`
  - `copilot_chat.agent.invocation.duration`
  - `copilot_chat.agent.turn.count`
  - `copilot_chat.time_to_first_token`
  - `copilot_chat.session.count`
- Structured logs/events:
  - Per-request records.
  - `error.type` on failures.
