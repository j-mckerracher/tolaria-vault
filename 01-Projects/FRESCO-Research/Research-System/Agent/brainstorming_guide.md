# Brainstorming Guide

How to use LLMs to systematically brainstorm research ideas for FRESCO.

---

## Overview

This guide helps you leverage LLMs to discover novel research directions that are:
- ✅ Answerable with FRESCO data
- ✅ Novel and publishable
- ✅ Feasible to execute
- ✅ Impactful for HPC research

---

## Quick Start

### Step 1: Prepare the Prompt

Copy the full contents of [`brainstorming_prompt.md`](brainstorming_prompt.md)

### Step 2: Start an LLM Conversation

Open your preferred LLM:
- ChatGPT, Claude, Gemini, Copilot, etc.
- Or use `copilot` CLI locally

### Step 3: Paste the Prompt

Paste the brainstorming prompt as your first message.

### Step 4: Provide Context (Optional)

Tell the LLM about your background, time available, and interests:

> I'm a systems researcher with experience in ML. I have 1-2 months for this project. 
> I'm most interested in failure analysis and performance prediction.

### Step 5: Review and Evaluate

The LLM will generate research questions. Evaluate each one:

| Criterion | Good Sign | Red Flag |
|-----------|-----------|----------|
| **Novelty** | "Not found in HPC literature" | "Standard approach" |
| **Feasibility** | "Answerable with FRESCO" | "Requires external data" |
| **Impact** | "Helps operations/research" | "Interesting but academic" |
| **Scope** | "1-2 week experiment" | "6-month project" |

### Step 6: Drill Deeper

Ask follow-up questions on promising ideas:

> "For RQ-3, can you help me design the first experiment? 
> What FRESCO query would I use? What would the results look like?"

### Step 7: Document Results

Copy promising ideas into [`brainstorming_session_template.md`](brainstorming_session_template.md)

### Step 8: Take Action

Create a research path for your top idea:
```bash
mkdir -p Planning/PATH-X_[name]
cp Templates/research_path_template.md Planning/PATH-X_[name]/README.md
```

---

## Example Brainstorming Session

**Your prompt**:
> "Brainstorm research ideas for FRESCO. I'm interested in workload characterization."

**LLM might generate**:
```
## Research Area: Workload Characterization

### RQ-1: How do job submission patterns differ across institutions?
- Hypothesis: User communities are distinct (Purdue vs TACC)
- Why it matters: Helps design institution-specific scheduling
- First experiment: Compare job inter-arrival times by institution
- Feasibility: High (simple statistical analysis)
- Publication: PEARC or ASPLOS

### RQ-2: Are there seasonal patterns in HPC workloads?
- Hypothesis: Academic calendar drives workload spikes
- Why it matters: Helps predict resource demand
- First experiment: Time-series analysis of job submissions
- Feasibility: High (75-month data available)
- Publication: ASPLOS or SC conference
```

**Your follow-up**:
> "I like RQ-2. What would the first experiment look like?"

**LLM provides details**:
```
## First Experiment for RQ-2

Query FRESCO for:
- Time range: Full 75 months
- Metric: Job submission count per day
- Group by: Month and year

Expected deliverables:
- Time series plot with seasonal patterns
- Statistical test: ACF analysis for periodicity
- Observation: "Academic calendar correlates with workload"

Timeline: 1 week (mostly waiting for analysis to run)
```

**You create the research path**:
```
mkdir -p Planning/PATH-A_seasonal_workload
cp Templates/research_path_template.md Planning/PATH-A_seasonal_workload/README.md
# Fill in hypothesis, methodology, first experiments
```

---

## Tips for Better Brainstorming

### 1. **Be Specific About Constraints**
Instead of: "Brainstorm ideas"  
Say: "Brainstorm ideas I can complete in 2 weeks on a system with 128 cores"

### 2. **Reference the Dataset**
Remind the LLM what's available:
> "Remember: 20.9M jobs, CPU/GPU/memory/I/O metrics, 3 clusters, 75 months"

### 3. **Ask for Evaluation**
> "Which of these ideas is most novel? Which is most feasible?"

### 4. **Drill into Promising Ideas**
Don't stop at the research question. Ask:
- What would the experiment look like?
- What would results look like?
- How would we validate/verify findings?

### 5. **Challenge the LLM**
> "Is this really novel? Show me similar work in HPC literature."

### 6. **Think About Combinations**
Ask the LLM:
> "Could ideas RQ-2 and RQ-5 combine into one stronger paper?"

---

## Common Brainstorming Pitfalls

| Pitfall | How to Avoid |
|---------|--------------|
| Ideas are too vague | Ask for specific research questions |
| Ideas require external data | Remind LLM: "FRESCO data only" |
| Ideas are not novel | Ask: "What's new here?" |
| Ideas are too complex | Ask: "What's a 1-week version?" |
| No actionable first steps | Ask: "What experiment validates this?" |

---

## From Brainstorm to Research

Once you have promising ideas:

1. **Create Research Path**: `Planning/PATH-X_name/README.md`
2. **Literature Review**: `Planning/PATH-X_name/literature.md`
3. **Design Experiments**: List in research path
4. **Run First Experiment**: `Experiments/EXP-001/`
5. **Track Findings**: `Documentation/Findings_Log.md`
6. **Toward Publication**: Research path has "Progress Toward Publication" section

---

## File References

| File | Purpose |
|------|---------|
| `brainstorming_prompt.md` | Main prompt to copy to LLM |
| `brainstorming_session_template.md` | Template to record results |
| `research_path_template.md` | Create path for validated idea |
| `experiment_template.md` | Design first experiment |

---

## Next Steps

1. Copy `brainstorming_prompt.md`
2. Start an LLM conversation
3. Generate ideas
4. Pick top 3
5. Create research path for your favorite
6. Design first experiment
7. Submit to supercomputer
