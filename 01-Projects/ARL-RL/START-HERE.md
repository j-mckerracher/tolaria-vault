# ARL-RL Project — Start Here

> This document provides your roadmap to the ARL-RL project documentation.

---

## 📂 Documentation Structure

### Core Status Documents
These are the most frequently updated files that track current state:

- **[[01-Projects/ARL-RL/README]]** — Current status, next actions, recent context (AI agent entry point)
- **[[Status]]** — Detailed current status, stage progression, next actions
- **[[Plan]]** — Roadmap, milestones, tasks, risks
- **[[Experiments]]** — Canonical experiment tracker (all runs with results)
- **[[RESULTS_SUMMARY]]** — Executive summary for research reporting

### Quick Reference
- **[[Dont-Forget]]** — Critical reminders, preferred commands, common patterns
- **[[01-Projects/Demo-AGILE3D/Backlog]]** — Future work items not yet prioritized

### Detailed Documentation Folders

#### 📁 Documents/
Technical guides, how-tos, and experiment details:
- **[[Documents/Index]]** — Full index of all documents
- SLURM guides, common commands, engineering notes
- **Documents/Experiments/** — Detailed experiment notes (one per experiment run)

#### 📁 Decisions/
Key architectural and methodological choices:
- **[[Decisions/Index]]** — Index of all decision records
- Each decision documented with: context, options, choice, rationale

#### 📁 Work-Log/
Chronological work history (day-by-day):
- **[[Work-Log/Index]]** — Index of all work log entries
- Organized by month (e.g., Work-Log/2025-10/)

#### 📁 Work-Completed/
Daily completion logs (what was finished each day):
- **[[Work-Completed/Index]]** — Index of completed work
- Organized by month (e.g., Work-Completed/2025-10/)

#### 📁 Job-Submission-Commands/
SLURM job submission records:
- Exact commands used for each experiment
- Job IDs, resource allocations, timestamps

#### 📁 Scripts-Reference/
Reference documentation for scripts:
- **[[Scripts-Reference/README]]** — Scripts overview
- Script usage, parameters, examples

#### 📁 Run-Logs/
Raw output logs from experiment runs:
- **[[Run-Logs/Index]]** — Index of all run logs
- Stdout/stderr from SLURM jobs

#### 📁 Notes/
Technical notes, insights, observations:
- **[[Notes/Index]]** — Index of all notes
- Engineering notes, mixed precision guidance, etc.

#### 📁 References/
External references and collaboration guides:
- **[[References/Index]]** — Index of references
- **[[References/LLM-Collaboration-Guide]]** — Guide for AI agent collaboration

#### 📁 Context/
Project context and background information:
- **[[Context/Index]]** — Index of context documents

#### 📁 Templates/
Document templates for consistency:
- Experiments.template.md
- Plan.template.md
- Status.template.md

#### 📁 Archive/
Historical documents no longer actively used:
- Old restructuring summaries
- Completed tasks
- Legacy documentation

---

## 🔄 Typical Workflow

### Intro
1. Read **[[01-Projects/ARL-RL/README]]** — Get current status and context
2. Review **[[RESULTS_SUMMARY]]** — Understand key findings
3. Check **[[Status]]** — See detailed current state
4. Review **[[Plan]]** — Understand roadmap and milestones
5. Browse **[[Experiments]]** — See all experiment history

### For Continuing Work
1. Update **[[Status]]** after significant progress
2. Update **[[Plan]]** when milestones change
3. Update **[[Experiments]]** when runs complete
4. Add to **[[Work-Completed/Index]]** at end of session
5. Update **[[01-Projects/ARL-RL/README]]** recent context section

---

## 🔗 External Resources

- **Code: `/home/jmckerra/Code/ARL-RL` (on Gilbreth HPC cluster)
- **Results Path**: `/depot/sbagchi/data/josh/RL/FindAndDefeatZerglings/results_split_advanced`
- **HPC Cluster**: Gilbreth (Purdue)
- **Account**: `sbagchi`
- **Partition**: `a30` (GPU partition)

---

## 📋 File Naming Conventions

All files and folders use hyphens instead of spaces:
- ✅ `Dont-Forget.md`
- ✅ `Work-Completed/`
- ❌ ~~`Don't Forget.md`~~
- ❌ ~~`Work Completed/`~~

Experiment files follow the pattern:
- `expt-YYYYMMDD-{stage}-{type}.md`
- Example: `expt-20251025-e2-prod-3k.md`

---

*This guide maintained as the navigation hub for all ARL-RL documentation. Last updated: 2025-12-04*
