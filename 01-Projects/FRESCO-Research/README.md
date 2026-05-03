# FRESCO Research System

A systematic framework for conducting LLM-assisted research on the FRESCO dataset, designed to support publication-quality documentation and reproducibility.

---

## Quick Start

### Starting a New LLM Session

1. Copy the contents of [`Research-System/Agent/system_prompt.md`](Research-System/Agent/system_prompt.md) into your LLM conversation
2. The LLM will read the current state from `Documentation/Master_Index.md`
3. Tell the LLM what you want to accomplish

### Directory Structure

```
FRESCO-Research/
├── Documentation/           # Central tracking documents
│   ├── Master_Index.md      # All experiments overview
│   ├── Research_Plan.md     # Active research paths
│   └── Findings_Log.md      # Centralized discoveries
│
├── Experiments/             # Individual experiment folders
│   └── EXP-XXX_name/        # Each experiment gets a folder
│       ├── README.md        # Experiment documentation
│       ├── scripts/         # Job scripts
│       ├── results/         # Output data and figures
│       └── logs/            # Job logs
│
├── Planning/                # Research path documentation
│   └── PATH-X_name/         # Each path gets a folder
│       ├── README.md        # Path documentation
│       └── literature.md    # Related work
│
├── Reference/               # FRESCO papers and references
│
├── Research-System/         # System infrastructure
│   ├── Agent/               # LLM prompts and procedures
│   ├── Scripts/             # Automation scripts
│   ├── Templates/           # Document templates
│   ├── Controller/          # Python CLI (legacy)
│   └── Registry/            # (reserved for future use)
│
└── Logs/                    # Session logs (optional)
```

---

## Core Workflows

### Creating a New Research Path

```bash
# 1. Create the path folder
mkdir -p Planning/PATH-X_descriptive_name

# 2. Copy templates
cp Research-System/Templates/research_path_template.md Planning/PATH-X_descriptive_name/README.md
cp Research-System/Templates/literature_template.md Planning/PATH-X_descriptive_name/literature.md

# 3. Edit README.md with hypothesis, methodology, etc.
# 4. Add path to Documentation/Research_Plan.md
```

### Creating a New Experiment

```bash
# Using the script (recommended)
./Research-System/Scripts/create_experiment.sh "Title" "Objective" "PATH-X"

# Or manually copy template to Experiments/EXP-XXX_name/README.md
```

### Updating Experiment Status

```bash
./Research-System/Scripts/update_status.sh EXP-001 "Running"
```

Valid statuses: `Created`, `Queued`, `Running`, `Completed`, `Failed`, `Analysis`, `Published`

### Submitting a Job

```bash
# For SLURM clusters (Anvil, etc.)
./Research-System/Scripts/submit_job.sh EXP-001 job.slurm slurm

# For PBS clusters
./Research-System/Scripts/submit_job.sh EXP-001 job.pbs pbs
```

---

## Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| **System Prompt** | `Research-System/Agent/system_prompt.md` | Copy to start LLM sessions |
| **Runbook** | `Research-System/Agent/runbook.md` | Step-by-step procedures |
| **Master Index** | `Documentation/Master_Index.md` | Track all experiments |
| **Research Plan** | `Documentation/Research_Plan.md` | Active research paths |
| **Findings Log** | `Documentation/Findings_Log.md` | Record discoveries |

---

## For LLM Agents

If you're an LLM reading this:

1. **First**: Read `Documentation/Master_Index.md` to understand current state
2. **Reference**: Use `Research-System/Agent/runbook.md` for procedures
3. **Templates**: All templates are in `Research-System/Templates/`
4. **Scripts**: Automation scripts are in `Research-System/Scripts/`
5. **Standards**: Follow formatting rules in the system prompt

---

## About FRESCO

FRESCO is a public multi-institutional dataset containing 20.9 million jobs spanning 75 months from three supercomputing clusters (Purdue's Anvil and Conte, TACC's Stampede). It captures performance metrics (CPU, GPU, memory, NFS, block I/O) alongside job attributes.

- **Website**: https://www.frescodata.xyz
- **Reference Papers**: See `Reference/` folder
