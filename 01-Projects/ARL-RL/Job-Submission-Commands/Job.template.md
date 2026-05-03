---
title: "Jobs for expt-{{YYYYMMDD}}-{{slug}} — {{short}}"
date: "{{ISO}}"
last_updated: "{{ISO}}"
tags: ["project/arl-rl", "job"]
experiment: "[[01 Projects/ARL RL/Documents/Experiments/expt-{{YYYYMMDD}}-{{slug}}.md]]"
scheduler: "slurm|pbs|<other>"
cluster: "{{name}}"
resources: { nodes: {{int}}, gpus: {{int}}, cpus: {{int}}, mem_gb: {{int}}, time: "{{hh:mm:ss}}", partition: "{{name}}" }
env_setup:
  modules: ["{{module}}"]
  conda_env: "{{name}}"
  container: "{{image:tag}}"
workdir: "{{relative/path}}"
stdout_path: "{{relative/path}}"
stderr_path: "{{relative/path}}"
job_ids: ["{{id}}"]
status: "submitted|running|succeeded|failed|canceled|mixed"
---
## Commands
- Exact submission command(s): {{copy-paste exact}}
- Arrays/dependencies: {{details}}
## Notes
## Outputs & Logs
## Changelog
- {{ISO}} Added commands and job IDs
