# EXP-005: Anvil verification (FIND-016)

- **Status**: Completed
- **Research Path**: PATH-B

## Objective

Verify whether Anvil can recover runtime prediction signal without timelimit (FIND-016), and test whether the earlier result was driven by user leakage.

## Outputs

- Results: `results/`
- Logs: `logs/`
- Scripts: `scripts/`

## Key Result (high-level)

The earlier apparent Anvil "signal recovery" without timelimit was refuted; performance collapses under user-aware splits, indicating user-level memorization.
