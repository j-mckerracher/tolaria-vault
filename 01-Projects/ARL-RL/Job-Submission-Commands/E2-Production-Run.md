```bash
sbatch --job-name=E2_prod_s4_4k --account=sbagchi --partition=a30 --qos=normal --time=12:00:00 --export=ALL,RL_NUM_EPISODES=4000,RL_BATCH_SIZE=4,RL_SCREEN_RES=32,RL_MINIMAP_RES=32,RL_REPLAY_MEMORY_SIZE=100000,RL_EPS_START=0.90,RL_EPS_END=0.01,RL_EPS_DECAY=100000,RL_LEARNING_RATE=0.00005,RL_TARGET_UPDATE_FREQ=400,RL_STEP_MUL=16,RL_USE_DUELING_DQN=1 scripts/run_e1.sh --res 32 --seeds "4" --episodes 4000 --allow-env
```

```bash
sbatch --job-name=E2_prod_s6_4k --account=sbagchi --partition=a30 --qos=normal --time=12:00:00 --export=ALL,RL_NUM_EPISODES=4000,RL_BATCH_SIZE=4,RL_SCREEN_RES=32,RL_MINIMAP_RES=32,RL_REPLAY_MEMORY_SIZE=100000,RL_EPS_START=0.90,RL_EPS_END=0.01,RL_EPS_DECAY=100000,RL_LEARNING_RATE=0.00005,RL_TARGET_UPDATE_FREQ=400,RL_STEP_MUL=16,RL_USE_DUELING_DQN=1 scripts/run_e1.sh --res 32 --seeds "6" --episodes 4000 --allow-env
```

```bash
sbatch --job-name=E2_prod_s8_4k --account=sbagchi --partition=a30 --qos=normal --time=12:00:00 --export=ALL,RL_NUM_EPISODES=4000,RL_BATCH_SIZE=4,RL_SCREEN_RES=32,RL_MINIMAP_RES=32,RL_REPLAY_MEMORY_SIZE=100000,RL_EPS_START=0.90,RL_EPS_END=0.01,RL_EPS_DECAY=100000,RL_LEARNING_RATE=0.00005,RL_TARGET_UPDATE_FREQ=400,RL_STEP_MUL=16,RL_USE_DUELING_DQN=1 scripts/run_e1.sh --res 32 --seeds "8" --episodes 4000 --allow-env
```

vs. 

Resolution Scaling (64×64) — 500 episode smoke test:
```bash
for seed in 4 6 8; do
  sbatch --account=sbagchi --partition=a30 --qos=standby --gres=gpu:1 \
    --ntasks=1 --cpus-per-task=4 --mem=80G --time=03:00:00 \
    --export=ALL,RL_SEED=$seed,RL_NUM_EPISODES=500,RL_LEARNING_RATE=0.00005,\
RL_EPS_DECAY=100000,RL_BATCH_SIZE=4,RL_REPLAY_MEMORY_SIZE=100000,\
RL_SCREEN_RESOLUTION=64,RL_MINIMAP_RES=64,RL_STEP_MUL=16,\
RL_TARGET_UPDATE_FREQ=400,RL_DUELING_DQN=1 \
    scripts/run_e2.sh
  sleep 2
done
```
