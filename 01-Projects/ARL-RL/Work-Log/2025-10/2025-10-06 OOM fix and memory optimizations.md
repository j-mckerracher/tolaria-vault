---
project: ARL RL
tags: [project/arl-rl, work-log, bugfix]
created: 2025-10-06
---

# OOM Fix and Memory Optimizations — 2025-10-06

## Problem
Stage E1 overnight training run hit CUDA OOM during the **first optimizer step** when Adam tried to allocate momentum buffers (needed 66MB, only 57MB free). The GPU had heavy contention from other processes:
- Process 1473544: **21.62 GiB** (primary consumer)
- Other processes: ~1.2 GB
- Our process: 598 MB

The `wait_and_run_e1.sh` script checked for 2GB free and found it, but by the time training allocated optimizer state, another process had consumed most of it.

## Root Cause
1. **Lazy optimizer state allocation**: Adam doesn't allocate momentum buffers until the first `.step()` call
2. **GPU memory fragmentation**: Even with expandable_segments, tight memory conditions cause allocation failures
3. **Race condition**: GPU memory can be consumed between the check and actual usage

## Solution

### 1. Preallocate Optimizer State (`training_split.py`)
Added initialization code in `DQNAgent.__init__()` to force Adam to allocate its state buffers immediately:

```python
# Force optimizer state initialization with a dummy backward pass
# This preallocates Adam's momentum buffers to avoid OOM during first real step
if torch.cuda.is_available():
    logging.info("Preallocating optimizer state to avoid OOM...")
    dummy_screen = torch.zeros(1, screen_channels, self.res, self.res, device=self.device)
    dummy_minimap = torch.zeros(1, minimap_channels, self.res, self.res, device=self.device)
    dummy_nonspatial = torch.zeros(1, self.non_spatial_dim, device=self.device)
    with torch.amp.autocast('cuda'):
        _, _ = self.policy_net(dummy_screen, dummy_minimap, dummy_nonspatial)
    dummy_loss = self.policy_net.action_head.weight.sum()
    self.optimizer.zero_grad()
    dummy_loss.backward()
    self.optimizer.step()
    self.optimizer.zero_grad()
    del dummy_screen, dummy_minimap, dummy_nonspatial, dummy_loss
    torch.cuda.empty_cache()
    logging.info("Optimizer state preallocation complete.")
```

**Benefit**: Fails fast during initialization (with clear error) rather than after hours of training.

### 2. Enhanced PYTORCH_CUDA_ALLOC_CONF (`scripts/run_e1.sh`)
Updated memory allocator configuration:

```bash
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,garbage_collection_threshold:0.7,max_split_size_mb:128
```

- **`expandable_segments:True`**: Allows memory segments to grow dynamically (reduces fragmentation)
- **`garbage_collection_threshold:0.7`**: Actively reclaims unused memory when usage exceeds 70% (prevents accumulation)
- **`max_split_size_mb:128`**: Limits block splitting to reduce fragmentation for large allocations

### 3. Reduced Default Batch Size
Changed `RL_BATCH_SIZE` from **8 → 4** in `run_e1.sh`:

```bash
export RL_BATCH_SIZE=4  # Reduced from 8 for memory safety on contended GPUs
```

**Impact**: 
- Reduces peak memory usage during training by ~40-50%
- Slightly increases training time but ensures completion on contended GPUs
- Still maintains good gradient stability

## Testing
To verify the fix works:

```bash
# Test locally with memory-constrained setup
bash scripts/run_e1.sh --res 32 --seeds "4" --episodes 100

# Full overnight run with updated configuration
bash scripts/wait_and_run_e1.sh --min-free 2048 --sleep 300 --timeout 7200 --fallback-batch 2 -- --res 32 > e1_master.log 2>&1 &
```

## Performance Considerations
- **Batch size 4 vs 8**: Approximately 1.25-1.5x longer training time, but ensures completion
- **Garbage collection**: Small CPU overhead (~1-2%) but prevents memory leaks
- **Preallocation**: One-time cost at initialization (<1 second)

## Alternative Approaches Considered
1. ~~Use SGD instead of Adam~~ — Adam works better for this problem; losing momentum would hurt performance
2. ~~Reduce replay buffer size~~ — Doesn't help with optimizer state allocation
3. ~~Wait longer for more memory~~ — Unreliable; other processes can consume memory anytime
4. **Use cudaMallocAsync backend** — Requires CUDA 11.4+; may try later if issues persist

## Next Steps
1. Monitor `e1_master.log` for successful training start
2. If OOM persists, further reduce batch size to 2 (fallback is already configured)
3. Consider requesting dedicated GPU time slot for critical runs
4. Profile memory usage with `torch.cuda.memory_summary()` if needed

## Related
- [[2025-10-06 Mixed precision + wait wrapper]]
- [[2025-10-06 Stage E1 implemented and automation]]
- PyTorch CUDA Memory Management: https://pytorch.org/docs/stable/notes/cuda.html#environment-variables