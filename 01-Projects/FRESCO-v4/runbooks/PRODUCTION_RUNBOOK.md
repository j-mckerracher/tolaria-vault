# FRESCO v4 Experiment Runbook

**Dataset**: v4 uses the authoritative chunks-v3 dataset. No new production pipeline. See FRESCO-v3/runbooks/PRODUCTION_RUNBOOK.md for dataset production details.

**Data location**: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/`
**Manifest**: `/depot/sbagchi/data/josh/FRESCO/chunks-v3/manifests/output_manifest.jsonl`

## Pre-flight checklist (before any experiment)
1. Data accessible on Gilbreth at the above path
2. Conda env active (fresco_v2 or equivalent with sklearn, pandas, pyarrow, numpy)
3. Pipeline code pinned to git commit (run `git rev-parse HEAD` and `git status`)
4. Config file created and reviewed
5. Experiment folder created with standard subfolders: config/, logs/, results/, manifests/, validation/

## Running a few-shot experiment
1. Create experiment config (see docs/CONFIGURATION.md)
2. Create experiment folder: `experiments/EXP-XXX_<description>/`
3. Submit to Gilbreth with an explicit validated partition (do **not** use `sbbest` or generic `gpu` partition names):
   ```bash
   #SBATCH --partition=a100-80gb
   #SBATCH --qos=normal
   #SBATCH --account=sbagchi
   #SBATCH --gres=gpu:1
   #SBATCH --cpus-per-task=8
   #SBATCH --mem=48G
   python scripts/few_shot_transfer.py --config experiments/EXP-XXX/config/expXXX.json
   ```
   Current validated default for `sbagchi`: `--partition=a100-80gb --qos=normal`. If an accepted job remains pending with `AssocGrpGRES`, that indicates temporary group GPU quota saturation rather than a broken config. Do not switch to `gpu`, `a10`, `a30`, `a100-40gb`, or `h100`; those are not valid submission targets for this account.
4. Wait 10 minutes, check status with `sacct -j <JOBID> --format=JobID,State,Elapsed,ExitCode -X`
5. If not completed, stop and wait for user signal

## Running the full sweep
1. Create sweep config (see docs/CONFIGURATION.md)
2. Run: `python scripts/few_shot_sweep.py --config config/sweep_config.json`
3. This generates individual configs and (optionally) a SLURM array script
4. Submit the array job or individual jobs

## Post-run verification
1. Check results/metrics.json exists and contains valid R² values
2. Check predictions parquet files exist
3. Check manifests/ and validation/ populated
4. Update experiment run log

## SLURM constraints
- Account: sbagchi, User: jmckerra
- Validated default: `--partition=a100-80gb --qos=normal` (accepted repair job `10410106` confirms the config is live)
- Pending reason `AssocGrpGRES` means the shared A100-80GB quota is temporarily saturated, not that the partition/QoS settings are invalid
- Do not use `sbbest` or generic `gpu` partition aliases for this account; pin the partition explicitly to `a100-80gb`
- Previous `training` / `qos=training` attempts should not be treated as the normal fallback for this account unless re-verified
- Monitor: squeue -u $USER, sacct -j <JOBID>
- After submission, wait 10 minutes then check; if not done, stop and wait
