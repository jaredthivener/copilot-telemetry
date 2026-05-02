# Skill: Stack Teardown

## Use When

- Done observing and ready to free local resources.
- Resetting state before the next run.

## Command

```sh
scripts/03-stop.sh
```

## Expected Outcomes

- Compose services are stopped and removed.

## Verify

```sh
scripts/02-status.sh
```

Core endpoints should report DOWN after teardown.
