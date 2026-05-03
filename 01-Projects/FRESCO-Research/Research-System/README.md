# Research System

Infrastructure for systematic LLM-assisted research on the FRESCO dataset.

---

## Folders

| Folder | Purpose | Key Files |
|--------|---------|-----------|
| `Agent/` | LLM prompts and procedures | `system_prompt.md`, `runbook.md` |
| `Scripts/` | Bash automation scripts | `create_experiment.sh`, `update_status.sh`, `submit_job.sh` |
| `Templates/` | Document templates | `experiment_template.md`, `research_path_template.md`, etc. |
| `Controller/` | Python CLI (legacy) | `manage_research.py` |
| `Registry/` | Reserved for future use | - |

---

## Quick Reference

### Start an LLM Session
Copy `Agent/system_prompt.md` to your LLM conversation.

### Create an Experiment
```bash
./Scripts/create_experiment.sh "Title" "Objective" "PATH-X"
```

### Update Status
```bash
./Scripts/update_status.sh EXP-001 "Running"
```

### Submit Job
```bash
./Scripts/submit_job.sh EXP-001 job.slurm slurm
```

---

## See Also

- `Agent/README.md` - How to use LLM prompts
- `Scripts/README.md` - Script documentation
- `Templates/README.md` - Template usage guide
- `../README.md` - Project overview
