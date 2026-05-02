# SKILLS.md

## Purpose

This catalog is intentionally lightweight.

Detailed procedures live in focused files under `skills/` to improve retrieval precision and keep this index small.

## Skill Index

- Stack Bootstrap
  - File: `skills/01-stack-bootstrap.md`
  - Use when starting or recovering the local telemetry stack.

- Copilot Telemetry Observation
  - File: `skills/02-copilot-observation.md`
  - Use when inspecting Copilot latency, token usage, and structured request logs.

- API Probes and Data Pulls (curl)
  - File: `skills/03-api-probes-curl.md`
  - Use when validating endpoints and pulling collector counters via shell commands.

- Stack Teardown
  - File: `skills/04-stack-teardown.md`
  - Use when stopping and cleaning local stack resources.

## Authoring Guidelines

- Keep this file as an index only.
- Place command-heavy workflows in one skill file per topic.
- Remove stale commands as soon as scripts change.
