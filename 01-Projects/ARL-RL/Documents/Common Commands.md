# Common Commands — ARL RL (Gilbreth)

## Job submission (quick recipes)

- 12h, normal QoS, 4k episodes across seeds 4/6/8
```bash
bash scripts/submit_e1_job.sh --account sbagchi --partition a30 --qos normal --time 12:00:00 --episodes 4000
```

- 2h smoke test, one seed, 3k episodes (standby QoS)
```bash
bash scripts/submit_e1_job.sh --account sbagchi --partition a30 --qos standby --time 2:00:00 --seeds "4" --episodes 3000
```

- Dry run (show sbatch command without submitting)
```bash
bash scripts/submit_e1_job.sh --account sbagchi --dry-run --time 02:00:00 --res 32
```

- Direct sbatch (bypass wrapper)
```bash
sbatch --account sbagchi --partition a30 --qos standby \
  --ntasks 1 --cpus-per-task 4 --mem 50G --gres gpu:1 \
  scripts/run_e1.sh --res 32 --seeds "4" --episodes 3000
```

## Discover time limits (partition/QoS/association)
```bash
scontrol show partition a30 | grep -i time
sacctmgr show qos format=Name,MaxWall,Flags
sacctmgr show assoc where user=$USER format=Account,Partition,QOS,MaxWall
```

## Monitor jobs
```bash
# All my jobs
squeue -u $USER

# Specific job
squeue -j JOBID

# Detailed view
scontrol show job JOBID | egrep -i 'JobId|JobName|UserId|State|RunTime|TimeLimit|NodeList|Partition|QOS'

# Runtime stats (RSS, CPU)
sstat -j JOBID --format=AveCPU,AvePages,AveRSS,MaxRSS,Elapsed
```

## Logs (live tail)
```bash
# Follow stdout
tail -f e1_training_JOBID.out
# Follow stderr
tail -f e1_training_JOBID.err
# Follow both (interleaved)
tail -f e1_training_JOBID.out e1_training_JOBID.err
# Robust follow if file rotates
tail -F e1_training_JOBID.out
# Pager follow (press Ctrl+C to stop)
less +F e1_training_JOBID.out
```

## Cancel jobs
```bash
scancel JOBID
```

## Chunked runs and dependencies
```bash
# First chunk (2h, one seed)
JID=$(bash scripts/submit_e1_job.sh --account sbagchi --partition a30 --qos standby \
  --time 2:00:00 --seeds "4" --episodes 3000 | awk '/Submitted batch job/{print $4}')

# Next chunk starts after the prior completes successfully
sbatch --dependency=afterok:$JID --account sbagchi --partition a30 --qos standby \
  --time 2:00:00 scripts/run_e1.sh --res 32 --seeds "4" --episodes 3000
```

## GPU checks
```bash
# One-shot summary
nvidia-smi

# Compact free/total per GPU
nvidia-smi --query-gpu=index,name,memory.free,memory.total --format=csv,noheader,nounits

# Watch processes using GPU memory (run on compute node)
watch -n 2 'nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv'
```

## Conda and Python (non-interactive batch)
```bash
# Initialize conda without modules (works in SLURM batch)
CONDA_ROOT=/depot/sbagchi/data/preeti/anaconda3
source "$CONDA_ROOT/etc/profile.d/conda.sh" || eval "$($CONDA_ROOT/bin/conda shell.bash hook)"
conda activate /depot/sbagchi/data/preeti/anaconda3/envs/gpu

# Verify
python -c 'import torch; print("torch", torch.__version__, "cuda?", torch.cuda.is_available())'

# Alternative: call interpreter directly (no activation)
/depot/sbagchi/data/preeti/anaconda3/envs/gpu/bin/python -u training_split.py
```

## Environment variables (memory tuning and RL overrides)
```bash
# PyTorch CUDA allocator tuning
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,garbage_collection_threshold:0.7,max_split_size_mb:128

# RL overrides (examples)
export RL_NUM_EPISODES=3000
export RL_BATCH_SIZE=4
export RL_SCREEN_RES=32
export RL_MINIMAP_RES=32
export RL_TARGET_UPDATE_FREQ=300
```

## Files, disk, and search
```bash
# Disk space and directory sizes
df -h
du -sh . /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced

# Find recent run directories
find /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced -maxdepth 1 -type d -printf "%TY-%Tm-%Td %TT %p\n" | sort -r | head

# Grep logs for errors
grep -R "ERROR" /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/logs | tail -n 50

# CSV quick look
head -n 5 /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv
 tail -n 5 /depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced/e1_results.csv
```

## Git (overwrite local with remote)
```bash
# Backup branch (optional)
git branch backup/local-before-reset

# Overwrite local with remote branch (e.g., double-dqn)
git fetch origin
git reset --hard origin/double-dqn
git clean -fd

# Set pull strategy globally (pick one)
# git config --global pull.rebase false   # merge
# git config --global pull.rebase true    # rebase
# git config --global pull.ff only        # fast-forward only
```

## Tmux (persistent terminal on login/compute nodes)
```bash
# New session
tmux new -s arl
# List sessions
tmux ls
# Attach to session
tmux attach -t arl
# Detach (inside tmux)
Ctrl+b then d
```
