---
project: ARL RL
tags: [project/arl-rl, engineering-notes, mixed-precision, hpc, slurm]
created: 2025-10-11
---

# Engineering Notes — Mixed Precision, Memory, and HPC (Gilbreth)

These are practical notes and patterns collected while stabilizing Stage E1 training on Gilbreth with mixed precision.

## Mixed Precision (torch.amp) — common gotchas

1) Dtype-safe masking constants (FP16 overflow)
- Problem: Using large negative constants like `-1e9` under autocast (FP16) can overflow (min finite ≈ -65504), causing crashes.
- Fix pattern:

```python
# Use dtype-safe large negative for masks
neg_large = -1e4 if tensor.dtype == torch.float16 else -1e9
mask = torch.full_like(tensor, neg_large)
```

2) Where to use autocast
- Use autocast for forward passes and any inference-only blocks.
- Keep loss scaling via GradScaler only around backward()/optimizer.step().

```python
from torch.amp import autocast, GradScaler

scaler = GradScaler("cuda") if torch.cuda.is_available() else None

with autocast("cuda", enabled=(device.type == "cuda")):
    logits = model(inputs)
    loss = criterion(logits, targets)

if scaler is not None:
    scaler.scale(loss).backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    scaler.step(optimizer)
    scaler.update()
else:
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()
```

3) Numerical stability
- Prefer smooth L1 loss for value targets (Huber) to reduce sensitivity.
- Clamp rewards to a reasonable range (e.g., [-5, 5]).
- Grad clip (e.g., 1.0) helps avoid divergence under FP16.

## Memory Management and OOM prevention

1) Optimizer state preallocation (fail fast)
- Adam allocates momentum buffers on the first step; in a contended GPU this can fail late.
- Preallocate at init time with a dummy forward/backward to fail fast.

```python
# After constructing model/optimizer
with autocast("cuda", enabled=torch.cuda.is_available()):
    _ = model(dummy_inputs)
loss = model.some_head.weight.sum()
optimizer.zero_grad()
loss.backward()
optimizer.step()
optimizer.zero_grad()
```

2) PyTorch CUDA allocator tuning
- PYTORCH_CUDA_ALLOC_CONF suggestions:
  - `expandable_segments:True`
  - `garbage_collection_threshold:0.7`
  - `max_split_size_mb:128`

```bash
# Environment
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,garbage_collection_threshold:0.7,max_split_size_mb:128
```

3) Batch size and resolution
- When contended, reduce batch size (e.g., 8 → 4 → 2) and/or use 32×32 resolution.

## SLURM on Gilbreth — must-haves

1) Required placement/policy and resources
- Always specify: `--partition`, `--account`, and usually `--qos`.
- Request GPUs via `--gres=gpu:N`.
- Typical single-GPU job resources:

```bash
sbatch \
  --account <your_account> \
  --partition a30 \
  --qos standby \
  --ntasks 1 \
  --cpus-per-task 4 \
  --mem 50G \
  --gres gpu:1 \
  scripts/run_e1.sh --res 32 --seeds "4 6 8" --episodes 10000
```

2) Conda in non-interactive batch
- Skip module loads if Lmod modules are unreliable; initialize conda directly:

```bash
CONDA_ROOT=/depot/sbagchi/data/preeti/anaconda3
source "$CONDA_ROOT/etc/profile.d/conda.sh" || eval "$($CONDA_ROOT/bin/conda shell.bash hook)"
conda activate /depot/sbagchi/data/preeti/anaconda3/envs/gpu
```

- Alternative: call interpreter directly

```bash
/depot/sbagchi/data/preeti/anaconda3/envs/gpu/bin/python -u training_split.py
```

## Time limits and chunking strategy

1) Discover time limits (partition, QoS, association)
```bash
scontrol show partition a30 | grep -i time
sacctmgr show qos format=Name,MaxWall,Flags
sacctmgr show assoc where user=$USER format=Account,Partition,QOS,MaxWall
```

2) Chunk runs to fit the window (example: 2h standby)
- Throughput observed: ~2–3s/episode → ~2,400–3,000 episodes in 2h.
- Submit one seed per job, 3k episodes/job, chain jobs with dependencies.

3) Chain jobs so the next chunk starts after the prior completes
```bash
# First chunk (capture JobID)
JID=$(bash scripts/submit_e1_job.sh --account <acct> --partition a30 --qos standby \
  --time 2:00:00 --seeds "4" --episodes 3000 | awk '/Submitted batch job/{print $4}')

# Next chunk (starts after OK)
sbatch --dependency=afterok:$JID --account <acct> --partition a30 --qos standby \
  --time 2:00:00 scripts/run_e1.sh --res 32 --seeds "4" --episodes 3000
```

## Operational patterns

1) Pre-flight checks
- Verify SC2PATH, training script presence, create save/log directories.
- Log Python, torch, CUDA availability at job start.

2) Result persistence and aggregation
- Save `config.json` with env snapshot.
- Save `eval/test_results.json` with numeric types cast to builtin Python types.
- Append run summary to a central CSV (`e1_results.csv`).

3) Monitoring and retries
- Print SLURM info (job id, node, submit dir) at start.
- On failure, print final GPU status via `nvidia-smi`.
- Use a short 2h smoke test before 12h production runs.

## Recent fixes (context)
- FP16 masking overflow: replace `-1e9` with dtype-safe `neg_large` to avoid half overflow in action selection masking.
- Conda initialization: remove Lmod `anaconda` load; initialize conda directly and activate env by absolute path.
- Gilbreth submission: require `--partition/--account/--qos`, request GPUs via `--gres=gpu:N`.

## References
- [[2025-10-11 FP16 masking overflow fix]]
- [[2025-10-10 Stage E1 job submission success]]
- [[Submitting SLURM Jobs on Gilbreth for LLMs]]
