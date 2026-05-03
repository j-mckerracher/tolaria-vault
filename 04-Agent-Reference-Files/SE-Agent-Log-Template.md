---
tags: [agent/se, log, work-log]
unit_id: "<UNIT_ID>"
project: "[[01-Projects/<Project-Name>]]"
assignment_note: "[[03-Agent-Prompts/Work-Assigner/<Assignment-Note>]]"
date: "<YYYY-MM-DD>"
status: "in-progress"  # in-progress | blocked | done
owner: "[[Josh]]"
---

# SE Work Log — <UNIT_ID>

- Project: [[01-Projects/<Project-Name>]]
- Assignment: [[03-Agent-Prompts/Work-Assigner/<Assignment-Note>]]
- Daily note: [[<YYYY-MM-DD>]]
- Reference: [[04-Agent-Reference-Files/Code-Standards]] · [[04-Agent-Reference-Files/Common-Pitfalls-to-Avoid]]

> [!tip] Persistence (where to save this log)
> Save per Unit-of-Work under the relevant project:
> - Create (if absent) folder: 01-Projects/<Project-Name>/Logs/SE-Work-Logs/
> - File name: SE-Log-<UNIT_ID>.md
> - Link this log from the Assignment note and from today’s daily note.

## Overview
- Restated scope (1–2 sentences):
- Acceptance criteria (copy from assignment; keep as checklist):
  - [ ] 
  - [ ] 
- Dependencies / prerequisites:
  - [[<Related-Note-or-UoW>]]
- Files to read first:
  - `path/to/file1`
  - `path/to/file2`

## Timeline & Notes

### 1) Receive Assignment
- Start: <YYYY-MM-DD HH:MM> UTC
- Restatement/clarifications:
- Blocking inputs (if any):
- Repo overview notes:

### 2) Pre-flight
- Plan (minimal change set):
- Test approach (what to run):
- Commands to validate environment:
```bash
# add commands you intend to run
```

### 3) Implementation (append small updates)
> Copy the snippet below for each update.

- <YYYY-MM-DD HH:MM> — Update N
  - Change intent:
  - Files touched: `path/...`, `path/...`
  - Rationale:
  - Risks/mitigations:

### 4) Validation
- Commands run:
```bash
# example
npm run lint
npm test -- --watch=false
```
- Results (pass/fail + notes):
- Acceptance criteria status:
  - [ ] 
  - [ ] 

### 5) Output Summary
- Diff/patch summary (high level):
- Tests added/updated:
- Build result:
- Anything noteworthy (perf, security, CSP):

## Escalation (use if blocked)
- unit_id: <UNIT_ID>
- Blocker (1–2 sentences):
- Exact files/commands tried (with short error snippets):
- Options/trade-offs (A/B) with recommended path:
- Explicit questions to unblock:
- Partial work available to stage? yes/no (where): [[SE-Log-<UNIT_ID>]]

## Links & Backlinks
- Project: [[01-Projects/<Project-Name>]]
- Assignment: [[03-Agent-Prompts/Work-Assigner/<Assignment-Note>]]
- Today: [[<YYYY-MM-DD>]]
- Related logs: [[SE-Log-<Related-UoW>]]

## Checklist
- [ ] Log created, linked from assignment and daily note
- [ ] Pre-flight complete (plan + commands noted)
- [ ] Minimal diffs implemented (≤5 files, ≤400 LOC)
- [ ] Validation commands run and recorded
- [ ] Summary completed and status updated to "done"