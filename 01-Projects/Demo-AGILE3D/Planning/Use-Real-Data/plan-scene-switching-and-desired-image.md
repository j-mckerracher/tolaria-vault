---
plan_title: "Fix Scene Switching + Match Desired Image"
tags: [planning, bugfix, ui, streaming, detections]
created: 2025-11-08T04:37:36Z
status: draft
---

# Plan — Fix Scene Switching and Match the Desired Image

## Context
- Current behavior: selecting different scenes in the control panel does not change the loaded sequence. Left pane renders Ground Truth (GT) only, so it never shows FP (by definition). Desired: baseline vs Agile3D predictions, TP in class colors and FP in red, similar to desired.png.

---

## A) Fix Scene Switching (sequence selection does nothing)

### Likely root causes
1) UI event not wired to service: selection updates local state but never triggers a re-load.
2) FrameStreamService lacks a proper restart path (abort → clear → load new manifest → start).
3) Manifest base URL/registry missing or wrong (all selections resolve to same path).
4) Change detection/async race: component doesn’t react to selection (OnPush + missing subscription).

### Diagnostics
- Log the selected seqId from the control panel and verify it reaches the container (MainDemo or StateService).
- Log FrameStreamService when `start()` is called; assert it runs on selection change with the new manifest URL.
- Inspect active AbortControllers and prefetch queue on switch; ensure old requests are aborted.

### Implementation plan
1) Sequence registry and resolver
   - Add `SequenceRegistry` mapping: seqId → manifest URL (runtime-config aware).
   - File: `apps/web/src/app/services/config/config.service.ts` and/or new `sequence-registry.ts`.
   - Example: `assets/data/sequences/${seqId}/manifest.json` (dev) or `${manifestBaseUrl}/${seqId}/manifest.json` (CDN).

2) Service API for switching sequences
   - Add `loadSequence(seqId: string)` to `FrameStreamService`:
     - pause(); abort in‑flight; clear caches/buffers; reset indices and miss counters; emit status=Loading.
     - resolve manifest URL via SequenceRegistry; fetch with timeout/retry; set `this.manifest` and `this.sequenceId`.
     - (Re)initialize shared geometry capacity from first frame pointCount; restart cadence with fresh prefetch window.
   - Ensure all observables (`currentFrame$`, `status$`, `bufferLevel$`) re-emit from a clean state.

3) Wire control panel → service
   - In the control panel component (or MainDemo), subscribe to selection changes and call `frameStream.loadSequence(seqId)`.
   - Disable the selector while `status$==='Loading'`; show small spinner.

4) Title/label updates
   - Update DualViewer labels from the active `seqId` and branch names (baseline vs Agile3D) so the user sees the change.

5) Tests
   - Unit: FrameStreamService “switch sequence” flow aborts old requests, resets indices, loads new manifest.
   - E2E: Clicking scene A then scene B updates frame IDs and right‑pane title; verify pointCount differs between scenes.

### Acceptance criteria
- Selecting a different scene causes:
  - Old network requests aborted; prefetch reset; playback restarts at frame 0 of the new sequence.
  - Both panes reflect new sequence (labels update; geometry changes; frame IDs differ).
  - No memory growth or stale buffers across 3+ rapid switches.

---

## B) Match the Desired Image (baseline vs Agile3D with TP/FP coloring)

Attached guidance (carry-over):
- Render predictions on both panes (use GT only to classify):
  - Left: baseline branch predictions (e.g., `DSVT_Voxel_038`) with TP in class colors and FP in red.
  - Right: Agile3D branch predictions with the same coloring.
  - Keep GT hidden or faint; it’s the matcher, not a viewer layer.

### Implementation plan
1) Branch role semantics
   - Define `baselineBranch='DSVT_Voxel_038'` (fallback `DSVT_Voxel_030` if missing) and `activeBranch='CP_Pillar_032'` in config/service.
   - Standardize names in manifests and det files.

2) StreamedFrame payloads
   - For each frame, fetch det JSON for both branches; compute classification via BEV IoU (threshold=0.5) against GT.
   - Emit `agile` and `baseline` detection sets with `Map<string,'tp'|'fp'>`.

3) Visualization
   - Left pane: render `baseline.det` with TP/FP coloring; Right pane: render `agile.det` similarly.
   - Keep GT hidden or as a faint outline (optional toggle) to avoid visual clutter.
   - Colors: vehicle=blue, ped/cyclist=green; FP override=red (#ff3b30).

4) Ensure pedestrians appear
   - Use sequence `p_7513_7557` for the screenshot (pedestrian‑heavy).
   - Confirm det JSON include labels 2/3 and label filters are enabled; score threshold default 0.7.

5) UI updates
   - Update DualViewer titles: Left “Baseline (DSVT_Voxel_038)”, Right “AGILE3D (CP_Pillar_032)”.
   - Optional: quick toggle to show only FP for debugging.

6) Tests & validation
   - Unit: IoU utility, classification map correctness on small synthetic cases.
   - E2E: Load pedestrian sequence; assert red boxes present (FP) and green/blue (TP) visible.

### Acceptance criteria (visual)
- With `p_7513_7557` selected: pedestrians visible (green) in the right pane; left pane shows baseline predictions with some red FPs under contention.
- Both panes share the same point cloud and frame cadence.
- Screenshot comparable to desired.png.

---

## C) Tasks and owners (suggested)
- Config/registry + service restart flow (FS): 0.5–1 day
- DualViewer wiring (baseline left, Agile3D right) + coloring: 0.5 day
- Sequence selector UI wiring + loading state: 0.25 day
- Tests (unit + basic e2e): 0.5 day
- Final screenshot pass: 0.25 day

---

## D) Risks and mitigations
- Naming drift of baseline branch → enforce constants and validate manifest keys on load.
- Large frames cause stutter on switch → preload first frame of target sequence before switching labels; show spinner.
- Missing ped labels in GT → OK (GT only used for classification). Ensure prediction labels 2/3 present.

---

## E) Quick checklist
- [ ] Sequence selector triggers `frameStream.loadSequence()`
- [ ] Manifest resolves per seqId; old fetches aborted
- [ ] Left=baseline predictions; Right=Agile3D predictions
- [ ] TP class colors; FP red
- [ ] Pedestrians visible on `p_7513_7557`
- [ ] E2E click‑switch test passes
