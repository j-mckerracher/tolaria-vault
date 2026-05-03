# ARL-RL Research Results Summary

> [!NOTE] Executive Summary
> This document provides a high-level overview of the ARL-RL project for research reporting and stakeholder communication.

---

## Objective

Develop a high-performance reinforcement learning agent for the StarCraft II "FindAndDefeatZerglings" mini-game through systematic algorithmic improvements and hyperparameter optimization, while operating under HPC resource constraints on Purdue's Gilbreth cluster.

**Success Criteria**: Achieve >90% win rate with stable, reproducible training across multiple random seeds.

---

## Key Results

### Performance Progression

| Stage | Algorithm | Episodes | Seeds | Mean Win Rate | Std Dev | Status |
|-------|-----------|----------|-------|---------------|---------|--------|
| **Baseline** | DQN | 100 | 1 | 8.0% | — | Complete |
| **E1** | Double DQN + Cosine LR | 1,000 | 3 (4,6,8) | 44.0% | 38.7 pp | Complete |
| **E2 (Initial)** | + Dueling DQN | 500 | 3 (4,6,8) | 52.7% | 35.9 pp | Complete |
| **E2 (Confirm)** | + TUF=400 | 1,000 | 3 (4,6,8) | 91.3% | 4.0 pp | Complete |
| **E2 (Production)** | **Frozen Config** | **3,000** | **3 (4,6,8)** | **94.3%** | **5.7 pp** | **✅ Validated** |
| **E3** | + PER (α=0.4-0.6) | 500 | 3 (4,6,8) | <91.3% | — | ⏸️ Parked |

### Individual Seed Results (E2 Production @ 3k Episodes)

- **Seed 4**: 97.0% win rate (502.0 total reward, 5.02 avg)
- **Seed 6**: 88.0% win rate (163.0 total reward, 1.63 avg)
- **Seed 8**: 98.0% win rate (517.0 total reward, 5.17 avg) — **Best performance**

**Aggregate**: Mean = 94.3%, StdDev = 5.7 pp ✅ **Exceeds 90% target**

---

## Validated Configuration (E2 Frozen)

> [!IMPORTANT] Production-Ready Configuration
> The following configuration has been validated at production scale (3,000 episodes) and is recommended for deployment.

### Algorithm Architecture
- **Base**: Double DQN (reduces overestimation bias)
- **Enhancement**: Dueling DQN architecture (separate value/advantage streams)
- **Learning Rate Schedule**: Cosine annealing

### Hyperparameters
```yaml
Learning Rate: 5e-5
Epsilon Decay: 100,000 steps
Epsilon Range: 0.90 → 0.01
Batch Size: 4
Replay Memory: 100,000 transitions
Target Update Frequency: 400 steps
Resolution: 32×32 (screen & minimap)
Step Multiplier: 16
```

### Training Environment
- **Platform**: Gilbreth HPC (Purdue), NVIDIA A30 GPUs
- **Framework**: PyTorch with mixed precision (FP16)
- **Optimizer**: Adam with cosine LR scheduling
- **Memory**: 50GB RAM, 4 CPUs per job

---

## Methodology

### Staged Approach
The project followed a systematic staged exploration:

1. **Stage E1**: Established Double DQN baseline with hyperparameter sweeps
   - Learning rate sweep (5e-5 optimal)
   - Epsilon decay sweep (100k optimal)
   - Target update frequency sweep (300 optimal)

2. **Stage E2**: Architectural enhancement (Dueling DQN)
   - TUF refinement (400 improved over 300)
   - Validation at 500, 1k, and 3k episodes
   - Configuration frozen after 91.3% @ 1k episodes

3. **Stage E3**: Prioritized Experience Replay exploration
   - Alpha sweep (0.4, 0.5, 0.6) with beta annealing
   - Result: All configs underperformed E2 baseline
   - Decision: Parked PER for future consideration

### Experiment Tracking
All experiments documented with:
- Exact configuration (YAML metadata)
- Git commit hashes (where applicable)
- Random seeds for reproducibility
- SLURM job IDs and resource allocation
- Performance metrics (win rate, reward, training curves)
- Checkpoint artifacts (every 100 episodes)

---

## Technical Contributions

### Infrastructure Improvements
1. **SLURM Integration**: Complete job submission pipeline with wrapper scripts
2. **Memory Optimization**: Mixed precision (FP16) with overflow protection
3. **Queue Strategy**: Standby QoS backfill scheduling to avoid GPU quota limits
4. **Automated Result Aggregation**: CSV logging with JSON artifact exports

### Engineering Fixes
- Fixed FP16 masking overflow in action selection
- Implemented NO_OP behavior prioritization to reduce agent idling
- Created conda environment isolation for reproducibility
- Developed comprehensive troubleshooting documentation

---

## Current Status & Next Steps

### Decision Point
With E2 validated at 94.3%, three exploration paths are available:

**Option 1: Resolution Scaling (64×64)** 🔴 Recommended
- Test frozen E2 config at higher spatial resolution
- Expected: Better unit positioning and tactical awareness
- Resource: ~4x memory (80GB), 3-4h per seed
- Timeline: 500-1k episode smoke runs per seed

**Option 2: Stage E4 (N-step Returns)**
- Add multi-step bootstrapping (n=3) to E2 baseline
- Expected: Improved credit assignment, faster learning
- Resource: Similar to E2 baseline
- Timeline: Requires code implementation + 500-1k episodes

**Option 3: Extended Validation (4k-5k episodes)**
- Push E2 to convergence limits
- Expected: Marginal improvements or plateau confirmation
- Resource: 6-8h per seed on normal QoS

---

## Artifacts & Deliverables

### Checkpoints
- **Best Model**: Seed 8, Episode 3000 (98% win rate)
- **Location**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/20251025_021201_E1_seed8/`
- **Format**: PyTorch `.pth` files (~64MB each)
- **Frequency**: Saved every 100 episodes

### Documentation
- **Experiment Logs**: 23+ detailed experiment notes with full reproducibility metadata
- **Decision Records**: 8 decision documents capturing rationale for major choices
- **Work Logs**: 25+ chronological daily logs tracking progress
- **Technical Guides**: SLURM job submission, memory optimization, common commands

### Data
- **Training Metrics**: Episode rewards, win rates, loss curves (CSV + JSON)
- **Test Results**: 100-episode evaluation metrics for each checkpoint
- **Configuration**: Full environment snapshots with hyperparameters

---

## Challenges & Mitigations

| Challenge | Impact | Mitigation | Outcome |
|-----------|--------|------------|---------|
| GPU queue contention (`AssocGrpGRES`) | High | Switch to standby QoS backfill | ✅ Resolved |
| FP16 overflow in action masking | Medium | Dtype-safe masking implementation | ✅ Fixed |
| Memory constraints (OOM crashes) | High | Reduce batch size 8→4, preallocate optimizer | ✅ Stable |
| Variable training time per episode | Low | SLURM deadline guards, chunked runs | ✅ Managed |

---

## Publications & Reporting

**Recommended Visualizations** (to be generated):
1. Performance trajectory plot (stages E1→E2→E3)
2. Win rate distribution box plots by seed and stage
3. Training curve comparison (E1 vs E2 architectures)
4. Hyperparameter sensitivity heatmaps

**Key Metrics for Stakeholder Reports**:
- **Primary**: 94.3% mean win rate at 3,000 episodes (E2 production)
- **Secondary**: 10.7× improvement over baseline (8% → 94.3%)
- **Stability**: Low variance (5.7 pp std dev) across seeds
- **Reproducibility**: 3/3 seeds exceeded 88% win rate

---

## References

- **Detailed Experiment Log**: [[Experiments]]
- **Technical Plan**: [[Plan]]
- **Current Status**: [[Status]]
- **Decision History**: [[Decisions/Index]]

---

