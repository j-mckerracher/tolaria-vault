---
plan_title: "Make Control Panel Effective + Voxel/Contention + Match Desired Image"
tags: [planning, controls, branches, voxel, contention, streaming]
created: 2025-11-08T21:34:37Z
status: draft
---

# Plan — Control Panel, Voxel Size, Contention, and Matching Desired Image

## Goals
- Make control panel selections visibly change the scene (sequence, branch, filters, contention).
- Expose voxel-size variants as selectable baseline branches.
- Simulate contention (delay/misses) without new data.
- Match the desired image: Left = baseline predictions with TP/FP coloring, Right = Agile3D predictions with the same.

---

## Included guidance (verbatim)

> Yes—precomputed data doesn’t prevent the control panel from changing what you see. The key is to map each control to either:
> • which precomputed assets you load, or
> • a client-side transform/filter you apply to those assets.
>
> What the controls can change without recomputing data
> • Scene/sequence: pick a different manifest.json and restart streaming.
> • Branches: switch which per-frame det JSON you fetch (baseline vs Agile3D) while using GT only for TP/FP classification.
> • Tier (full vs fallback): pick the sequence/tier directory that has ≤100k vs ≤50k frames (requires both tiers to exist in assets/CDN).
> • Score threshold: filter boxes client-side and re-run classification.
> • Label mask: include/exclude vehicle/pedestrian/cyclist client-side.
> • Diff mode: show all/tp/fp; purely rendering logic.
> • Delay simulation: baseline frame index offset; no new files needed.
> • Playback params: fps, prefetch, concurrency; service behavior only.
> • Camera presets: purely viewer state.
>
> What the controls cannot change (without new precomputation)
> • The underlying predictions for a model/branch that you didn’t export.
> • Alternate point clouds not present in assets (e.g., different downsample if only one tier shipped).
>
> Minimal plan to make the control panel effective
> • Add a sequence/branch resolver that maps UI selection → URLs:
>   ◦ sequenceId → {manifestUrl}
>   ◦ baselineBranchId, activeBranchId → per-frame det URLs from manifest
> • Extend FrameStreamService:
>   ◦ loadSequence(seqId): abort inflight, clear caches, fetch manifest, reinit geometry, restart cadence.
>   ◦ setBranches(baselineId, activeId): start fetching the two det streams for each frame; reclassify.
>   ◦ setFilters({score, labelMask}), setDiffMode(), setDelaySimulation(): update rendering without restart.
> • Wire controls to these methods and disable the controls while status=Loading.
> • Acceptance: switching scene/branch visibly changes frame IDs, box counts/colors, and labels; no stale data; memory stable.

---

## Data readiness — which detection files to convert

Your available PKLs (baseline DSVT Pillar variants):
- 001/: dsvt_sampled_pillar030_det.pkl, dsvt_sampled_pillar032_det.pkl, dsvt_sampled_pillar038_det.pkl, dsvt_sampled_pillar046_det.pkl
- 002/: dsvt_sampled_pillar036_det.pkl, dsvt_sampled_pillar040_det.pkl, dsvt_sampled_pillar050_det.pkl

Convert ALL of the above into per-frame detection JSON for each sequence you ship (v_1784_1828, p_7513_7557, c_7910_7954).

Branch ID mapping (use these exact keys in manifests and file names):
- dsvt_sampled_pillar030_det.pkl → DSVT_Pillar_030
- dsvt_sampled_pillar032_det.pkl → DSVT_Pillar_032
- dsvt_sampled_pillar036_det.pkl → DSVT_Pillar_036
- dsvt_sampled_pillar038_det.pkl → DSVT_Pillar_038
- dsvt_sampled_pillar040_det.pkl → DSVT_Pillar_040
- dsvt_sampled_pillar046_det.pkl → DSVT_Pillar_046
- dsvt_sampled_pillar050_det.pkl → DSVT_Pillar_050

Active (Agile3D) branch already present:
- CP_Pillar_032 (keep as default right‑pane branch)

Conversion (repeat per branch × sequence):
```bash
python tools/converter/pkl_det_to_web_by_manifest.py \
  --pkl /path/to/dsvt_sampled_pillar038_det.pkl \
  --seq-dir src/assets/data/sequences/v_1784_1828 \
  --branch DSVT_Pillar_038
```
Outputs per sequence:
- frames/NNNNNN.det.{BRANCH}.json
- Update manifest.frames[i].urls.det[{BRANCH}] to point to each file.

---

## Ordered implementation plan (dependencies-first)

1) Normalize manifests and branch keys (data contract)
- Ensure every sequence manifest top-level `branches` matches exactly the union of `frames[0].urls.det` keys.
- Remove stale names (e.g., `DSVT_Voxel`) and add the converted keys above.
- Acceptance: for each sequence, frames[0].urls.det contains at least `{ DSVT_Pillar_030, CP_Pillar_032 }` and any newly converted DSVT_Pillar_0xx.

2) Convert additional DSVT variants (voxel-size)
- Run the converter for each of the 7 PKLs across all three sequences.
- Use the converter fixed in U20: tools/converter/pkl_det_to_web_by_manifest.py) to emit frames/NNNNNN.det.{BRANCH}.json for each sequence based on manifest frame_ids.
- Here are all det files: ![[Pasted image 20251108145601.png]]
- Update manifests with new det URLs; validate presence with a quick script or grep.
- Acceptance: manifests reference valid JSON files for all selected branches.

3) Sequence/branch resolver (runtime)
- Implement `SequenceRegistry` (seqId → manifestUrl) using runtime-config.json.
- Derive available branch IDs from `frames[0].urls.det` at runtime; expose to the control panel.
- Acceptance: control panel lists only branches that truly exist in the loaded manifest.

1) FrameStreamService enhancements
- `loadSequence(seqId)`: abort inflight, clear queues, fetch manifest, reinit geometry from first frame’s `pointCount`, restart cadence.
- `setBranches(baselineId, activeId)`: for each fetched frame, load both branches’ det files, classify vs GT (IoU=0.5), emit to left/right panes.
- `setFilters({score, labelMask})`, `setDiffMode(mode)`, `setDelaySimulation({frames})`.
- Acceptance: switching sequence/branch updates counts/colors immediately; no stale buffers; status$ shows Loading/Ready.

5) Visualization to match desired image
- Left pane = baseline predictions (selected DSVT_Pillar_0xx) with TP class colors and FP red (#ff3b30).
- Right pane = Agile3D (CP_Pillar_032) same coloring.
- GT is used only for classification; keep hidden or faint (toggle).
- Acceptance: visual parity with desired.png on p_7513_7557 (pedestrians visible and colored correctly).

6) Contention controls (no new data)
- Delay simulation: baseline uses `index - delayFrames` while points/GT use `index`.
- Miss injection: drop/timeout k% frames to exercise banner and buffering.
- Acceptance: increasing delay increases FP (more red) on left; miss rate triggers pause after 3 consecutive misses.

7) Control panel wiring (UX)
- Controls to add:
  - Sequence selector (v_1784_1828, p_7513_7557, c_7910_7954).
  - Baseline branch (voxel size): dropdown from available `DSVT_Pillar_0xx`.
  - Active branch: default CP_Pillar_032 (more can be added later).
  - Diff mode: all | fp | tp.
  - Score threshold slider (default 0.7).
  - Label toggles: vehicle, pedestrian, cyclist.
  - Contention: delay (0–10 frames), miss rate (0–30%).
  - Playback: fps (10 default), prefetch (3), concurrency (2–3).
  - Camera presets: bird’s‑eye, isometric.
- Disable controls while status=Loading; show spinner.
- Acceptance: each control changes the scene or streaming behavior without reloads (except sequence switch which restarts).

8) QA and tests
- Unit: IoU/classify, service restart, branch switch, filters, delay.
- E2E: 
  - Switch sequence → frame IDs and pointCount change.
  - Switch baseline DSVT_Pillar_030 → DSVT_Pillar_038 → visible detection/TPFP differences.
  - Delay increases FP on left.
- Soak: 10‑minute loop, no memory growth; fps ≥55.

---

## Risks & mitigations
- Branch name drift → derive branch list from manifest at runtime; validate on load.
- Large frames stutter on switch → preload first target frame before swapping labels; show Loading banner.
- Missing ped labels in GT → acceptable (GT used only for IoU); ensure prediction labels 2/3 appear in CP/DSVT JSON.

---

## Acceptance checklist
- [ ] Manifests normalized; frames[0].urls.det reflects real branches.
- [ ] Converted JSONs exist for all DSVT_Pillar_0xx across all sequences.
- [ ] Control panel sequence/branch switching works and visibly changes the scene.
- [ ] Left = baseline (DSVT_Pillar_0xx), Right = CP_Pillar_032; TP class colors, FP red.
- [ ] Contention controls (delay/miss) change the scene as specified.
- [ ] Pedestrians visible on p_7513_7557; matching screenshot achievable.
