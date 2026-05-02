# Skill: API Probes and Data Pulls (curl)

## Use When

- Validating Aspire and collector endpoints over HTTP.
- Pulling scriptable telemetry pipeline counters.
- Troubleshooting ingestion/forwarding without opening the UI.

## Inputs

- Stack is running.
- `curl` and `grep` installed.

## Commands

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

Pull accepted counters (collector receiver side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_receiver_accepted_(log_records|metric_points|spans).*receiver="otlp".*transport="http"'
```

Pull sent counters (collector exporter side):

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_exporter_sent_(log_records|metric_points|spans).*exporter="otlp_grpc/aspire"'
```

Pull exporter queue pressure:

```sh
curl -s http://localhost:8888/metrics \
  | grep -E 'otelcol_exporter_queue_(size|capacity).*exporter="otlp_grpc/aspire"'
```

## Verify

- Accepted counters increase after Copilot chat activity.
- Sent counters increase accordingly.
- Queue size stays low under normal load.
