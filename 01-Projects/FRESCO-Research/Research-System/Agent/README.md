# LLM Agent Resources

This folder contains resources for LLM agents working on the FRESCO research project.

---

## Files

### `system_prompt.md`

**Purpose**: Context and instructions to copy at the start of each new LLM session.

**How to Use**:
1. Open a new conversation with your LLM (ChatGPT, Claude, Gemini, etc.)
2. Copy the entire contents of `system_prompt.md`
3. Paste it as your first message (or as system instructions if supported)
4. The LLM will now understand the research system and follow its conventions

**When to Use**: Every new LLM session. The prompt provides:
- Background on FRESCO dataset
- Research goals and context
- Documentation standards
- File locations
- Formatting rules

---

### `runbook.md`

**Purpose**: Step-by-step procedures for all common research tasks.

**How to Use**:
1. Reference specific sections when performing tasks
2. Follow procedures exactly to maintain consistency
3. LLMs can read this file to understand how to perform operations

**Contains Procedures For**:
- Creating new research paths
- Creating new experiments
- Updating experiment status
- Submitting supercomputer jobs
- Recording results
- Logging findings
- Adding literature
- Session start/end checklists

---

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│                    NEW LLM SESSION                       │
├─────────────────────────────────────────────────────────┤
│  1. Paste system_prompt.md contents                      │
│  2. LLM reads Master_Index.md                           │
│  3. LLM asks what you want to accomplish                │
│  4. LLM follows runbook.md procedures                   │
│  5. LLM updates documents per system prompt standards   │
└─────────────────────────────────────────────────────────┘
```

---

## Tips

- **Consistency**: Always use the same system prompt for consistent behavior
- **Context**: If the conversation gets long, remind the LLM to check runbook.md
- **Updates**: If you modify the system, update these files so LLMs stay current
- **Debugging**: If an LLM does something wrong, point it to the relevant runbook section
