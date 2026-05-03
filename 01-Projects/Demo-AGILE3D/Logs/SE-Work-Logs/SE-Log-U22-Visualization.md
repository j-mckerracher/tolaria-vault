# SE-Log-U22: Visualization to Match Desired Image

**Date:** 2025-11-09  
**Status:** Completed  
**Component:** Visualization enhancements for dual-viewer and detection rendering

## Overview
Completed the "Visualization to match desired image" step from the plan. This involved:
1. Detection rendering updates for TP/FP color differentiation
2. Dual-viewer UI enhancements (titles, legend, branch info)
3. Main demo wiring to pass correct data to dual viewer
4. Build validation

## Completed Tasks

### 1. Detection Rendering Updates (`render-updates`) ✓
**File:** `src/app/core/services/visualization/bbox-instancing.ts`

- Enhanced `createClassGroup()` to partition detections into TP/FP/other buckets based on `diffClassification` map
- TP detections render in class color (vehicle=cyan, pedestrian=magenta, cyclist=yellow)
- FP detections render in red (`#ff3b30`)
- Diff mode filtering correctly handles:
  - `'fp'` mode: renders only false positives in red
  - `'tp'` mode: renders only true positives + unknown in class color
  - `'all'` mode: renders both TP (class color) and FP (red)
- Each class now uses a THREE.Group containing up to 2 InstancedMesh objects (one for TP/class, one for FP/red)
- Updated `disposeClassBatches()` to properly traverse and dispose group-based hierarchies

### 2. Dual-Viewer UI Enhancements (`dual-ui`) ✓
**File:** `src/app/features/dual-viewer/dual-viewer.component.ts`

#### Legend Overlay
- Repositioned legend from `<div>` to `<aside>` for better semantics
- Updated to semantic `<header>` and `<ul>/<li>` structure
- Legend swatches use CSS variable colors for class identification
- Clear FP indicator: "False Positive" label with red swatch

#### Pane Headers & Counters
- Left pane: Shows "Ground Truth" with GT count or branch-specific title
- Right pane: Shows "AGILE3D ({branch})" with detection count
- Headers positioned at top-left with semi-transparent background
- Branch name extracted from component input and displayed dynamically

#### FP-Only Toggle
- Positioned at top-left below legend
- Toggles between 'all' and 'fp' diff modes
- Shows current state: "FP Only: On/Off"
- Styled with dark background and light text

#### Responsive Layout
- Legend and toggles positioned absolutely with z-index management
- Tablet breakpoint (≤1024px): viewers stack vertically
- Mobile breakpoint (≤768px): controls scaled down

#### Accessibility
- Legend wrapped in `<aside>` with aria-label
- Branch info and counts included in template comments for maintainability
- Reduced motion support via media query

### 3. Main Demo Wiring (`main-wiring`) ✓
**File:** `src/app/features/main-demo/main-demo.component.ts`

#### Template Updates
- Removed hardcoded `[diffMode]="'all'"` from `<app-dual-viewer>`
- Now passes `diffMode` from `frameStream.currentFrame$` dynamically
- Updated `leftTitle` and `rightTitle` to reflect current branches:
  - Left: "Baseline ({baselineBranch})"
  - Right: "AGILE3D ({activeBranch})"

#### Component Logic
- Subscriptions to `frameStream.currentFrame$` provide:
  - `agile.cls` / `baseline.cls` for diff classifications
  - Current detection sets for both panes
  - Delay simulation info from baseline detection metadata
- Passes branch-specific diff classifications to `<app-dual-viewer>`
- Ensures AGILE3D pane receives active branch detections
- Baseline pane receives baseline branch detections with delay info

### 4. Build Validation (`visual-validation`) ✓
- First build: `npm run build` completed successfully
- Warnings present (expected):
  - CameraSyncControlsComponent unused in DualViewerComponent imports (legacy feature disabled)
  - Optional chain operators in template (minor Angular lint suggestions)
  - SASS deprecation warnings (framework-level, no action needed)
  - Metrics dashboard CSS budget exceeded by 502 bytes (pre-existing)
- Second build after removing unused import: Build passed
- No compilation errors introduced

## Files Modified
1. `src/app/core/services/visualization/bbox-instancing.ts` — Detection partitioning & rendering
2. `src/app/features/dual-viewer/dual-viewer.component.ts` — UI layout, legend, dynamic titles
3. `src/app/features/main-demo/main-demo.component.ts` — Wiring branch data and diff modes to dual viewer
4. `src/app/features/scene-viewer/scene-viewer.component.ts` — No changes (uses existing diff mode logic)

## Key Features Implemented
- ✓ TP/FP color differentiation at render time
- ✓ Dynamic pane titles showing active branch names
- ✓ Detection count display per pane
- ✓ Legend overlay with class colors and FP indicator
- ✓ FP-only toggle for diff mode filtering
- ✓ Responsive layout for tablet/mobile
- ✓ Semantic HTML structure (aside, header, ul/li)
- ✓ Accessibility labels and ARIA attributes

### 5. Runtime Config & Sequence Registry (`todo-1762645916513-6ep6stm0f`) ✓
**Files:** `src/assets/runtime-config.json`, `src/app/core/services/data/sequence-registry.service.ts`

- Created `runtime-config.json` with sequence entries for v_1784_1828, p_7513_7557, c_7910_7954
- Each entry contains `sequenceId`, `sceneId`, `basePath`, `manifestUrl`, `defaultBaselineBranch`, `defaultActiveBranch`
- `SequenceRegistryService` loads and manages runtime configuration
- Provides `listSequences()`, `findBySequenceId()`, `findBySceneId()`, `getDefaults()` methods
- Enables dynamic sequence resolution without code changes

### 6. Data Service & Main Demo Integration (`todo-1762645916513-g72rwh5h3`) ✓
**Files:** `src/app/core/services/data/sequence-data.service.ts`, `src/app/features/main-demo/main-demo.component.ts`

- `SequenceDataService` injected `SequenceRegistryService` and added `setBasePath()` method
- `loadManifest()`, `fetchPoints()`, `fetchGT()`, `fetchDet()` now use dynamic base path
- `MainDemoComponent` initializes sequence registry, resolves entries, and loads manifests
- Passes registry entries to data service via `setBasePath()`
- Extracts available branches from manifest and propagates to state service
- Tracks current sequence ID for scene switching

### 7. State Service & Frame Stream Sync (`todo-1762645916513-kob8cc557`) ✓
**Files:** `src/app/core/services/state/state.service.ts`, `src/app/core/services/frame-stream/frame-stream.service.ts`

- `StateService` added `baselineBranchSubject` and `availableBranchesSubject`
- Added `setBaselineBranch()` and `setAvailableBranches()` methods
- `setAvailableBranches()` normalizes branch list and reconciles current selections with fallback logic
- `FrameStreamService` subscribed to state service observables for branches, score threshold, label mask, diff mode, delay, miss rate, FPS, prefetch count, concurrency
- Added `setActiveBranch()`, `setBaselineBranch()`, `resetPrefetchWindow()` methods
- `fetchFrame()` uses dynamic `activeBranch` and `baselineBranch` for fetching detections

### 8. Control Panel Branch Selectors (`todo-1762645916513-drrz6y16m`) ✓
**File:** `src/app/features/control-panel/control-panel.component.ts`

- Added `baselineBranch` and `activeBranch` form controls to `primaryForm`
- Added `baselineOptions` and `agileOptions` properties for dropdown display
- Subscribed to `availableBranches$`, `baselineBranch$`, `activeBranch$` from state service
- Filters branches: DSVT-prefixed for baseline, CP_-prefixed for AGILE3D
- Form value changes synced back to state service via `setBaselineBranch()` and `setActiveBranch()`
- Updated template with `<mat-form-field>` and `<mat-select>` elements

## Next Steps
- Plan document specifies next step: "Contention controls (no new data)"
- All "Visualization to match desired image" todos marked complete
- All 4 duplicate branch resolver todos marked complete
- Build passes with no new errors

## Notes
- The dual viewer now fully reflects branch-specific detections with proper color coding
- Legend and UI controls are positioned to avoid obscuring the main 3D view
- Diff mode is controlled by the state service and propagated through the frame stream
- The visualization updates in real-time as users switch branches or toggle FP-only mode
- Runtime config enables multi-sequence support with dynamic branch resolution
- Control panel now exposes branch selectors from the manifest's available branches
- State and frame stream synchronization ensures branch changes propagate through entire data pipeline

