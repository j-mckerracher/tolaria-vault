# Detailed Implementation Plan — Use Real Data

**Goal**: Transform the current sequence playback scene (actual.png) into a side-by-side visualization where the left pane shows Ground Truth (GT) boxes over the real LiDAR point cloud, and the right pane shows predicted detections for an AGILE3D branch, with TP/FP classification via BEV IoU and optional progressive delay simulation.

**Status**: Ready for implementation  
**Last Updated**: 2025-11-06T15:21:58Z

---

## Scope and Defaults

- **Left pane**: Ground Truth (GT) boxes over real Waymo LiDAR point clouds.
- **Right pane**: Predicted detections for an AGILE3D branch over the same point cloud.
- **TP/FP classification**: BEV IoU threshold = 0.5.
- **Default score threshold**: 0.7.
- **Branch IDs**:
  - Baseline: `DSVT_Voxel_038` (fallback: `DSVT_Voxel_030` if 038 unavailable).
  - Active AGILE3D (right pane default): `CP_Pillar_032`.
- **Data storage**: Local under `src/assets/data/sequences` for v_1784_1828, p_7513_7557, c_7910_7954.
- **Contention legend**: Not shown on first iteration; add hook for later.
- **Progressive delay**: Implement baseline delay hook for comparison; keep default display on AGILE3D current predictions.

---

## Step 1: Collect Detection PKLs from Pengcheng

**Inputs**:
- Baseline: `dsvt_sampled_voxel038_det.pkl` (or `pillar030` if 038 unavailable).
- AGILE3D: `CP_Pillar_032` variant (CenterPoint Pillar).

**Schema (from Pengcheng)**:
- Detection PKL dict keys: `name`, `score`, `boxes_lidar`, `pred_labels`, `frame_id`, `metadata`.
- `boxes_lidar`: `[x, y, z, dx, dy, dz, heading]` per box.
- Label map: 1→vehicle, 2→pedestrian, 3→cyclist.

**Action**:
- Store PKLs in a local folder (not committed).
- Note the frame count (expect ~39,987 total; we will extract snippets for each sequence).

---

## Step 2: Convert PKLs to Per-Frame JSON and Enrich Manifests

**Tool**: `C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\AGILE3D-Demo\pkl2web_min.py`

**Output per sequence** (for frames 000000–000044, for example):
```
frames/000000.det.DSVT_Voxel_038.json
frames/000000.det.CP_Pillar_032.json
...
frames/000044.det.DSVT_Voxel_038.json
frames/000044.det.CP_Pillar_032.json
```

**JSON shape** (each file):
```json
{
  "boxes": [
    {
      "x": 0.3,
      "y": 12.1,
      "z": -1.2,
      "dx": 4.5,
      "dy": 1.8,
      "dz": 1.6,
      "heading": 1.57,
      "score": 0.92,
      "label": 1
    }
  ]
}
```

**Manifest update** (each sequence's `manifest.json` frame entry):
```json
{
  "id": "000000",
  "origId": "...",
  "urls": {
    "points": "frames/000000.bin",
    "gt": "frames/000000.gt.json",
    "det": {
      "DSVT_Voxel_038": "frames/000000.det.DSVT_Voxel_038.json",
      "CP_Pillar_032": "frames/000000.det.CP_Pillar_032.json"
    }
  },
  "pointCount": 193807
}
```

**Fallback handling**:
- If only `pillar030` is present for baseline, use branch key `DSVT_Voxel_030` and surface in UI.

**Sanity checks**:
- Non-empty detection arrays.
- Reasonable coordinate and score ranges.
- All three sequences have complete det files.

---

## Step 3: Verify Final Assets Tree

**Expected structure** (per sequence):
```
src/assets/data/sequences/
├── v_1784_1828/
│   ├── manifest.json
│   └── frames/
│       ├── 000000.bin (points)
│       ├── 000000.gt.json
│       ├── 000000.det.DSVT_Voxel_038.json (or DSVT_Voxel_030.json)
│       ├── 000000.det.CP_Pillar_032.json
│       ├── 000001.bin
│       ├── ...
│       ├── 000044.bin
│       ├── 000044.gt.json
│       ├── 000044.det.DSVT_Voxel_038.json (or _030)
│       └── 000044.det.CP_Pillar_032.json
├── p_7513_7557/
│   └── ... (same structure)
└── c_7910_7954/
    └── ... (same structure)
```

**Validation**:
- Frame count = 45 per sequence.
- All `det` URLs present.

---

## Step 4: Add Detection Fetch + Mapping in SequenceDataService

**File**: `src/app/core/services/data/sequence-data.service.ts`

**Additions**:

1. **Interface for detection boxes**:
```typescript
interface DetBox {
  x: number;
  y: number;
  z: number;
  dx: number;
  dy: number;
  dz: number;
  heading: number;
  score: number;
  label: number;
}

interface DetFile {
  boxes: DetBox[];
}
```

2. **fetchDet method**:
```typescript
async fetchDet(seqId: string, url: string): Promise<DetFile> {
  const fullUrl = `assets/data/sequences/${seqId}/${url}`;
  return firstValueFrom(this.http.get<DetFile>(fullUrl));
}
```

3. **mapDetToDetections method**:
```typescript
mapDetToDetections(
  branchId: string,
  boxes: DetBox[],
  scoreThresh: number = 0.7
): Detection[] {
  return boxes
    .filter(box => box.score >= scoreThresh)
    .map((box, i) => {
      const label = box.label !== undefined 
        ? LABEL_MAP[box.label] 
        : 'vehicle';
      
      if (!label) {
        console.warn(`[SequenceDataService] Unknown label ${box.label}, skipping`);
        return null;
      }

      return {
        id: `${branchId}-${i}`,
        class: label,
        center: [box.x, box.y, box.z] as [number, number, number],
        dimensions: {
          // Waymo: dx=length (X-axis), dy=width (Y-axis), dz=height
          // Renderer: width (X), length (Y), height (Z)
          width: box.dy,
          length: box.dx,
          height: box.dz
        },
        yaw: box.heading,
        confidence: box.score
      };
    })
    .filter((d): d is Detection => d !== null);
}
```

4. **Export constant**:
```typescript
export const DET_SCORE_THRESH = 0.7;
```

---

## Step 5: Implement BEV IoU + TP/FP Classification

**File**: New utility module `src/app/core/services/frame-stream/bev-iou.ts` (or inline in frame-stream service)

**Core functions**:

1. **Oriented rectangle corners (BEV)**:
```typescript
function getCorners2D(x: number, y: number, dx: number, dy: number, heading: number): [number, number][] {
  // Local corners (half-dimensions)
  const corners = [
    [dx / 2, dy / 2],
    [dx / 2, -dy / 2],
    [-dx / 2, -dy / 2],
    [-dx / 2, dy / 2]
  ];

  const cos = Math.cos(heading);
  const sin = Math.sin(heading);

  // Rotate and translate
  return corners.map(([lx, ly]) => [
    x + lx * cos - ly * sin,
    y + lx * sin + ly * cos
  ]) as [number, number][];
}
```

2. **Polygon intersection (Sutherland–Hodgman)**:
```typescript
function polygonIntersection(subj: [number, number][], clip: [number, number][]): [number, number][] {
  let output = [...subj];

  for (let i = 0; i < clip.length; i++) {
    const A = clip[i];
    const B = clip[(i + 1) % clip.length];

    const input = output;
    output = [];

    if (input.length === 0) break;

    for (let j = 0; j < input.length; j++) {
      const P1 = input[j];
      const P2 = input[(j + 1) % input.length];

      const p1Inside = ccw(A, B, P1) >= 0;
      const p2Inside = ccw(A, B, P2) >= 0;

      if (p2Inside) {
        if (!p1Inside) {
          const intersection = lineIntersection(P1, P2, A, B);
          if (intersection) output.push(intersection);
        }
        output.push(P2);
      } else if (p1Inside) {
        const intersection = lineIntersection(P1, P2, A, B);
        if (intersection) output.push(intersection);
      }
    }
  }

  return output;
}

function ccw(A: [number, number], B: [number, number], C: [number, number]): number {
  return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]);
}

function lineIntersection(
  p1: [number, number],
  p2: [number, number],
  p3: [number, number],
  p4: [number, number]
): [number, number] | null {
  const x1 = p1[0], y1 = p1[1];
  const x2 = p2[0], y2 = p2[1];
  const x3 = p3[0], y3 = p3[1];
  const x4 = p4[0], y4 = p4[1];

  const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
  if (Math.abs(denom) < 1e-10) return null;

  const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;

  return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)];
}
```

3. **Polygon area (shoelace)**:
```typescript
function polygonArea(polygon: [number, number][]): number {
  if (polygon.length < 3) return 0;
  let area = 0;
  for (let i = 0; i < polygon.length; i++) {
    const j = (i + 1) % polygon.length;
    area += polygon[i][0] * polygon[j][1];
    area -= polygon[j][0] * polygon[i][1];
  }
  return Math.abs(area) / 2;
}
```

4. **BEV IoU**:
```typescript
export function bevIoU(
  boxA: { x: number; y: number; dx: number; dy: number; heading: number },
  boxB: { x: number; y: number; dx: number; dy: number; heading: number }
): number {
  const cornersA = getCorners2D(boxA.x, boxA.y, boxA.dx, boxA.dy, boxA.heading);
  const cornersB = getCorners2D(boxB.x, boxB.y, boxB.dx, boxB.dy, boxB.heading);

  const intersection = polygonIntersection(cornersA, cornersB);
  const intersectionArea = polygonArea(intersection);

  const areaA = polygonArea(cornersA);
  const areaB = polygonArea(cornersB);

  const unionArea = areaA + areaB - intersectionArea;
  return unionArea > 1e-6 ? intersectionArea / unionArea : 0;
}
```

5. **Classification**:
```typescript
export function classifyDetections(
  preds: Detection[],
  gts: Detection[],
  iouThresh: number = 0.5
): Map<string, 'tp' | 'fp'> {
  const result = new Map<string, 'tp' | 'fp'>();
  const matchedGts = new Set<number>();

  for (let i = 0; i < preds.length; i++) {
    const pred = preds[i];
    let maxIoU = 0;
    let bestGtIdx = -1;

    for (let j = 0; j < gts.length; j++) {
      const gt = gts[j];
      const iou = bevIoU(
        {
          x: pred.center[0],
          y: pred.center[1],
          dx: pred.dimensions.length,
          dy: pred.dimensions.width,
          heading: pred.yaw
        },
        {
          x: gt.center[0],
          y: gt.center[1],
          dx: gt.dimensions.length,
          dy: gt.dimensions.width,
          heading: gt.yaw
        }
      );

      if (iou > maxIoU) {
        maxIoU = iou;
        bestGtIdx = j;
      }
    }

    if (maxIoU >= iouThresh && bestGtIdx >= 0) {
      result.set(pred.id, 'tp');
      matchedGts.add(bestGtIdx);
    } else {
      result.set(pred.id, 'fp');
    }
  }

  return result;
}
```

**Performance notes**:
- Precompute GT BEV corners per frame to avoid recomputation.
- Use Float32Array internally if needed.
- Avoid object churn in hot loops.

---

## Step 6: Extend FrameStreamService for Both Branches + Progressive Delay

**File**: `src/app/core/services/frame-stream/frame-stream.service.ts`

**Update StreamedFrame interface**:
```typescript
export interface StreamedFrame {
  index: number;
  frame: FrameRef;
  points: Float32Array;
  gt: Detection[];
  agile?: {
    det: Detection[];
    cls: Map<string, 'tp' | 'fp'>;
  };
  baseline?: {
    det: Detection[];
    cls: Map<string, 'tp' | 'fp'>;
    delay: number;
  };
}
```

**Add configuration to start options**:
```typescript
interface FrameStreamStartOptions {
  fps?: number;
  prefetch?: number;
  loop?: boolean;
  activeBranch?: string; // default 'CP_Pillar_032'
  baselineBranch?: string; // default 'DSVT_Voxel_038'
  simulateDelay?: boolean; // default false
  delayParams?: {
    initDelay: number; // default 2
    growth: number; // default 0.2
    maxDelay: number; // default 10
  };
}
```

**Update start() method signature**:
```typescript
start(
  manifest: SequenceManifest,
  opts?: FrameStreamStartOptions & { fps?: number; prefetch?: number; loop?: boolean }
): void
```

**Update fetchFrame to handle both branches**:
```typescript
private async fetchFrame(index: number, signal?: AbortSignal): Promise<StreamedFrame> {
  if (!this.manifest) throw new Error('No manifest loaded');

  const frame = this.manifest.frames[index];
  if (!frame) throw new Error(`Frame ${index} not found`);

  const seqId = this.manifest.sequenceId;

  // Fetch points and GT
  const [pointsBuffer, gtFile] = await Promise.all([
    this.sequenceData.fetchPoints(seqId, frame.urls.points),
    frame.urls.gt ? this.sequenceData.fetchGT(seqId, frame.urls.gt) : Promise.resolve({ boxes: [] })
  ]);

  if (signal?.aborted) throw new Error('Aborted');

  // Parse points
  const parsed = await this.sceneData.parseInWorker(pointsBuffer, 3);
  // ... (existing axis remap heuristic and stride handling)

  const gt = this.sequenceData.mapGTToDetections(frame.id, gtFile.boxes);

  // Fetch AGILE3D detections
  let agileDetections: Detection[] = [];
  let agileClassification = new Map<string, 'tp' | 'fp'>();

  if (frame.urls.det && this.activeBranch && frame.urls.det[this.activeBranch]) {
    const agileDetFile = await this.sequenceData.fetchDet(
      seqId,
      frame.urls.det[this.activeBranch]
    );
    agileDetections = this.sequenceData.mapDetToDetections(
      this.activeBranch,
      agileDetFile.boxes,
      0.7 // scoreThresh
    );
    agileClassification = classifyDetections(agileDetections, gt, 0.5);
  }

  // Fetch baseline detections with optional delay
  let baselineDetections: Detection[] = [];
  let baselineClassification = new Map<string, 'tp' | 'fp'>();
  let currentDelay = 0;

  if (this.baselineBranch && this.manifest.frames[index].urls.det?.[this.baselineBranch]) {
    let baselineIndex = index;

    if (this.simulateDelay) {
      currentDelay = Math.min(
        this.maxDelay,
        Math.round(this.initDelay + index * this.delayGrowth)
      );
      baselineIndex = Math.max(0, index - currentDelay);
    }

    const baselineFrame = this.manifest.frames[baselineIndex];
    if (baselineFrame?.urls.det?.[this.baselineBranch]) {
      const baselineDetFile = await this.sequenceData.fetchDet(
        seqId,
        baselineFrame.urls.det[this.baselineBranch]
      );
      baselineDetections = this.sequenceData.mapDetToDetections(
        this.baselineBranch,
        baselineDetFile.boxes,
        0.7
      );
      baselineClassification = classifyDetections(baselineDetections, gt, 0.5);
    }
  }

  return {
    index,
    frame,
    points,
    gt,
    agile: {
      det: agileDetections,
      cls: agileClassification
    },
    baseline: {
      det: baselineDetections,
      cls: baselineClassification,
      delay: currentDelay
    }
  };
}
```

**Store config in start()**:
```typescript
start(manifest, opts?) {
  // ... existing code
  this.activeBranch = opts?.activeBranch ?? 'CP_Pillar_032';
  this.baselineBranch = opts?.baselineBranch ?? 'DSVT_Voxel_038';
  this.simulateDelay = opts?.simulateDelay ?? false;

  const delayParams = opts?.delayParams ?? {};
  this.initDelay = delayParams.initDelay ?? 2;
  this.delayGrowth = delayParams.growth ?? 0.2;
  this.maxDelay = delayParams.maxDelay ?? 10;
  // ... rest of init
}
```

---

## Step 7: Enable FP Highlighting in BBox Instancing

**File**: `src/app/core/services/visualization/bbox-instancing.ts`

**Update createInstancedMesh signature**:
```typescript
function createInstancedMesh(
  detections: Detection[],
  classType: DetectionClass,
  color: THREE.Color,
  diffMode: DiffMode,
  diffClassification?: Map<string, 'tp' | 'fp' | 'fn'> | Map<string, 'tp' | 'fp'>
): THREE.InstancedMesh {
  // ... existing code
  const fpColor = new THREE.Color(0xff3b30); // red
  
  for (let i = 0; i < count; i++) {
    const det = detections[i];
    if (!det) continue;

    // ... existing matrix setup

    // Set instance color
    const instanceColor = new THREE.Color();
    
    // Check if this detection is FP
    const classification = diffClassification?.get(det.id);
    if (classification === 'fp') {
      instanceColor.copy(fpColor); // red for FP
    } else {
      instanceColor.copy(color); // class color for TP
    }
    
    mesh.setColorAt(i, instanceColor);
  }

  // ... rest of method
}
```

**Update buildClassBatches to accept TP/FP classification**:
```typescript
export function buildClassBatches(
  detections: Detection[],
  colors: ClassColors,
  diffMode: DiffMode = 'off',
  diffClassification?: Map<string, 'tp' | 'fp' | 'fn'> | Map<string, 'tp' | 'fp'>
): ClassBatches {
  // ... existing code, pass diffClassification through to createInstancedMesh
}
```

---

## Step 8: Wire Right Viewer to AGILE3D Detections

**File**: `src/app/features/main-demo/main-demo.component.ts`

**In sequence mode subscription**:
```typescript
this.frameStream.currentFrame$
  .pipe(takeUntil(this.destroy$))
  .subscribe((streamedFrame) => {
    if (!streamedFrame) return;

    try {
      // Update point geometry
      if (this.sharedPoints) {
        this.sceneData.updatePointsAttribute(this.sharedPoints, streamedFrame.points);
      }

      // Left viewer: GT only
      this.baselineDetections = streamedFrame.gt;

      // Right viewer: AGILE3D detections with TP/FP classification
      this.agile3dDetections = streamedFrame.agile?.det ?? [];
      this.agile3dClassification = streamedFrame.agile?.cls; // Map<string, 'tp'|'fp'>

      this.cdr.markForCheck();
    } catch (err) {
      console.error('[MainDemo] Frame processing error:', err);
    }
  });
```

**Add protected property for classification**:
```typescript
protected agile3dClassification?: Map<string, 'tp' | 'fp'>;
```

**Pass classification to DualViewer**:
```html
<app-dual-viewer
  [inputPoints]="sharedPoints"
  [baselineDetections]="baselineDetections"
  [agile3dDetections]="agile3dDetections"
  [agile3dDiffClassification]="agile3dClassification"
  [diffMode]="'all'"
  [showFps]="showFps"
/>
```

**Optional: Add internal toggle for comparison**:
```typescript
// Add a key listener or internal toggle to switch right pane:
private showBaselineDelayed = false;

// In subscription, use:
if (this.showBaselineDelayed && streamedFrame.baseline) {
  this.agile3dDetections = streamedFrame.baseline.det;
  this.agile3dClassification = streamedFrame.baseline.cls;
} else {
  this.agile3dDetections = streamedFrame.agile?.det ?? [];
  this.agile3dClassification = streamedFrame.agile?.cls;
}
```

---

## Step 9: Update Viewer Labels

**File**: `src/app/features/dual-viewer/dual-viewer.component.ts`

**Sequence mode label logic**:
```typescript
// In template, conditionally set labels:
<h2 id="baseline-viewer-label" class="viewer-label">
  {{ isSequenceMode ? 'Ground Truth' : 'DSVT-Voxel (Baseline)' }}
</h2>

<h2 id="agile3d-viewer-label" class="viewer-label">
  {{ isSequenceMode ? ('AGILE3D (' + activeBranchLabel + ')') : 'AGILE3D' }}
</h2>
```

**Add property and logic**:
```typescript
protected isSequenceMode = false;
protected activeBranchLabel = 'CP_Pillar_032';

// In ngOnInit or a service subscription, detect sequence mode and update label
// based on StateService or FrameStreamService config
```

**Optional: Add contention legend hook (hidden by default)**:
```typescript
protected showContentionLegend = false;
protected contentionText = '';

// Hook for later:
// this.stateService.contention$.subscribe(pct => {
//   if (pct < 20) this.contentionText = 'No Contention';
//   else if (pct < 60) this.contentionText = 'Light Contention';
//   else this.contentionText = 'Intense Contention';
// });
```

---

## Step 10: Robustness & Fallbacks

**In SequenceDataService**:
- If `urls.det` for requested branch is missing, log a warning and return empty detections array.

**In FrameStreamService**:
- If `baselineBranch` is not found in manifest, silently fall back to `DSVT_Voxel_030`; if still absent, skip baseline fetching.
- If `activeBranch` is not found, log and render only GT on right pane.

**In MainDemoComponent**:
- If `streamedFrame.agile?.det` is undefined or empty, show a small message on the right pane: "No detections available for this frame".

---

## Step 11: Quick Validation Tests

**Location**: `src/app/core/services/frame-stream/bev-iou.spec.ts` (or inline as a dev harness)

**Test cases**:
1. **Identical boxes**: `bevIoU(box, box) ≈ 1.0`
2. **Non-overlapping boxes**: `bevIoU(box1, box2) = 0`
3. **Partial overlap**: `bevIoU(box1, box2) ∈ (0, 1)`
4. **Rotated boxes**: Verify orientation handling (90° rotations should be distinct).
5. **classifyDetections**:
   - Box with IoU >= 0.5 to any GT → marked TP.
   - Box with IoU < 0.5 to all GTs → marked FP.
6. **Dimension mapping**: Visual sanity check that dx/dy swap aligns with rendered boxes.

---

## Step 12: Performance Pass

**Checklist**:
- [ ] Cache GT BEV corners per frame (compute once, reuse for all predictions).
- [ ] Use Float32Array for corner/polygon data internally.
- [ ] No unnecessary object allocations in `bevIoU` or `classifyDetections`.
- [ ] Looped playback of 45 frames: no memory growth over 5 minutes.
- [ ] Render loop maintains ~60 FPS; frame updates at 10 Hz.

---

## Step 13: Acceptance Criteria & Screenshot

**Conditions**:
- [ ] Data manifests (`src/assets/data/sequences/*/manifest.json`) contain `urls.det` for both `DSVT_Voxel_038` and `CP_Pillar_032` for all 45 frames in all three sequences.
- [ ] Playback at ~10 Hz with shared point cloud in both panes.
- [ ] Left pane labeled "Ground Truth" and displays GT boxes only.
- [ ] Right pane labeled "AGILE3D (CP_Pillar_032)" and displays predicted detections:
  - Filtered by score >= 0.7.
  - TP boxes in class colors (blue for vehicle, green for pedestrian/cyclist).
  - FP boxes in red.
  - IoU threshold = 0.5.
- [ ] Camera synchronized; FPS stable; no memory growth during loop.
- [ ] Optional: Right pane can be toggled to show baseline delayed detections to verify progressive delay effect (increased red FP boxes).
- [ ] Capture screenshot matching desired.png style (or a similar result showing TP in colors, FP in red).

---

## Step 14: Documentation & Commit

**Files to update**:
- Create or update `src/assets/data/sequences/README.md` with:
  - Explanation of branch IDs.
  - Score threshold: 0.7.
  - IoU threshold: 0.5.
  - Instructions for regenerating detection JSONs with `pkl2web_min.py`.
  - Example command for conversion.

**Commit message format** (per rule):
```
chore: 2025-11-06 15:21 Implement GT vs AGILE3D side-by-side with BEV IoU TP/FP coloring and delay sim hook; add det manifests for three sequences
```

---

## Summary of Changes

| Step | File(s) | Changes |
|------|---------|---------|
| 1–3 | `src/assets/data/sequences/*/` | Add per-frame `*.det.*.json` files; enrich manifests. |
| 4 | `sequence-data.service.ts` | Add `fetchDet()`, `mapDetToDetections()`. |
| 5 | `bev-iou.ts` (new) | IoU calc, Sutherland–Hodgman, classification. |
| 6 | `frame-stream.service.ts` | Handle both branches, progressive delay. |
| 7 | `bbox-instancing.ts` | FP color override (red). |
| 8 | `main-demo.component.ts` | Wire detections, pass classification. |
| 9 | `dual-viewer.component.ts` | Update labels, add legend hook. |
| 14 | `src/assets/data/sequences/README.md` | Document branches, thresholds, regen process. |

---

## Notes

- **Label map**: 1→vehicle, 2→pedestrian, 3→cyclist (from Pengcheng).
- **Coordinate frame**: Waymo uses LiDAR frame; yaw about +Z; renderer is Z-up. Existing code already handles dx/dy swap (length↔width).
- **Data storage**: Kept local under assets for this iteration; CDN/S3 deferred to future phase.
- **Progressive delay**: Implemented as optional hook; default playback shows AGILE3D current predictions without delay for the desired screenshot.

