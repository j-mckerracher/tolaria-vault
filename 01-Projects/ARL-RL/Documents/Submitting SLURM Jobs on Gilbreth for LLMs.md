# Guide: Submitting SLURM Jobs on Gilbreth for LLMs

This guide provides a systematic approach to submitting jobs on the Gilbreth cluster using the **SLURM workload manager**. The primary command for job submission is `sbatch`. This guide will cover the essential options and best practices to ensure successful job submission.

---

## Core Concepts: `sbatch` and Submission Scripts

The fundamental command to submit a job is:

```bash
sbatch my_job_script.sh
```

- `my_job_script.sh`: This is a shell script that contains two things:
    
    1. **SLURM Directives**: Special comments at the top of the file that start with `#SBATCH`. These directives specify the resources your job needs (nodes, GPUs, time, etc.).
        
    2. **Job Commands**: The actual commands you want to execute for your job.
        

---

## Essential `sbatch` Options (Mandatory for Gilbreth)

On Gilbreth, every job must specify both placement/policy and resources:

- Placement/Policy (required on Gilbreth):
  - `--partition=<partition>` (e.g., `a30`, `a100-40gb`, `v100`)
  - `--account=<your_account>` (find with `slist`)
  - `--qos=<qos>` (e.g., `standby` for idle resources, or `normal`)

- Resources (typical for single‑GPU jobs):
  - `--ntasks=<n>` (e.g., `1`)
  - `--cpus-per-task=<n>` (e.g., `4`)
  - `--mem=<size>` (e.g., `50G`)
  - GPUs: `--gres=gpu:<n>` (recommended on Gilbreth) or `--gpus-per-task=<n>`

Example SBATCH block:

```bash
# Resources
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=50G
#SBATCH --gres=gpu:1
# Placement/policy
#SBATCH --partition=a30
#SBATCH --account=<your_account>
#SBATCH --qos=standby
```

Command‑line override example (overrides any SBATCH lines):

```bash
sbatch \
  --account <your_account> \
  --partition a30 \
  --qos standby \
  --ntasks 1 \
  --cpus-per-task 4 \
  --mem 50G \
  --gres gpu:1 \
  my_job_script.sh
```

### Discovering Time Limits (Partition/QoS)

You can check the maximum wall times allowed by your partition and QoS:

```bash
scontrol show partition a30 | grep -i time
sacctmgr show qos format=Name,MaxWall,Flags
sacctmgr show assoc where user=$USER format=Account,Partition,QOS,MaxWall
```

### Chunked Runs and Dependencies

When your QoS window is short, split runs into episode chunks that fit within the time limit and chain them:

```bash
# First chunk (2h, one seed)
JID=$(bash scripts/submit_e1_job.sh --account <acct> --partition a30 --qos standby \
  --time 2:00:00 --seeds "4" --episodes 3000 | awk '/Submitted batch job/{print $4}')

# Next chunk starts when the prior job finishes successfully
sbatch --dependency=afterok:$JID --account <acct> --partition a30 --qos standby \
  --time 2:00:00 scripts/run_e1.sh --res 32 --seeds "4" --episodes 3000
```

### Wall Time

- `--time=<time>` or `-t <time>`: Maximum run time (formats: `DD-HH:MM:SS`, `HH:MM:SS`, or minutes).

Example:

```bash
# In your submission script
#SBATCH --time=02:30:00
```

---

## Partition, Account, and QOS (Gilbreth)

On Gilbreth, you must specify all three of the following when submitting jobs:
- `--partition=<partition>`: Which GPU partition to target (e.g., `a30`, `a100-40gb`, `v100`).
- `--account=<your_account>`: Your group account. Find yours with `slist`.
- `--qos=<qos>`: The job QoS; use `standby` to use idle resources (lower priority, shorter max wall-time), or `normal` for regular priority.

Example SBATCH block:

```bash
# Resources
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=50G

# Placement and policy (Gilbreth)
#SBATCH --partition=a30
#SBATCH --account=<your_account>
#SBATCH --qos=standby  # or omit to use default normal QoS
```

---

## Advanced Job Configurations

### 1. Multi-Node Jobs

If your code is designed for parallel processing across multiple nodes (e.g., using MPI), you can request multiple nodes as shown above.

**Example:** A job script for a multi-node MPI application might look like this:

Bash

```
#!/bin/bash
#SBATCH --nodes=4
#SBATCH --gpus-per-node=1
#SBATCH --time=01:00:00

# Your MPI execution command
mpirun ./my_parallel_program
```

### 2. Multi-Task Jobs on a Single Node

To run multiple tasks within a single node, you can use the `--ntasks-per-node` option.

- `--ntasks-per-node=<number>`: Specifies the number of tasks to launch on each node.
    

**Example:** To run 8 tasks on a single node:

Bash

```
#!/bin/bash
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=00:30:00

# This will run 'my_program' 8 times in parallel on the same node
srun my_program
```

---

## Best Practices Summary

1. **Use `#SBATCH` Directives**: It is best practice to include all your resource requests as `#SBATCH` directives at the top of your submission script. This makes your job submission process repeatable and easier to track.
    
2. **Command-Line Overrides**: Remember that any options specified directly on the command line with `sbatch` will take precedence over the `#SBATCH` directives in the script.
    
3. **Request Only What You Need**: Be realistic with your resource requests, especially wall time. Over-requesting resources can lead to longer queue times.
    

---
