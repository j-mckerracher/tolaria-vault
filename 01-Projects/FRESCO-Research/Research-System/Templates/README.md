# Document Templates

Templates for creating consistent documentation across the research project.

---

## Available Templates

### `experiment_template.md`

**Use for**: Creating new experiments

**Contains**:
- Objective and hypothesis
- FRESCO data specification (clusters, date range, filters)
- Methodology section
- Reproducibility info (environment, code, seeds)
- Supercomputer job details (SLURM/PBS)
- Execution log table
- Results and analysis sections
- Conclusion with hypothesis confirmation

**How to use**:
```bash
# Automated (recommended)
./Research-System/Scripts/create_experiment.sh "Title" "Objective" "PATH-X"

# Manual
cp Research-System/Templates/experiment_template.md Experiments/EXP-XXX_name/README.md
# Then edit to fill in {placeholders}
```

---

### `research_path_template.md`

**Use for**: Creating new research paths/directions

**Contains**:
- Research questions and hypotheses
- Background and motivation
- Literature review section
- Methodology description
- Experiments table
- Decision log (for tracking pivots and rationale)
- Findings summary
- Progress toward publication tracker

**How to use**:
```bash
mkdir -p Planning/PATH-X_name
cp Research-System/Templates/research_path_template.md Planning/PATH-X_name/README.md
# Then edit to fill in {placeholders}
```

---

### `literature_template.md`

**Use for**: Tracking related work for a research path

**Contains**:
- Paper entry structure (citation, summary, relevance)
- Key quotes section
- Use-in-paper checklist
- Papers-to-read queue
- Related work section draft area

**How to use**:
```bash
cp Research-System/Templates/literature_template.md Planning/PATH-X_name/literature.md
# Add papers as you find them
```

---

### `findings_log_template.md`

**Use for**: Reference when adding findings to the Findings Log

**Contains**:
- Finding entry structure
- Status values (Needs Verification, Verified, Published)
- Publication potential ratings (High, Medium, Low)
- Tips for good findings documentation

**How to use**:
- Reference this template when adding entries to `Documentation/Findings_Log.md`
- Copy the markdown structure and fill in details

---

## Template Placeholders

All templates use `{placeholder}` syntax for fields that need to be filled in:

| Placeholder | Example Value |
|-------------|---------------|
| `{experiment_id}` | EXP-001 |
| `{title}` | CPU Usage Analysis |
| `{date_created}` | 2026-01-24 |
| `{status}` | Created |
| `{research_path}` | PATH-A |
| `{objective}` | Analyze CPU patterns... |

---

## For LLM Agents

When using templates:

1. **Copy first**: Never edit the template files directly
2. **Fill all fields**: Replace every `{placeholder}` with real values
3. **Use ISO dates**: Format as YYYY-MM-DD
4. **Use consistent IDs**: Check existing IDs before creating new ones
5. **Link documents**: Use relative paths to connect related docs
