# Findings Log Entry Template

Use this structure when adding a new finding to `Documentation/Findings_Log.md`.

---

```markdown
### FIND-XXX: {Brief Descriptive Title}

- **Date Discovered**: YYYY-MM-DD
- **Source Experiment(s)**: [EXP-XXX](../Experiments/EXP-XXX_name/README.md)
- **Research Path**: PATH-X
- **Publication Potential**: High / Medium / Low
- **Status**: Needs Verification / Verified / Published

**Description**:  
{2-3 sentences describing what was discovered. Be specific and quantitative where possible.}

**Evidence**:
- {Specific statistic or data point}
- {Reference to figure: [Figure X](../Experiments/EXP-XXX_name/results/figures/figX.png)}
- {Statistical significance if applicable: p < 0.05}

**Implications**:  
{Why does this matter? What does it mean for HPC research/operations?}

**Related Findings**: FIND-YYY, FIND-ZZZ (or "None yet")

**Next Steps**:
- [ ] {Verification needed}
- [ ] {Additional analysis}
- [ ] {Include in paper section X}

---
```

## Finding Status Values

| Status | Meaning |
|--------|---------|
| Needs Verification | Initial discovery, requires additional validation |
| Verified | Confirmed through additional experiments or analysis |
| Published | Included in a submitted/published paper |

## Publication Potential Ratings

| Rating | Criteria |
|--------|----------|
| High | Novel, significant, could be a paper's main contribution |
| Medium | Interesting, supports main findings, good for discussion |
| Low | Minor observation, footnote-worthy, or expected result |

## Tips for Good Findings

1. **Be Specific**: "CPU usage is 40% higher" not "CPU usage is higher"
2. **Include Context**: Compare to baselines or prior work
3. **Link Evidence**: Always reference source experiments and figures
4. **Consider Narrative**: Think about how findings combine into a story
