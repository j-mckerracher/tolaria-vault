# Scripts Reference — ARL RL

> [!IMPORTANT] Reference Only
> These scripts are **reference copies** for documentation purposes.  
> **Actual executable scripts** are located at: `/home/jmckerra/Code/ARL-RL/scripts/` on Gilbreth

## Purpose

This directory contains markdown-formatted copies of SLURM job submission scripts for quick reference in Obsidian. These are snapshots taken from the actual repository to improve discoverability and offline access.

## Contents

- [[run_e1]] — Stage E1 training script (Double DQN + LR scheduler)
- [[run_e2]] — Stage E2 training script (Dueling DQN)
- [[run_e3_local]] — Stage E3 local testing script (PER)
- [[submit_e1_job]] — SLURM job submission wrapper

## Usage

**To use these scripts**:
1. SSH to Gilbreth: `ssh jmckerra@gilbreth.rcac.purdue.edu`
2. Navigate to code: `cd /home/jmckerra/Code/ARL-RL`
3. Use actual scripts: `sbatch scripts/run_e2.sh --res 64 --seeds "4 6 8"`

**To update these references**:
- Copy updated scripts from Gilbreth repository when significant changes are made
- Maintain as `.md` files with bash code blocks for Obsidian rendering

## Related

- [[Documents/Common Commands]] — SLURM commands and usage examples
- [[Documents/Submitting SLURM Jobs on Gilbreth for LLMs]] — Job submission guide
- [[01-Projects/Demo-ICLR-Confidential/Don't Forget]] — Current preferred submission methods
