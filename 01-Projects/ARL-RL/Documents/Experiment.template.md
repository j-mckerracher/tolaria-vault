---
title: "{{title}}"
experiment_id: "expt-{{YYYYMMDD}}-{{slug}}"
date: "{{YYYY-MM-DD}}"
last_updated: "{{ISO 8601 timestamp}}"
status: "planned|running|completed|abandoned"
tags: ["project/arl-rl", "experiment"]
dataset: "{{name/version}}"
algorithm: "{{name/version}}"
params:
  {{key}}: {{value}}
seeds: [{{int}}]
code_ref:
  repo: "{{url-or-path}}"
  commit: "{{hash}}"
  entrypoint: "{{path or command}}"
artifacts: "{{relative/path}}"
job_ids: ["{{scheduler-id}}"]
metrics:
  primary: { name: "{{metric}}", value: {{number}}, step: {{int}} }
  others:
    {{metric}}: {{value}}
hardware: { gpu: {{int}}, cpu: {{int}}, ram_gb: {{int}} }
sources: ["{{links or files}}"]
related: ["[[...]]"]
---
## Summary
## Goal
## Setup (Hardware/Software)
## Procedure
## Results
## Analysis
## Issues
## Next Steps
## Jobs
- [[01 Projects/ARL RL/Job-Submission-Commands/{{YYYY-MM-DD}}-expt-{{YYYYMMDD}}-{{slug}}.md]] — status: {{submitted|running|succeeded|failed}}
## Artifacts
## Links
## Changelog
- {{ISO}} Created from template
