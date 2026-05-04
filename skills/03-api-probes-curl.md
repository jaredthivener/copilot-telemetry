# Skill: API Probes and Data Pulls (curl)

## Use When

- Validating Aspire and collector endpoints over HTTP.
- Validating trace ingestion and forwarding without opening the UI.
- Pulling scriptable telemetry pipeline counters.
- Troubleshooting ingestion/forwarding without opening the UI.
- Rendering exported telemetry files in a human-readable terminal view.

## Inputs

- Stack is running.
- `curl` and `grep` installed.

## Commands

Set repo path once (works for any clone location):

```sh
REPO="$(git rev-parse --show-toplevel)"
```

Check Aspire health:

```sh
curl -sf http://localhost:18888/health
```

Check root redirect behavior:

```sh
curl -sI http://localhost:18888 | grep -E '^HTTP/|^Location:'
```

Pull collector metrics:

```sh
curl -s http://localhost:8888/metrics
```

Show a human-readable metrics signal summary (accepted/sent/refused by type):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_(receiver_accepted|receiver_refused|exporter_sent)_(log_records|metric_points|spans)' \
  | sed -E 's/\{[^}]*\}//'
```

Read latest exported trace payloads (JSONL):

```sh
curl -s "file://$REPO/telemetry/traces.jsonl" | tail -n 20
```

Read latest exported structured logs payloads (JSONL):

```sh
curl -s "file://$REPO/telemetry/logs.jsonl" | tail -n 20
```

Read latest exported metrics payloads (JSONL):

```sh
curl -s "file://$REPO/telemetry/metrics.jsonl" | tail -n 20
```

Show formatted telemetry (recommended for day-to-day inspection):

```sh
./scripts/04-show-telemetry.sh all
```

Show traces only:

```sh
./scripts/04-show-telemetry.sh traces
```

Show traces with full wrapped prompt text:

```sh
./scripts/04-show-telemetry.sh traces --prompt-full
```

Extract raw trace span names and timings from exported trace JSON (low-level fallback):

```sh
curl -s "file://$REPO/telemetry/traces.jsonl" \
  | tr -d '\n' \
  | sed 's/{"resourceSpans"/\n{"resourceSpans"/g' \
  | rg -o '"name":"[^"]+"|"startTimeUnixNano":"[0-9]+"|"endTimeUnixNano":"[0-9]+"'
```

Extract raw log records from exported logs JSON (low-level fallback):

```sh
curl -s "file://$REPO/telemetry/logs.jsonl" \
  | tr -d '\n' \
  | sed 's/{"resourceLogs"/\n{"resourceLogs"/g' \
  | rg -o '"severityText":"[^"]+"|"body":\{"stringValue":"[^"]+"\}'
```

Pull accepted counters (collector receiver side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_receiver_accepted_(log_records|metric_points|spans).*receiver="otlp".*transport="http"'
```

Pull refused trace counters (receiver side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_receiver_refused_spans.*receiver="otlp".*transport="http"'
```

Pull sent counters (collector exporter side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_exporter_sent_(log_records|metric_points|spans).*exporter="otlp_grpc/aspire"'
```

Pull trace send failures (exporter side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_exporter_send_failed_spans.*exporter="otlp_grpc/aspire"'
```

Pull trace drop counters (processor side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_processor_dropped_spans'
```

Pull exporter queue pressure:

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_exporter_queue_(size|capacity).*exporter="otlp_grpc/aspire"'
```

## Verify

- Generate a few Copilot Chat turns with at least one tool call to create `invoke_agent`, `chat`, and `execute_tool` spans.
- Confirm exported files exist and grow: `telemetry/traces.jsonl`, `telemetry/logs.jsonl`, `telemetry/metrics.jsonl`.
- Accepted counters increase after Copilot chat activity.
- Accepted `spans` increase after Copilot chat activity.
- Sent counters increase accordingly.
- Sent `spans` track accepted `spans` with minimal lag.
- Refused, dropped, and send-failed trace counters remain at zero under normal load.
- Queue size stays low under normal load.
- `./scripts/04-show-telemetry.sh all` renders non-empty sections with readable rows.
