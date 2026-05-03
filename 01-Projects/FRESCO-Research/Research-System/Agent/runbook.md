# FRESCO Research System - LLM Runbook

This document contains step-by-step procedures for all common research tasks. Follow these procedures exactly to maintain consistency across the research system.

---

## Table of Contents

1. [Creating a New Research Path](#1-creating-a-new-research-path)
2. [Creating a New Experiment](#2-creating-a-new-experiment)
3. [Updating Experiment Status](#3-updating-experiment-status)
4. [Submitting a Job to Supercomputer](#4-submitting-a-job-to-supercomputer)
5. [Recording Results](#5-recording-results)
6. [Logging a Finding](#6-logging-a-finding)
7. [Adding Literature](#7-adding-literature)
8. [Session Start Procedure](#8-session-start-procedure)
9. [Session End Procedure](#9-session-end-procedure)

---

## 1. Creating a New Research Path

**When to use**: Starting a new line of investigation (e.g., anomaly detection, performance prediction)

### Procedure

1. **Determine Path ID**: Check `Documentation/Research_Plan.md` for existing paths. Use next letter (PATH-A, PATH-B, etc.)

2. **Create Path Document**:
   ```bash
   # Create directory
   mkdir -p Planning/PATH-X_descriptive_name
   
   # Copy template
   cp Research-System/Templates/research_path_template.md Planning/PATH-X_descriptive_name/README.md
   ```

3. **Fill Out Template**: Edit the README.md with:
   - Research questions (specific, testable)
   - Hypothesis (falsifiable prediction)
   - Methodology (how you'll test the hypothesis)
   - Initial literature review
   - First planned experimentsq

4. **Update Research Plan**: Add the new path to `Documentation/Research_Plan.md`:
   ```markdown
   ### Path X: [Title]
   *Objective: [One-sentence goal]*
   *Document: [Planning/PATH-X_name/README.md](../Planning/PATH-X_name/README.md)*
   - [ ] EXP-XXX: First experiment
   ```

5. **Create Literature File**:
   ```bash
   cp Research-System/Templates/literature_template.md Planning/PATH-X_name/literature.md
   ```

---

## 2. Creating a New Experiment

**When to use**: Defining a specific experiment within a research path

### Procedure

1. **Determine Experiment ID**: Check `Documentation/Master_Index.md` for last ID. Use next number (EXP-001, EXP-002, etc.)

2. **Create Experiment**:
   ```bash
   ./Research-System/Scripts/create_experiment.sh "Experiment Title" "Objective statement" "PATH-X"
   ```
   
   Or manually:
   ```bash
   # Create directory
   mkdir -p Experiments/EXP-XXX_descriptive_name
   
   # Copy template
   cp Research-System/Templates/experiment_template.md Experiments/EXP-XXX_descriptive_name/README.md
   ```

3. **Fill Out Template**: Edit README.md with:
   - Clear objective (what question does this answer?)
   - Hypothesis (what do you expect to find?)
   - FRESCO data specification:
     - Date range
     - Clusters (Anvil/Conte/Stampede)
     - Filters applied
     - Columns used
   - Methodology (analysis approach)
   - Environment details (Python version, packages)

4. **Update Master Index**: Add row to `Documentation/Master_Index.md`:
   ```markdown
   | EXP-XXX | Title | Created | PATH-X | YYYY-MM-DD | YYYY-MM-DD |
   ```

5. **Update Research Plan**: Add checkbox to appropriate path in `Documentation/Research_Plan.md`

---

## 3. Updating Experiment Status

**When to use**: When experiment status changes (submission, completion, failure)

### Status Values

| Status | When to Use |
|--------|-------------|
| Created | Just defined, not submitted |
| Queued | Submitted to cluster, waiting in queue |
| Running | Actively executing on cluster |
| Completed | Finished successfully |
| Failed | Job failed (document why) |
| Analysis | Results being analyzed |
| Published | Included in a publication |

### Procedure

1. **Update via Script**:
   ```bash
   ./Research-System/Scripts/update_status.sh EXP-XXX "Running"
   ```

2. **Or Manually Update** in `Experiments/EXP-XXX_name/README.md`:
   ```markdown
   **Status**: Running
   ```

3. **Update Master Index**: Change status in `Documentation/Master_Index.md`

4. **Add Execution Log Entry**: In the experiment's README.md:
   ```markdown
   | YYYY-MM-DD HH:MM | Status changed to Running | Job ID: 123456 |
   ```

---

## 4. Submitting a Job to Supercomputer

**When to use**: Submitting an experiment to run on Purdue or TACC clusters

### Procedure

1. **Prepare Job Script**: Create SLURM/PBS script in experiment directory:
   ```bash
   Experiments/EXP-XXX_name/job.slurm  # or job.pbs
   ```

2. **Record Environment**: In experiment README, document:
   - Cluster name (Anvil, Negishi, etc.)
   - Python/module versions
   - Key package versions
   - Git commit hash: `git rev-parse HEAD`

3. **Submit Job**:
   - **Gilbreth (preferred for FRESCO runs)**: submit via `sbbest`.
   - Other clusters: use the repository submission script.

   ```bash
   # Gilbreth (recommended)
   ssh jmckerra@gilbreth.rcac.purdue.edu "source ~/.bashrc && cd ~/Experiments/EXP-XXX && sbbest scripts/expXXX.slurm"
   
   # Sleep 10 minutes, then only continue if COMPLETED (else stop)
   Start-Sleep -Seconds 600
   ssh jmckerra@gilbreth.rcac.purdue.edu "sacct -j <JOBID> --format=JobID,State%20,Elapsed --noheader"

   # Other clusters (SLURM)
   ./Research-System/Scripts/submit_job.sh EXP-XXX job.slurm slurm

   # PBS
   ./Research-System/Scripts/submit_job.sh EXP-XXX job.pbs pbs
   ```

4. **Record Job ID**: Script will log this, but verify in README:
   ```markdown
   ## Supercomputer Job
   - **Cluster**: Anvil
   - **Scheduler**: SLURM
   - **Job ID**: 12345678
   - **Submitted**: 2026-01-24 15:30:00
   ```

5. **Update Status**: Set to "Queued"

---

## 5. Recording Results

**When to use**: After an experiment completes (success or failure)

### For Successful Completion

1. **Update Status** to "Analysis"

2. **Download Results**: Copy output files to experiment directory:
   ```
   Experiments/EXP-XXX_name/
   ├── results/
   │   ├── output.csv
   │   ├── metrics.json
   │   └── figures/
   │       ├── fig1.png
   │       └── fig2.png
   └── logs/
       └── job.log
   ```

3. **Fill Results Section** in README:
   ```markdown
   ## Results & Analysis
   
   ### Summary Statistics
   - Metric 1: value (95% CI: [low, high])
   - Metric 2: value (p < 0.05)
   
   ### Key Observations
   1. Observation with evidence
   2. Another observation
   
   ### Figures
   ![Description](results/figures/fig1.png)
   ```

4. **Document Conclusions**:
   ```markdown
   ## Conclusion
   - [x] Hypothesis Confirmed (or [ ] Hypothesis Rejected)
   - Key takeaway: [One sentence]
   - Next Steps:
     - [ ] Follow-up experiment EXP-XXX
     - [ ] Log finding to Findings Log
   ```

5. **Log Significant Findings**: See [Logging a Finding](#6-logging-a-finding)

### For Failed Jobs

1. **Update Status** to "Failed"

2. **Document Failure** in README:
   ```markdown
   ## Failure Analysis
   - **Error Type**: OOM / Timeout / Code Error / Data Issue
   - **Error Message**: [paste relevant error]
   - **Root Cause**: [your analysis]
   - **Resolution**: [what to try next]
   ```

3. **Log Execution Entry**:
   ```markdown
   | YYYY-MM-DD HH:MM | Failed | OOM error after 2 hours |
   ```

---

## 6. Logging a Finding

**When to use**: When you discover something significant that could contribute to a publication

### Procedure

1. **Determine Finding ID**: Check `Documentation/Findings_Log.md` for last ID

2. **Add Entry** to Findings Log:
   ```markdown
   ### FIND-XXX: [Brief Title]
   
   - **Date Discovered**: YYYY-MM-DD
   - **Source Experiment(s)**: EXP-XXX, EXP-YYY
   - **Research Path**: PATH-X
   - **Publication Potential**: High / Medium / Low
   - **Status**: Needs Verification / Confirmed / Published
   
   **Description**: 
   [2-3 sentences describing the finding]
   
   **Evidence**:
   - [Specific data point or statistic]
   - [Link to figure or table]
   
   **Related Findings**: FIND-YYY, FIND-ZZZ
   
   **Notes**:
   [Additional context or next steps]
   ```

3. **Cross-Reference**: Add link to finding in source experiment's README:
   ```markdown
   ## Related Findings
   - [FIND-XXX: Title](../../Documentation/Findings_Log.md#find-xxx-title)
   ```

---

## 7. Adding Literature

**When to use**: When you find a paper relevant to a research path

### Procedure

1. **Open Literature File**: `Planning/PATH-X_name/literature.md`

2. **Add Entry**:
   ```markdown
   ### [Author et al., Year] Short Title
   
   **Full Citation**: 
   Author, A., Author, B. (Year). Full Title. Journal/Conference. DOI/URL
   
   **Summary**:
   [2-3 sentences summarizing the paper]
   
   **Relevance to This Path**:
   [How this paper relates to your research]
   
   **Key Quotes/Ideas**:
   - "[Quote]" (p. X)
   - Key finding or method
   
   **Use in Paper**:
   - [ ] Related Work section
   - [ ] Methodology justification
   - [ ] Results comparison
   ```

3. **Add to Reference Folder** (optional): If PDF available:
   ```bash
   cp paper.pdf Reference/author_year_short_title.pdf
   ```

---

## 8. Session Start Procedure

**When to use**: At the beginning of every LLM session

### Checklist

1. **Read Master Index**:
   ```
   View: Documentation/Master_Index.md
   ```
   Note any experiments with status "Running" or "Queued"

2. **Check Research Plan**:
   ```
   View: Documentation/Research_Plan.md
   ```
   Understand active research paths

3. **Review Pending Work**:
   - Any experiments awaiting analysis?
   - Any findings needing verification?

4. **Ask User**:
   > "I've reviewed the current state. What would you like to accomplish this session?"
   
   Or if there's pending work:
   > "I see EXP-XXX is marked as Completed but needs analysis. Should I analyze those results, or do you have a different priority?"

---

## 9. Session End Procedure

**When to use**: At the end of every LLM session

### Checklist

1. **Update All Statuses**: Ensure any changed experiments have correct status

2. **Log Execution Entries**: Add entries for any actions taken today

3. **Update Last Modified Dates**: On all documents edited

4. **Summarize Session**: Provide user with:
   - What was accomplished
   - Current state of active experiments
   - Recommended next steps

5. **Commit Changes** (if user has git):
   ```bash
   git add -A
   git commit -m "Research session: [brief summary]"
   ```

---

## Appendix: Template Locations

| Template | Path | Use For |
|----------|------|---------|
| Experiment | `Research-System/Templates/experiment_template.md` | New experiments |
| Research Path | `Research-System/Templates/research_path_template.md` | New research paths |
| Literature | `Research-System/Templates/literature_template.md` | New literature files |
| Findings Entry | See Section 6 | New findings |
