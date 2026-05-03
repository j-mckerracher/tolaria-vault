# Automation Scripts

Bash scripts for automating common research tasks. Designed for use by LLM agents on systems with bash available.

---

## Scripts

### `create_experiment.sh`

Creates a new experiment from the template.

```bash
./create_experiment.sh "Title" "Objective" "PATH-X"
```

**Arguments**:
| Arg | Required | Description |
|-----|----------|-------------|
| Title | Yes | Experiment title (used in folder name) |
| Objective | Yes | One-sentence goal |
| PATH-X | No | Research path ID (e.g., PATH-A) |

**What it does**:
1. Determines next experiment ID (EXP-001, EXP-002, etc.)
2. Creates experiment folder with subdirectories (`results/`, `logs/`, `scripts/`)
3. Copies and fills experiment template
4. Adds entry to Master_Index.md

**Example**:
```bash
./create_experiment.sh "CPU Usage Patterns" "Analyze CPU utilization across Anvil jobs" "PATH-A"
# Creates: Experiments/EXP-001_CPU_Usage_Patterns/
```

---

### `update_status.sh`

Updates an experiment's status in its README and the Master Index.

```bash
./update_status.sh EXP-XXX "Status"
```

**Arguments**:
| Arg | Required | Description |
|-----|----------|-------------|
| EXP-XXX | Yes | Experiment ID |
| Status | Yes | New status value |

**Valid Statuses**:
- `Created` - Just defined, not submitted
- `Queued` - Submitted to cluster, waiting
- `Running` - Actively executing
- `Completed` - Finished successfully
- `Failed` - Job failed
- `Analysis` - Results being analyzed
- `Published` - Included in publication

**Example**:
```bash
./update_status.sh EXP-001 "Running"
```

---

### `submit_job.sh`

Submits a job to a supercomputer and logs the details.

```bash
./submit_job.sh EXP-XXX script.sh [slurm|pbs]
```

**Arguments**:
| Arg | Required | Description |
|-----|----------|-------------|
| EXP-XXX | Yes | Experiment ID |
| script.sh | Yes | Job script filename |
| scheduler | No | `slurm` (default) or `pbs` |

**What it does**:
1. Finds the experiment directory
2. Submits job via sbatch (SLURM) or qsub (PBS)
3. Captures job ID
4. Updates experiment README with job details
5. Sets status to "Queued"
6. Updates Master Index

**Examples**:
```bash
# SLURM (Anvil, Negishi)
./submit_job.sh EXP-001 job.slurm slurm

# PBS
./submit_job.sh EXP-002 job.pbs pbs
```

---

## Requirements

- Bash shell (Git Bash on Windows, native bash on Linux/Mac)
- `sed`, `grep`, `awk` (standard Unix utilities)
- For job submission: `sbatch` (SLURM) or `qsub` (PBS) available

---

## Running on Windows

These scripts require a bash environment. Options:

1. **Git Bash** (recommended): Included with Git for Windows
2. **WSL**: Windows Subsystem for Linux
3. **Cygwin**: Unix-like environment for Windows

Run scripts from the bash shell:
```bash
cd /c/Users/username/path/to/FRESCO-Research
./Research-System/Scripts/create_experiment.sh "Title" "Objective"
```

---

## For LLM Agents

When using these scripts:

1. **Always use full paths** or navigate to project root first
2. **Check script output** for success/error messages
3. **Verify changes** by reading the updated files
4. **If script fails**, fall back to manual file editing per runbook.md procedures
