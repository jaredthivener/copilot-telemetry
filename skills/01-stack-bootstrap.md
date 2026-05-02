# Skill: Stack Bootstrap

## Use When

- Initializing the observation stack from a clean state.
- Recovering from broken containers or configuration drift.

## Inputs

- Docker daemon running.

## Commands

```sh
scripts/01-start.sh
scripts/02-status.sh
```

## Expected Outcomes

- OTel Collector healthy at http://localhost:13133.
- Aspire Dashboard reachable at http://localhost:18888.
- Status script reports core endpoints as UP.

## Verify

```sh
scripts/02-status.sh
```
