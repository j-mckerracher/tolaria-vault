# SE Log U20: Real Detection Data Integration and TP/FP Classification Infrastructure

**Date**: 2025-11-06  
**Sprint**: Real Data Integration - Detection Pipeline  
**Status**: In Progress (Infrastructure Complete, Visualization Pending)

## Objective
Integrate real LiDAR detection data from Waymo sequences with dual-view rendering showing Ground Truth vs. AGILE3D predictions, classified as True Positives (TP) or False Positives (FP) using BEV IoU.

---

## Completed Tasks (✅)

### 1. Detection PKL to JSON Conversion
- **Time**: ~15 minutes
- **Files Modified**: 
  - Fixed bug in `tools/converter/pkl_det_to_web_by_manifest.py` (line 189: numpy array boolean logic)
  - Converter now properly handles `pred_labels` arrays
  
- **Output Generated**:
  - All three sequences (v_1784_1828, p_7513_7557, c_7910_7954) converted
  - 90 detection JSON files per sequence (45 frames × 2 branches)
    - `frames/NNNNNN.det.DSVT_Pillar_030.json` (baseline)
    - `frames/NNNNNN.det.CP_Pillar_032.json` (AGILE3D variant)
  - Per-frame JSON schema: `{ boxes: [{ x, y, z, dx, dy, dz, heading, score, label }] }`
  
- **Manifests Updated**:
  - All three manifest.json files enriched with detection URLs
  - Frame URLs now include `det` object mapping branch IDs to detection file paths
  - No frame mismatches; all 45 frames matched in each sequence

### 2. SequenceDataService Enhancement
- **Time**: ~10 minutes
- **Changes**:
  - Added `DET_SCORE_THRESH` constant (default 0.7) export
  - Added `DetBox` interface matching detection JSON schema
  - Added `fetchDet(seqId: string, url: string)` async method
  - Added `mapDetToDetections()` method with:
    - Score-based filtering (threshold parameter)
    - Label mapping (1=vehicle, 2=pedestrian, 3=cyclist)
    - Coordinate transformation (dx/dy swapped to match renderer)
    - Heading preservation in radians
    - Confidence score mapping

- **File**: `src/app/core/services/data/sequence-data.service.ts`

### 3. BEV IoU Utility Implementation
- **Time**: ~30 minutes
- **File Created**: `src/app/core/services/frame-stream/bev-iou.util.ts` (231 lines)
- **Functions Implemented**:
  - `buildBoxCorners(box)` - Oriented rectangle corner generation from center, dimensions, heading
  - `bevIoU(boxA, boxB)` - 2D intersection-over-union in XY plane using Sutherland-Hodgman clipping
  - `classifyDetections(predictions, groundTruth, iouThresh)` - TP/FP marking via max IoU threshold
  - `cacheGTCorners()` - Pre-compute GT corners for performance
  - `classifyDetectionsFast()` - Optimized classification using cached corners
  - Helper functions: `sutherlandHodgmanClip()`, `polygonArea()`, `getLineIntersection()`, etc.

- **Algorithm Details**:
  - Uses Sutherland-Hodgman polygon clipping for robust oriented box intersection
  - Shoelace formula for polygon area computation
  - Predefined IoU threshold: 0.5 for TP determination
  - BEV-only (ignores Z) for speed and matches Pengcheng's reference implementation

### 4. FrameStreamService Detection Integration
- **Time**: ~45 minutes
- **File Modified**: `src/app/core/services/frame-stream/frame-stream.service.ts`

- **New Interfaces**:
  - `DetectionSet` with properties:
    - `det: Detection[]` - filtered detection objects
    - `cls: boolean[]` - TP/FP classification per detection
    - `delay?: number` - progressive delay for baseline
  - Extended `StreamedFrame` interface with:
    - `agile?: DetectionSet` - active branch detections + classification
    - `baseline?: DetectionSet` - baseline branch detections + classification
    - `gtCorners?: any[]` - cached GT corners for perf

- **New Configuration Properties**:
  - `activeBranch = 'CP_Pillar_032'` - default active branch
  - `baselineBranch = 'DSVT_Pillar_030'` - with fallback to _038 variants
  - `simulateDelay = false` - enables progressive delay mode
  - `detScoreThresh = 0.7` - score filtering threshold
  - `iouThresh = 0.5` - TP/FP boundary
  - `delayInitial = 2, delayGrowth = 0.2, delayMax = 10` - delay simulation params

- **Enhanced fetchFrame() Logic**:
  - Fetches detection URLs in parallel if present
  - Tries active branch first; skips silently if missing
  - Baseline tries configured branch, then falls back to _038, then _030 variants
  - Applies score filtering via `mapDetToDetections()`
  - Caches GT corners for repeated IoU evaluation
  - Calls `classifyDetectionsFast()` on both detection sets
  - Handles progressive delay simulation for baseline predictions
  - Maintains backward compatibility with legacy `det` field

- **Build Status**: ✅ Successful (with warnings only for SCSS deprecation)

### 5. Git Commits
- **Commit 1** (274c12b): "Convert detection PKLs to JSON and add detection fetching infrastructure; implement BEV IoU utilities for TP/FP classification"
  - Added converter fix, detection JSONs, sequence-data service updates, bev-iou util
- **Commit 2** (2b10cda): "Extend FrameStreamService with detection fetching and BEV IoU-based TP/FP classification for dual detection views"
  - Frame stream enhancements, interface updates, TypeScript fixes

---

## Remaining Tasks (📋)

### High Priority (Required for First Screenshot)

#### 1. Enable FP Highlighting in bbox-instancing.ts
- **Task**: Update `src/app/core/services/visualization/bbox-instancing.ts`
  - Accept per-instance classification array/map in instance update method
  - Apply color override logic:
    - **FP (false)**: Red (`#ff3b30`)
    - **TP (true)**: Class-based colors:
      - Vehicle: Blue (`#3b82f6`)
      - Pedestrian: Green (`#22c55e`)
      - Cyclist: Green (`#22c55e`)
  - Keep wireframe MeshBasicMaterial rendering
  - Do NOT modify GT visualization (left pane)

- **Estimated Time**: 20-30 minutes

#### 2. Wire Right Viewer to AGILE3D Detections
- **Task**: Update `src/app/features/main-demo/main-demo.component.ts`
  - Subscribe to updated `StreamedFrame` from `FrameStreamService.currentFrame$`
  - Left viewer:
    - Render point cloud
    - Render GT boxes only (existing logic, no changes)
    - Title: "Ground Truth"
  - Right viewer:
    - Render point cloud (same as left)
    - Render `agile.det` detections filtered by `DET_SCORE_THRESH`
    - Color per-instance using `agile.cls` classification array
    - Title: "AGILE3D (CP_Pillar_032)"
  - Maintain 10 Hz playback and shared camera sync
  - Optional: Add internal toggle (center button) to swap right view between agile ↔ baseline for testing

- **Estimated Time**: 30-40 minutes

#### 3. Dual Viewer Labels and Legend Hook
- **Task**: Update `src/app/features/dual-viewer/dual-viewer.component.ts`
  - Add/update pane titles in sequence mode
  - Left title: "Ground Truth"
  - Right title: Dynamically set to active branch (e.g., "AGILE3D (CP_Pillar_032)")
  - Add injection point for optional overlay contention legend in top-right
    - Hook labels: "No Contention", "Light Contention", "Intense Contention"
    - Default: Hidden (for first screenshot)
    - Can be populated/styled in later iteration

- **Estimated Time**: 15-20 minutes

#### 4. Missing Branch Variant Fallback & Robustness
- **Task**: Enhance error handling in FrameStreamService and visualization
  - If `frame.urls.det` lacks `activeBranch`, display "No detections for {branch}" in right pane
  - If `frame.urls.det` lacks baseline option, silently skip baseline rendering
  - Ensure no crashes on partial detection availability
  - Log warnings to console for diagnostic tracking

- **Estimated Time**: 10-15 minutes

### Medium Priority (Performance & Testing)

#### 5. Unit Tests for IoU and Classification
- **Task**: Create `src/app/core/services/frame-stream/bev-iou.util.spec.ts`
  - Test identical boxes → IoU ≈ 1.0
  - Test non-overlapping boxes → IoU ≈ 0
  - Test rotated overlap → 0 < IoU < 1
  - Test `classifyDetections()` with sample predicates
  - Validate dx/dy mapping by visual or numerical inspection
  - Run with `npm test` before acceptance

- **Estimated Time**: 30-45 minutes

#### 6. Performance Pass
- **Task**: Optimize hot loops and memory usage
  - Cache GT quad corners at frame boundary (already done in FrameStreamService)
  - Use Float32Arrays throughout (already in place)
  - Avoid object churn during classification loop
  - Profile looped playback:
    - Target: 60 FPS at 10 Hz tick (no stalls)
    - Memory: No growth over 45-frame loop cycles
    - Use Chrome DevTools or similar
  - Document findings in commit message

- **Estimated Time**: 20-30 minutes

### Lower Priority (Documentation & Polish)

#### 7. Documentation & README Update
- **Task**: Add README snippet under `src/assets/data/sequences/`
  - Explain branch ID mapping
  - Document score threshold (0.7) and IoU threshold (0.5)
  - Link to pkl2web_min.py for regeneration
  - Provide example manifest structure with detection URLs

- **Estimated Time**: 10-15 minutes

#### 8. Final Acceptance Checklist
- [ ] Manifests contain det URLs for both branches in all three sequences
- [ ] Playback smooth at 10 Hz with shared point cloud
- [ ] Left pane shows GT boxes only; labeled "Ground Truth"
- [ ] Right pane shows AGILE3D detections:
  - TP in class colors (blue, green)
  - FP in red
  - Score threshold 0.7, IoU threshold 0.5
- [ ] Optional: Toggle right pane baseline view (delayed) showing more FP in red
- [ ] Optional: Legend visible when enabled (hidden by default)
- [ ] Screenshot comparable to desired.png
- [ ] No memory leaks over sustained playback
- [ ] No console errors or warnings (except Sass deprecation)

---

## Technical Notes

### Data Flow
1. Manifest loaded → frames enumerated with det URLs
2. FrameStreamService.fetchFrame() → fetches points, GT, det in parallel
3. mapDetToDetections() → filter by score, map labels, swap dx/dy
4. classifyDetectionsFast() → compute BEV IoU, mark TP/FP
5. StreamedFrame emitted with agile/baseline DetectionSets
6. Main component subscribes → renders left (GT) and right (agile) with coloring

### Key Design Decisions
- **BEV-only IoU**: Matches Pengcheng's demo; avoids Z-axis variability and improves speed
- **Sutherland-Hodgman**: Robust polygon clipping handles rotated box intersections correctly
- **Pre-cached corners**: GT corners cached once per frame, reused for all predictions
- **Score threshold in SequenceDataService**: Filtering applied early to reduce downstream noise
- **Fallback branch logic**: Handles DSVT_Voxel_038 vs DSVT_Pillar_038 naming variations

### Known Limitations / Future Work
- Progressive delay simulation (simulateDelay flag) not yet visually validated
- Contention legend hook present but unfilled (ready for future enhancement)
- No per-prediction matching/tracking across frames (stateless classification)
- BEV IoU may miss fine Z-axis misalignments in stacked scenes

---

## Summary & Next Steps

**Infrastructure Status**: ✅ Complete
- All detection data converted and indexed
- Services enhanced for dual-branch rendering
- IoU calculation pipeline integrated
- Build passes with no errors

**Visualization Status**: 🚧 In Progress
- Remaining tasks focus on rendering the classification results
- Estimated 2-3 hours to complete high-priority visualization items
- Then performance testing and documentation

**Recommendation**: 
1. Start with bbox-instancing FP highlighting (cleanest scope)
2. Wire main-demo component to render dual views
3. Add labels and robustness guards
4. Test and optimize before final acceptance

**Next Commit Message**:
```
feat: 2025-11-06 Implement dual-view detection rendering with TP/FP coloring via BEV IoU classification; add bbox instancing updates and viewer labels
```

---

## Update 2025-11-07: Visualization Implementation (Step 1 and Step 2)

### Step 1 — Uniform Per-Class Wireframe Colors
- Goal: make class colors immediately visible while keeping the wireframe aesthetic.
- Change: in `bbox-instancing.ts` switched `MeshBasicMaterial` to use a uniform class color (vertexColors off) per instanced mesh.
- Result: Vehicles/Pedestrians/Cyclists render in distinct colors; no TP/FP yet.

### Step 2 — FP Highlighting with Split Instanced Meshes
- Goal: show FP in red without custom shaders and keep wireframe performance.
- Changes:
  - `ClassBatches` now stores `THREE.Object3D` per class, which is a Group containing up to two InstancedMeshes:
    - TP (and unknown) mesh in class color
    - FP mesh in red (#ff3b30)
  - New `createClassGroup()` partitions detections by classification map and `diffMode` ('all' | 'tp' | 'fp' | 'off').
  - `createInstancedMesh()` remains a uniform wireframe color path.
  - `disposeClassBatches()` traverses child meshes in Groups and disposes geometry/materials safely.
  - `SceneViewerComponent` updates:
    - Adds the returned Group to the scene (not just a single InstancedMesh)
    - Raycasting now traverses Groups to gather all InstancedMesh children for hover tooltips.
- Result: Red boxes appear for FPs in the AGILE3D pane; TP remain in class colors.

### UI Enhancements
- DualViewer
  - Titles: left defaults to "Ground Truth"; right bound to `AGILE3D (${activeBranch})` from MainDemo.
  - Legend overlay (top-right): shows class color swatches and FP red swatch.
  - FP Only toggle (top-left): quick debugging to switch `diffMode` between 'all' and 'fp'.
  - "No detections for branch" overlay appears in right pane when missing.
- SceneViewer
  - Tooltip now includes a "Pane:" row showing "GT" (left) or "AGILE3D" (right).

### Main Demo Wiring
- On each streamed frame:
  - baselineDetections = GT boxes.
  - AGILE3D detections from `streamedFrame.agile.det` when available; otherwise fallback.
  - Build `agile3dDiffClassification` Map<det.id, 'tp'|'fp'> from `streamedFrame.agile.cls` flags and pass to `DualViewer`.
  - Update right title to include the active branch id.

### Streaming Robustness & Console Hygiene
- Prefetch promises can be aborted when the prefetch window slides or loops. Added a no-op `.catch()` on prefetch promises to suppress unhandled rejection noise while keeping real error paths intact.

### Observed Behavior (sanity checks)
- Class colors visible in both panes; most objects in current snippets are vehicles (expected).
- AGILE3D pane shows red boxes for FPs; FP Only toggle filters to just those.
- Tooltip reports Pane and Confidence; GT tooltips default class to vehicle when GT labels are missing (documented limitation).

### Known Limitations / Notes
- GT JSON often lacks per-box labels; we default GT class to `vehicle` to avoid misclassification guesses.
- Contention legend remains a future hook (current overlay is class+FP legend only).

### Updated Remaining Tasks / Status
- ✅ FP highlighting implemented via split instanced meshes.
- ✅ Right viewer wired to AGILE3D detections; classification map applied; dynamic right title.
- ✅ Labels and legend: viewer titles active; legend overlay added; contention legend deferred.
- ✅ Robustness: right-pane "No detections for branch" overlay; baseline fallback logic present.
- 🔬 Tests and performance pass remain.

### Acceptance Checklist (current status)
- [x] Manifests contain det URLs for branches in all three sequences
- [x] Playback smooth at 10 Hz with shared point cloud
- [x] Left pane shows GT boxes only; labeled "Ground Truth"
- [x] Right pane shows AGILE3D detections with TP (class colors) and FP (red)
- [x] Score threshold 0.7, IoU threshold 0.5 enforced
- [x] FP Only toggle works for debugging
- [x] Legend overlay displayed (class + FP)
- [ ] Optional baseline delayed view comparison (hook present; UI toggle later)
- [ ] No memory growth over long playback (to validate)

### Next Steps (short list)
1. Unit tests for IoU/Classification utilities.
2. Performance profiling across loop cycles; ensure no leaks.
3. Optional: baseline/AGILE3D toggle in right pane for side-by-side FP comparison.
4. Optional: make legend togglable from UI.

---

**Log Author**: Agent Mode  
**Last Updated**: 2025-11-07 05:00 UTC
