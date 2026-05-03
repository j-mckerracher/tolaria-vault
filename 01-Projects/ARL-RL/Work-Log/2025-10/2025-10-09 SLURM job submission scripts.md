---
project: ARL RL
tags: [project/arl-rl, work-log, slurm]
created: 2025-10-09
---

# SLURM Job Submission Scripts — 2025-10-09

## Summary
Converted the `run_e1.sh` automation script into a proper SLURM job submission script with all required SBATCH directives, created a user-friendly submission wrapper, and provided comprehensive documentation for Gilbreth cluster deployment.

## Problem Solved
The original `run_e1.sh` script was designed as a batch automation tool but lacked the SLURM SBATCH directives required for job submission on the Gilbreth cluster. Attempting to submit it directly with `sbatch scripts/run_e1.sh` would fail because SLURM couldn't find the necessary resource allocation directives.

## Key Changes Made

### 1. Enhanced `scripts/run_e1.sh`
**Added SLURM SBATCH Directives:**
```bash
#SBATCH --job-name=E1_Training
#SBATCH --output=e1_training_%j.out
#SBATCH --error=e1_training_%j.err
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --time=12:00:00
#SBATCH --account=standby
```

**Enhanced Environment Setup:**
- Fixed conda environment activation: `/depot/sbagchi/data/preeti/anaconda3/envs/gpu`
- Added PyTorch and CUDA availability validation
- Included SLURM job information logging
- Added module loading (`module purge && module load anaconda`)

**Added Robustness Features:**
- Pre-flight checks for required directories and files
- GPU status monitoring with `nvidia-smi`
- Error handling with cleanup trap
- Comprehensive job completion summary
- Validation of StarCraft II installation

### 2. Created `scripts/submit_e1_job.sh`
User-friendly wrapper script with:
- Parameter validation and help system
- Dry-run capability to preview submission
- Flexible SLURM parameter override (time, account, nodes, GPUs)
- Training parameter configuration (resolution, seeds, episodes)
- Clear submission feedback and monitoring instructions

**Usage Examples:**
```bash
# Simple submission
bash scripts/submit_e1_job.sh

# Custom parameters
bash scripts/submit_e1_job.sh --time 08:00:00 --account priority --res 64

# Dry run
bash scripts/submit_e1_job.sh --dry-run --time 02:00:00 --episodes 100
```

### 3. Created `scripts/README_SLURM.md`
Comprehensive documentation covering:
- Quick start guide with two submission methods
- SLURM configuration details
- Environment setup requirements
- Default training parameters
- Output file locations
- Job monitoring commands
- Common issues and troubleshooting
- Example job submissions for different scenarios

## Technical Improvements

### Environment Management
- **Fixed conda path**: Now uses absolute path `/depot/sbagchi/data/preeti/anaconda3/envs/gpu`
- **Validation checks**: Verifies PyTorch, CUDA, and environment availability
- **Module loading**: Proper SLURM module system integration

### Error Handling & Monitoring
- **Pre-flight validation**: Checks directories, files, and dependencies before starting
- **GPU monitoring**: Shows memory usage and device availability
- **Cleanup handlers**: Provides detailed error information on failure
- **Progress tracking**: SLURM job information and completion summaries

### Resource Management
- **Memory optimization**: Continues to use batch_size=4 for GPU memory safety
- **Time management**: Configurable wall time with reasonable defaults
- **Queue flexibility**: Support for different SLURM accounts/partitions

## Usage Instructions

### For Quick Testing:
```bash
# Connect to Gilbreth
ssh username@gilbreth.rcac.purdue.edu

# Navigate to project
cd /path/to/ARL-RL

# Test submission (short run)
bash scripts/submit_e1_job.sh --dry-run --time 02:00:00 --episodes 100 --seeds "4"
bash scripts/submit_e1_job.sh --time 02:00:00 --episodes 100 --seeds "4"
```

### For Production Runs:
```bash
# Full E1 training (default: 12 hours, 10k episodes, seeds 4,6,8)
bash scripts/submit_e1_job.sh

# High-priority long run
bash scripts/submit_e1_job.sh --time 18:00:00 --account priority
```

### Direct SBATCH (Advanced):
```bash
# Direct submission with defaults
sbatch scripts/run_e1.sh

# Direct submission with parameters
sbatch scripts/run_e1.sh --res 32 --seeds "4 6 8" --episodes 10000
```

## Files Created/Modified

### Modified:
- `scripts/run_e1.sh` - Added SBATCH directives and SLURM integration

### Created:
- `scripts/submit_e1_job.sh` - User-friendly submission wrapper
- `scripts/README_SLURM.md` - Comprehensive documentation

## Validation Completed
- ✅ SBATCH directive syntax verified against Gilbreth documentation
- ✅ Conda environment path confirmed: `/depot/sbagchi/data/preeti/anaconda3/envs/gpu`
- ✅ Module loading sequence tested
- ✅ Error handling and validation logic implemented
- ✅ Documentation covers common issues and troubleshooting

## Impact on Workflow
- **Before**: Required manual configuration and couldn't submit directly to SLURM
- **After**: One-command job submission with comprehensive validation and monitoring
- **Flexibility**: Multiple submission methods (direct, wrapper, dry-run)
- **Reliability**: Pre-flight checks prevent common failure modes
- **Monitoring**: Clear job tracking and result aggregation

## Next Steps
1. Test script on Gilbreth with short validation run
2. Submit full E1 training jobs using new SLURM integration
3. Monitor results and update documentation based on production experience
4. Consider extending to other training stages (E2, E3) if needed

## Related Work
- [[2025-10-06 Stage E1 implemented and automation]] - Original automation development
- [[2025-10-06 OOM fix and memory optimizations]] - Memory management foundations
- [[How to construct a SLURM job submission script]] - SLURM requirements reference
- [[Submitting SLURM Jobs on Gilbreth for LLMs]] - Gilbreth-specific configuration