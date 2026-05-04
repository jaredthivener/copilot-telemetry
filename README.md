# Copilot Telemetry Stack

Observe GitHub Copilot Chat telemetry locally using an OpenTelemetry Collector and Aspire Dashboard.

![Observe GitHub Copilot Chat Telemetry Locally](images/ChatGPT%20Image%20May%203%2C%202026%2C%2002_35_05%20PM.png)

## What This Does

VS Code Copilot Chat emits OTLP telemetry when configured. This stack receives it and
visualizes it in Aspire Dashboard — giving you per-model token usage, latency,
structured request logs, and agent/tool traces without sending data to any
external service.

## Architecture

```
VS Code Copilot Chat
  └─> OTLP HTTP (localhost:4318)
        └─> OTel Collector (Docker)
              └─> gRPC (aspire-dashboard:18889)
                    └─> Aspire Dashboard UI (localhost:18888)
```

## What You Can See in Aspire

**Traces** (`service.name = copilot-chat`):
- `invoke_agent` spans for full agent orchestration
- `chat` spans for individual LLM calls
- `execute_tool` spans for tool invocations (including success/failure timing)

Open Aspire at `http://localhost:18888`, go to **Traces**, and filter by
`service.name = copilot-chat`.

**Metrics** (`service.name = copilot-chat`):
- `gen_ai.client.operation.duration` — request latency histogram per model
- `gen_ai.client.token.usage` — input/output token counts per model
- `copilot_chat.tool.call.count` — tool calls by name and outcome
- `copilot_chat.tool.call.duration` — tool execution latency
- `copilot_chat.agent.invocation.duration` — end-to-end agent runtime
- `copilot_chat.agent.turn.count` — LLM turn count per agent invocation
- `copilot_chat.time_to_first_token` — first-token latency
- `copilot_chat.session.count` — chat sessions started

**Structured Logs** (`service.name = copilot-chat`):
- Per-request and per-turn records with model, provider, and error details

**Events** (`service.name = copilot-chat`):
- `gen_ai.client.inference.operation.details`
- `copilot_chat.session.start`
- `copilot_chat.tool.call`
- `copilot_chat.agent.turn`

## Prerequisites

- Docker Desktop running
- VS Code with GitHub Copilot Chat extension

## VS Code Settings

The `.vscode/settings.json` in this repo configures Copilot Chat to export telemetry:

```json
{
  "github.copilot.chat.otel.enabled": true,
  "github.copilot.chat.otel.exporterType": "otlp-http",
  "github.copilot.chat.otel.otlpEndpoint": "http://localhost:4318",
  "github.copilot.chat.otel.captureContent": true
}
```

Open this workspace in VS Code for these settings to take effect.

## Generate And Verify Traces

1. Start the stack with `./scripts/01-start.sh`.
2. Open this folder in VS Code and run a few Copilot Chat prompts that include at least one tool call.
3. Open Aspire Dashboard (`http://localhost:18888`) and inspect **Traces**.
4. Confirm span tree shape like: `invoke_agent -> chat -> execute_tool -> chat`.

If traces do not appear, verify `github.copilot.chat.otel.enabled` is true and
`github.copilot.chat.otel.otlpEndpoint` is `http://localhost:4318`.

## Commands

Start stack:
```sh
./scripts/01-start.sh
```

Check status:
```sh
./scripts/02-status.sh
```

Stop stack:
```sh
./scripts/03-stop.sh
```

## Endpoints

| Service | URL |
|---------|-----|
| Aspire Dashboard UI | http://localhost:18888 |
| OTLP HTTP (send telemetry here) | http://localhost:4318 |
| OTLP gRPC | localhost:4317 |
| Collector health | http://localhost:13133 |
