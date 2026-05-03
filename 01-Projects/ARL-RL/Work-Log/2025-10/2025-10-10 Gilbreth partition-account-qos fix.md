---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-10
---

# Gilbreth Submission Fix — Partition/Account/QoS (2025-10-10)

## Summary
Adjusted SLURM documentation and scripts to comply with Gilbreth’s requirement to explicitly specify partition, account, and (optionally) QoS. Replaced incorrect use of `--account=standby` with correct usage (`--partition=<...>`, `--account=<your_account>`, `--qos=standby|normal`).

## Changes
- Updated docs:
  - Documents/Submitting SLURM Jobs on Gilbreth for LLMs: Added required partition/account/QoS section and fixed code fences.
  - Documents/How to construct a SLURM job submission script: Updated directive examples (ntasks, gpus-per-task, cpus-per-task, mem, partition/account/qos) and fixed formatting.
  - Documents/Gilbreth SLURM Queues: Confirmed guidance and linked usage snippet.
- Code (for reference):
  - scripts/run_e1.sh: SBATCH defaults now include ntasks/GPUs/mem and partition/qos; account is passed at submit-time.
  - scripts/submit_e1_job.sh: Requires --account and supports --partition/--qos and resource flags.

## Correct Submission Pattern (Gilbreth)

```bash
# Find your account (group name)
slist

# Submit with required account (A30 partition, standby QoS)
sbatch --account <your_account> --partition a30 --qos standby scripts/run_e1.sh
```

Or with the wrapper:

```bash
bash scripts/submit_e1_job.sh --account <your_account> --partition a30 --qos standby
```

## Rationale
- On Gilbreth, “standby” is a QoS, not an account.
- You must explicitly specify partition and your group account.

## Next
- Use wrapper for convenience (validates presence of account).
- If targeting other GPUs, change `--partition` to `v100`, `a100-40gb`, etc. Use constraints as needed (e.g., `--constraint v100-32gb`).
