---
project: ARL RL
tags: [project/arl-rl, work-log, bugfix, slurm]
created: 2025-10-11
---

# FP16 masking overflow fix (autocast-safe) — 2025-10-11

## Summary
Fixed a mixed-precision (FP16) overflow in action masking during exploitation that caused the job to crash under torch.amp autocast.

Error observed:
```text
RuntimeError: value cannot be converted to type at::Half without overflow
  at training_split.py:447 in select_action
  q_masked[self.config.ACTION_NO_OP] = -1e9
```

## Root cause
- Under autocast('cuda'), tensors may be float16 (FP16).
- Using a constant like `-1e9` to penalize actions overflows FP16 (min finite ≈ -65504).

## Fix
- Use a dtype-safe large negative value for masking:
  - `neg_large = -1e4 if q_masked.dtype == torch.float16 else -1e9`
  - Build the mask with `torch.full_like(q_masked, neg_large)`
  - Assign `q_masked[self.config.ACTION_NO_OP] = neg_large` when heavily penalizing NO_OP

Patch (excerpt):
```python
# Before
q_masked = action_q.clone().squeeze(0)
mask = torch.ones_like(q_masked) * -1e9  # penalize unavailable actions
...
q_masked[self.config.ACTION_NO_OP] = -1e9

# After (autocast-safe)
q_masked = action_q.clone().squeeze(0)
neg_large = -1e4 if q_masked.dtype == torch.float16 else -1e9
mask = torch.full_like(q_masked, neg_large)
...
q_masked[self.config.ACTION_NO_OP] = neg_large
```

File changed:
- `training_split.py` (DQNAgent.select_action exploitation path)

## Related environment fixes
- SLURM job script now initializes Conda directly without loading any Lmod “anaconda” modules:
  - `source /depot/sbagchi/data/preeti/anaconda3/etc/profile.d/conda.sh` (or `eval "$($CONDA_ROOT/bin/conda shell.bash hook)"`)
  - `conda activate /depot/sbagchi/data/preeti/anaconda3/envs/gpu`
- Avoids Lmod error "cannot load anaconda".

## Validation
- Job submitted and ran with autocast + FP16, past the action selection step without overflow.
- Logs showed:
  - Python: `/depot/.../envs/gpu/bin/python`
  - PyTorch: `2.7.0+cu126`, CUDA available: `True`
  - Environment ready; training started with Episode 1.
- Subsequent run (Job ID e.g., 9718771) proceeded without the prior exception.

## Next
- Monitor training curves and CSV aggregation (`e1_results.csv`).
- If masking strength needs tuning under FP16, adjust `neg_large` (e.g., -1e3 to -1e5) based on empirical behavior.
- Consider centralizing a utility for dtype-safe masking constants.

## Links
- [[2025-10-10 Stage E1 job submission success]]
- [[2025-10-10 Gilbreth partition-account-qos fix]]
- [[Submitting SLURM Jobs on Gilbreth for LLMs]]
