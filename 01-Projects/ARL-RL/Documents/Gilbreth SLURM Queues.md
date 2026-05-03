# Gilbreth SLURM Queues & Partitions

The **Simple Linux Utility for Resource Management (SLURM)** manages job scheduling on Gilbreth. This document outlines the specific partitions available to us and our strategy for selecting them.

## Quick Recommendations (ARL-RL)

| Partition | GPU | VRAM | Status | Use Case |
|---|---|---|---|---|
| **`a100-40gb`**| **A100** | **40GB** | ✅ **Preferred** | **Primary.** Best performance for 64x64 and general usage. |
| `a30` | A30 | 24GB | ⚠️ Backup | Baseline. Good for standard runs. |
| `v100` | V100 | 32GB | ⚠️ Fallback | Good alternative if A100/A30 are full. Older architecture. |
| `a10` | A10 | 24GB | 🛑 Avoid | Usually full. Comparable to A30 but less available. |

---

## Detailed Partition Status (as of 2025-12-03)

Current cluster status based on `sinfo`.

### 1. `a100-40gb` (Primary)
- **Hardware**: NVIDIA A100 (40GB VRAM). Ampere architecture.
- **Availability**: ~32 nodes total. Often has idle nodes, offering good performance.
- **Use Case**: Recommended for 64x64 resolution scaling and future high-memory tasks.
- **Constraint**: `SBATCH --partition=a100-40gb`

### 2. `a30` (Backup)
- **Hardware**: NVIDIA A30 (24GB VRAM). Ampere architecture.
- **Availability**: ~24 nodes total. Often has 1-2 idle nodes.
- **Project Alignment**: All Phase 2 baselines were established here. Good for standard E1/E2 runs.
- **Constraint**: `SBATCH --partition=a30`

### 4. `a10`
- **Hardware**: NVIDIA A10 (24GB VRAM).
- **Availability**: ~16 nodes. Rarely idle.
- **Constraint**: `SBATCH --partition=a10`

---

## Job Submission Parts

A typical job submission command on Gilbreth has four main parts.

### 1. Partition (`--partition`)
Specifies the hardware pool.
- **Recommendation**: Default to `a100-40gb`. Switch to `a30` or `v100` if queue is deep.

### 2. Account (`--account`)
The "billing" account.
- **Value**: `sbagchi` (Our lab account).

### 3. QoS (`--qos`)
Determines priority and time limits.

| QoS | Max Time | Priority | GPU Policy | Recommendation |
|---|---|---|---|---|
| `normal` | 14 days | High | Deducts from account quota | Use for long production runs (>4h). |
| `standby` | 4 hours | Low | Backfill (no quota hit) | **ALWAYS USE** for smoke tests, debugging, or shorter runs. Faster scheduling. |

### 4. Resources (`--gres`, `--mem`, `--time`)
- **GPUs**: `--gres=gpu:1` (Standard for our single-agent RL).
- **Memory**: `--mem=50G` (Standard E2), `--mem=80G` (64x64 experiments).
- **Time**: Set closest upper bound (e.g., `04:00:00` for standby) to help the scheduler backfill.

## Common Commands

**Check specific partition availability:**
```bash
sinfo -p a30
sinfo -p v100
```

**Check queue for specific user:**
```bash
squeue -u jmckerra
```

**Check when a pending job might start:**
```bash
squeue -u jmckerra --start
```
