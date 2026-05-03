# LLM Brainstorming Prompt

Copy and paste this into a new LLM conversation to brainstorm research ideas for FRESCO.

---

## System Context

You are helping brainstorm new research directions for the FRESCO dataset—a multi-institutional HPC job dataset with 20.9 million jobs spanning 75 months from Purdue (Anvil, Conte) and TACC (Stampede).

**Dataset Available**: Job attributes (submit/start/end times, resources, exit codes, user info) + performance metrics (CPU, GPU, memory, NFS, block I/O)

**Goal**: Identify novel research questions that could lead to publishable papers in peer-reviewed venues (ASPLOS, USENIX, PEARC, SuperComputing, etc.)

**Constraints**:
- Must be answerable with FRESCO data alone (no external data collection)
- Should produce quantifiable, reproducible findings
- Should advance HPC research or operations knowledge
- Feasible to execute on supercomputers (Purdue/TACC access)

---

## Brainstorming Instructions

I want to brainstorm research ideas for the FRESCO dataset. Please help me:

### 1. Understand the Opportunity Space

First, help me think about what research areas could benefit from FRESCO:

- **System Dependability**: What can we learn about failures, resource contention, or system health?
- **Workload Characterization**: What patterns exist in job submissions, resource usage, or user behavior?
- **Performance Prediction**: Can we predict job completion time, resource usage, or failures?
- **Resource Optimization**: How can we improve scheduling, allocation, or utilization?
- **Cross-Institutional Insights**: What differences/similarities exist between Anvil, Conte, and Stampede?
- **User Behavior**: How do different user communities use the systems? What patterns exist?
- **Temporal Trends**: How has HPC workload evolved over 75 months? Seasonal patterns?

### 2. Generate Specific Research Questions

For each area above, generate 3-5 specific, testable research questions that:
- Are concrete (answerable with data analysis)
- Are non-obvious (require FRESCO to discover)
- Have potential impact (useful for operations or research)

**Format each as**:
> RQ-X: [Specific question]?
> **Hypothesis**: [What we expect to find]
> **Why it matters**: [Impact/relevance]
> **Dataset requirements**: [Clusters, metrics, timeframe]

### 3. Evaluate Ideas

For each research question, help me assess:
- **Novelty**: Is this unexplored in HPC literature?
- **Feasibility**: Can we answer this with FRESCO?
- **Publication Potential**: Which venue might accept this?
- **Complexity**: Simple analysis or requires ML/advanced methods?

### 4. Synthesis

Help me identify:
- **Quick wins**: Research that's simple + publishable (1-2 week experiments)
- **Deep dives**: Complex research paths (3+ month projects)
- **Combinations**: How multiple ideas might combine into one strong paper
- **Gaps**: What questions are NOT answerable with FRESCO

### 5. Next Steps

For the top 3-5 ideas, provide:
- Concrete first experiment to validate the idea
- Required FRESCO query (date range, clusters, metrics)
- Expected deliverables (figures, statistics)

---

## Output Format

Please structure your response as:

```
## Research Area: [Area Name]

### RQ-1: [Question]
- **Hypothesis**: [Expected finding]
- **Why it matters**: [Relevance]
- **Dataset needed**: [Specifics]
- **Feasibility**: High/Medium/Low
- **Publication venue**: [Conference/Journal]
- **First experiment**: [What to try first]

### RQ-2: [Question]
...
```

---

## My Context (Optional - Fill In)

To help tailor suggestions, tell me about:
- **My expertise**: I'm a software engineer with a B.S. in C.S. But I'd like to explore creating an ML model.
- **Time available**: This can be a long term thing.
- **Focus areas**: I want to use the FRESCO data to extract insights. 
- **Existing work**: See the papers in the Reference folder
- **Target venue**: None

---

## Let's Begin

Please generate research questions and ideas. Start with the "Opportunity Space" categories and generate specific questions for each.
