# Copilot Telemetry Stack

Observe GitHub Copilot Chat telemetry locally using an OpenTelemetry Collector and Aspire Dashboard.

## What This Does

VS Code Copilot Chat emits OTLP telemetry when configured. This stack receives it and
visualizes it in Aspire Dashboard — giving you per-model token usage, latency, and
structured request logs without sending data to any external service.

## Architecture

```
VS Code Copilot Chat
  └─> OTLP HTTP (localhost:4318)
        └─> OTel Collector (Docker)
              └─> gRPC (aspire-dashboard:18889)
                    └─> Aspire Dashboard UI (localhost:18888)
```

## What You Can See in Aspire

**Metrics** (`service.name = copilot-chat`):
- `gen_ai.client.operation.duration` — request latency histogram per model
- `gen_ai.client.token.usage` — input/output token counts per model
- `copilot_chat.session.count` — active session counter

**Structured Logs** (`service.name = copilot-chat`):
- Per-request records with model, provider, error details

**Not yet available**: Traces (tool calls, agent turns) — Copilot Chat 0.46.x does not
emit OTLP trace data. Only metrics and logs are exported.

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

## Commands

Start stack:
```zsh
zsh scripts/01-start.sh
```

Check status:
```zsh
zsh scripts/02-status.sh
```

Stop stack:
```zsh
zsh scripts/03-stop.sh
```

## Endpoints

| Service | URL |
|---------|-----|
| Aspire Dashboard UI | http://localhost:18888 |
| OTLP HTTP (send telemetry here) | http://localhost:4318 |
| OTLP gRPC | localhost:4317 |
| Collector health | http://localhost:13133 |
