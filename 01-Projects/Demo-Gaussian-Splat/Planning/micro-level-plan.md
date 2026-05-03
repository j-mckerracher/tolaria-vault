# Micro-Level Plan (Demo Gaussian Splat)

## Restated Inputs (Macro/Meso Summary, Constraints, NFRs, Standards)
- Goal: Build {Project_Name} as an interactive web demo for {Reference_Paper} showing sparse 3D Gaussian primitives are more bandwidth-efficient than dense voxel methods for collaborative perception, and communicate the message within ~10 seconds.
- Users/Stakeholders: {Stakeholder_Group_A} (paper authors), {Stakeholder_Group_B} (lab PI), {Primary_Audience} (funding reviewers).
- Core capabilities: split-screen comparison (fixed 50/50); independent orbit/zoom/pan controls per view; procedural scene; dense voxel rendering; Gaussian shader faithful to Equation 7; HUD with bandwidth + accuracy; summary text; on-screen citation link; logging with UI toggle.
- Visual style: dark-mode technical dashboard, background #121212, bright semantic colors for Gaussians, muted translucent voxels, neon accents.
- Constraints: Angular + 3D engine; Vercel free tier; self-contained data (no external APIs/assets); desktop/laptop focus; mobile best-effort; low traffic.
- NFRs: best-effort performance with target 60 fps on a standard laptop; 90% uptime target; observability with configurable levels and UI log panel; security/privacy/accessibility/i18n not required for MVP; browser support Chrome/Edge/Firefox/Safari.
- Standards: TypeScript strict typing, modular components/services, log level gating, no backend services.

## Open Questions and Blocked Decisions
### Requirements
1. Final values for {Project_Name}, {Primary_Audience}, and {Stakeholder_Group_*} labels.
2. {Reference_Paper} exact title and citation URL for on-screen link.
3. Baseline and ours mIoU numbers to display (delta is +1.9 mIoU per macro plan).
4. Final summary copy for the text section (draft vs approved copy).
5. Minimum acceptable mobile behavior (view-only vs limited touch controls).

### NFRs
1. Performance acceptance threshold for best-effort (e.g., acceptable minimum FPS range on target hardware).

### Constraints
1. Confirm no analytics or telemetry beyond in-app logging.

### Dependencies
1. Confirm Equation 7 implementation details and parameter ranges from the paper.

### Risks
1. Safari/WebGL2 performance and shader precision.

### Provisional Assumptions (validate before implementation)
- Assume {Project_Name} = "Demo Gaussian Splat"; validate with stakeholder sign-off.
- Assume citation URL will be provided and stable; validate by checking the final paper DOI or lab page.
- Assume baseline/ours mIoU numbers will be extracted from the paper; validate with the authors.
- Assume mobile is view-only with disabled orbit controls below 768px width; validate with stakeholder.
- Assume log levels are error/warn/info/debug; validate with stakeholder.

---

## 1. Technology Stack and Version Pins
- Languages: TypeScript (5.5+), HTML, SCSS, GLSL (WebGL2, #version 300 es).
- Framework: Angular 18.x (target), Angular CLI 18.x, RxJS 7.8.x.
- 3D Engine: Three.js r160+ (target), @types/three pinned to the same release.
- Tooling: Node.js 20.x LTS, npm 10.x, ESLint (angular-eslint), Prettier, optional Stylelint.
- Testing: Angular CLI + Karma/Jasmine (default), with optional Playwright for e2e.
- Hosting: Vercel static build output.

Alternatives (where not mandated)
1. 3D engine: Babylon.js (more tooling, heavier bundle), Raw WebGL2 (max control, higher dev cost). Selection criteria: shader flexibility, bundle size, team familiarity.
2. State management: RxJS services (lightweight) vs NgRx (structured but heavier). Selection criteria: app size and state complexity.
3. Test runner: Jest (faster, extra config) vs Karma (default). Selection criteria: team preference and CI speed.

Deprecation/upgrade policy
- Pin exact versions in package.json and package-lock.json.
- Update patch/minor monthly; major upgrades quarterly after compatibility testing.
- Maintain WebGL2 requirement; show a clear fallback message when unsupported.

## 2. Repository Structure and Conventions
Proposed top-level structure
- / (repo root)
  - angular.json
  - package.json
  - package-lock.json
  - README.md
  - .editorconfig
  - .eslintrc.json
  - .prettierrc
  - /src
    - /app
      - /components
        - /split-view
        - /hud
        - /summary
        - /log-panel
      - /rendering
        - render-coordinator.service.ts
        - voxel-renderer.ts
        - gaussian-renderer.ts
        - view-controller.service.ts
      - /scene
        - scene-generator.service.ts
        - scene-models.ts
      - /services
        - telemetry.service.ts
        - logger.service.ts
        - config.service.ts
      - /models
        - types.ts
      - /shaders
        - gaussian.vert
        - gaussian.frag
        - voxel.vert
        - voxel.frag
    - /assets
    - /environments
      - environment.ts
      - environment.prod.ts
  - /docs (optional)
  - /.github/workflows (CI)

Conventions
- File naming: kebab-case; class names PascalCase; functions/vars camelCase.
- TypeScript strict mode enabled; no implicit any; avoid type assertions.
- CSS/SCSS: BEM-style class names for components.
- Commit messages: Conventional Commits (feat/fix/docs/chore/test).
- Branch strategy: trunk-based with short-lived feature branches.
- Code ownership: CODEOWNERS for /src/app/rendering and /src/app/scene.

## 3. Build, Dependency, and Environment Setup
- Package manager: npm with package-lock.json (authoritative). Use npm ci in CI.
- Build targets:
  - Dev: ng serve (hot reload)
  - Prod: ng build --configuration production
- Reproducible builds: lockfile + Node version file (.nvmrc or .tool-versions) + npm ci.
- Local dev prerequisites: Node 20.x, npm 10.x, Git, WebGL2-capable browser.
- Bootstrap steps:
  1) npm install
  2) npm run start
  3) open http://localhost:4200
- Cross-platform: avoid OS-specific paths; no native deps.
- Standard commands:
  - npm run start
  - npm run build
  - npm run test
  - npm run lint
  - npm run format

## 4. Detailed Module/Component Specifications
### 4.1 UI Shell (AppComponent + Layout)
- Purpose: compose the split view, HUD, summary text, citation link, and log panel toggle.
- Inputs: TelemetryState, LogEntry[] (from services).
- Outputs: UI events for log panel toggle and debug options.
- Key behaviors: fixed 50/50 split; no draggable divider (deferred).

### 4.2 SplitViewComponent
- Purpose: host left/right render targets and enforce fixed split ratio.
- Inputs: splitRatio (0.5), container size.
- Outputs: DOM element refs for left/right canvas containers.
- Error handling: if container sizes are 0 (hidden), pause render loop and log warn.

### 4.3 ViewControllerService (per panel)
- Purpose: create camera + OrbitControls tied to a specific DOM element.
- Inputs: DOM container, camera config.
- Outputs: ViewState updates via RxJS BehaviorSubject.
- Interface:
  - init(panelId: 'left' | 'right', dom: HTMLElement, config: CameraConfig): void
  - getState(panelId): Observable<ViewState>
- Concurrency: single-threaded; events processed in UI thread.

### 4.4 SceneGeneratorService
- Purpose: procedurally generate road, ego vehicle, obstacle, and semantic labels.
- Inputs: SceneConfig (seed, counts, sizes).
- Outputs: SceneData { voxels, gaussians, semantics }.
- Determinism: seeded RNG for repeatable outputs.
- Pseudocode:
  ```ts
  generateScene(config): SceneData {
    const rng = mulberry32(config.seed);
    const road = generateRoadVoxels(config, rng);
    const car = generateVehicleGaussians(config, rng);
    const obstacle = generateObstacleGaussians(config, rng);
    return { voxels: merge(road, car, obstacle), gaussians: [..] };
  }
  ```

### 4.5 VoxelRenderer
- Purpose: render dense voxel grid with semi-transparent cluttered look.
- Inputs: VoxelGrid, left camera, render context.
- Implementation: Three.js InstancedMesh of cubes with per-instance color/opacity.
- Interface:
  - init(scene: THREE.Scene): void
  - setVoxels(grid: VoxelGrid): void
  - render(camera: THREE.Camera, viewport: Viewport): void

### 4.6 GaussianRenderer (Equation 7)
- Purpose: render sparse Gaussian primitives faithfully to Equation 7.
- Inputs: GaussianPrimitive[], right camera, render context.
- Implementation: InstancedMesh of low-poly spheres with custom ShaderMaterial.
- Per-instance attributes: mean (vec3), scale (vec3), rotation (quat), opacity (float), semanticColor (vec3).
- Shader sketch (fragment):
  ```glsl
  // d = local position in ellipsoid space
  // Sigma = R * diag(scale^2) * R^T
  // w = exp(-0.5 * d^T * inv(Sigma) * d)
  // color = semanticColor * opacity * w
  // output with premultiplied alpha
  ```
- Error handling: if shader compilation fails, log error and show fallback text overlay.

### 4.7 RenderCoordinatorService
- Purpose: orchestrate render loop, viewports, resizing, and telemetry updates.
- Inputs: scenes, cameras, renderers, ViewState streams.
- Outputs: frame renders + Telemetry updates.
- Implementation: single WebGLRenderer with scissor/viewport for left/right.
- Pseudocode:
  ```ts
  start() { this.running = true; requestAnimationFrame(this.tick); }
  tick = (t) => {
    if (!this.running) return;
    this.updateTelemetry(t);
    this.renderPanel('left', voxelScene, leftCamera, leftViewport);
    this.renderPanel('right', gaussianScene, rightCamera, rightViewport);
    requestAnimationFrame(this.tick);
  };
  ```

### 4.8 TelemetryService (Bandwidth + Accuracy HUD)
- Purpose: compute bandwidth/accuracy HUD values responsive to interaction.
- Inputs: visibleVoxelCount, visibleGaussianCount, FPS.
- Outputs: TelemetryState stream.
- Logic:
  - baselineBandwidthPct = 100
  - gaussianBandwidthPct = baseGaussianPct * clamp(visibleGaussianCount / totalGaussians, 0.2, 1.0)
  - mIoU values from config (baseline, ours, delta)

### 4.9 LoggerService + Log Panel
- Purpose: structured logging with level gating and UI display.
- Ring buffer size: 200 entries (configurable).
- Interface:
  - log(level, message, meta?)
  - setLevel(level)
  - entries$: Observable<LogEntry[]>

### 4.10 ConfigService
- Purpose: centralize constants (colors, counts, split ratio, HUD values).
- Precedence: environment.ts overrides defaults.
- No secrets; values are safe for client-side exposure.

Decided vs deferred
- Decided: Angular + Three.js, fixed 50/50 split, instanced rendering, no backend.
- Deferred: draggable slider, optional analytics, additional scenes or assets.

## 5. Data Model and Persistence
Entities (TypeScript interfaces)
```ts
type SemanticClass = 'road' | 'vehicle' | 'obstacle' | 'vegetation' | 'unknown';
interface Voxel { position: Vec3; size: number; opacity: number; semantic: SemanticClass; }
interface VoxelGrid { dims: [number, number, number]; voxels: Voxel[]; }
interface GaussianPrimitive { mean: Vec3; scale: Vec3; rotation: Quat; opacity: number; semantic: SemanticClass; }
interface SceneData { voxels: VoxelGrid; gaussians: GaussianPrimitive[]; }
interface ViewState { cameraPos: Vec3; target: Vec3; fov: number; near: number; far: number; }
interface TelemetryState { bandwidthBaselinePct: number; bandwidthGaussianPct: number; baselineMiou: number; oursMiou: number; deltaMiou: number; fps: number; visibleVoxelCount: number; visibleGaussianCount: number; }
interface LogEntry { ts: string; level: LogLevel; component: string; message: string; meta?: Record<string, unknown>; }
```
Persistence
- No database; all data is in-memory.
- Log retention: fixed ring buffer; oldest entries dropped.
Migrations/rollbacks
- Not applicable (no persistent storage).
Caching
- Cache generated geometry and instance buffers; regenerate only on config changes.

## 6. API and Message Contracts
External APIs
- None (client-only).

Internal events/contracts
- CameraUpdate: { panel: 'left' | 'right', viewState: ViewState }
- TelemetryUpdate: TelemetryState
- LogEntry: { ts, level, component, message, meta }
- UI events: LogPanelToggle { open: boolean }

Versioning/compatibility
- Internal only; maintain backward compatibility within the app when refactoring by keeping interface shapes stable.

Rate limits/pagination/idempotency
- Not applicable; for UI updates, throttle to animation frame.

## 7. Configuration and Secrets
Configuration keys (environment.ts)
- splitRatio: 0.5
- voxelGridDims: [64, 64, 32]
- gaussianCountTarget: 3000
- baseGaussianBandwidthPct: 34.6
- baselineMiou: TBD
- oursMiou: TBD
- logLevel: 'info'
- showFps: true
- citationUrl: TBD

Precedence
- environment.ts -> defaults in ConfigService.

Secrets
- None. All values are non-sensitive and safe for client exposure.

## 8. Observability and Operational Readiness
Logging schema
- fields: ts, level, component, message, meta, sessionId, frameId
- levels: error, warn, info, debug
- sinks: console + UI log panel

Operational readiness
- WebGL2 capability check at startup; show fallback message if unsupported.
- FPS sampling every N frames for HUD display.
- Minimal global error handler to log fatal errors (no silent catches).

## 10. Testing Strategy and Plan
Test pyramid
- Unit: SceneGenerator, TelemetryService, LoggerService, ConfigService, ViewController math.
- Integration: RenderCoordinator viewport/scissor setup, split view sizing, shader compile smoke test.
- E2E (optional): page loads, split view visible, HUD text shows, log panel toggles.
- Performance: manual FPS check on target browsers.

Coverage targets
- Unit test coverage >= 70% for non-rendering logic.

Test data
- Seeded RNG for deterministic scene generation.

Flakiness controls
- Disable rAF loops in unit tests; mock requestAnimationFrame.

Sample test cases
1. SceneGenerator returns expected counts for fixed seed.
2. Telemetry computes gaussian bandwidth pct within expected range.
3. Logger ring buffer drops oldest entries at capacity.
4. RenderCoordinator sets correct scissor rects for 50/50 split.
5. WebGL2 unsupported path shows fallback message.

## 12. Work Breakdown Structure (WBS)
Epics and tasks (with dependencies)
1. Project scaffolding and CI
   - Create Angular app, install Three.js, set lint/format/test.
   - Add Vercel config and CI workflow.
   - Exit: app builds and serves locally.
2. Data models + config
   - Define types, config service, environment defaults.
   - Exit: types compile and config is injectable.
3. Scene generator
   - Implement procedural road/vehicle/obstacle generators.
   - Exit: deterministic outputs for fixed seed.
4. Rendering core
   - RenderCoordinator + ViewController + split view.
   - VoxelRenderer with instancing.
   - GaussianRenderer with Equation 7 shader.
   - Exit: both views render with independent controls.
5. UI shell
   - HUD, summary text, citation link, log panel UI.
   - Exit: UI renders with correct values and toggle.
6. Telemetry + logging
   - Telemetry calculations and FPS sampling.
   - LoggerService + UI integration.
   - Exit: HUD updates and logs visible.
7. Performance tuning + cross-browser validation
   - Tune counts and shader; test Chrome/Edge/Firefox/Safari.
   - Exit: best-effort FPS documented.
8. Release readiness
   - Production build, deploy to Vercel, smoke test.
   - Exit: accessible demo URL.

Parallelization
- UI shell (Epic 5) can proceed in parallel with Scene Generator (Epic 3) once types/config are ready.
- Telemetry/logging (Epic 6) can proceed after rendering core interfaces are defined.

Critical path
- Scaffolding -> Rendering core -> UI shell/HUD -> Performance validation -> Release.

## 13. Runbooks and Developer Onboarding
Local setup
1. Install Node 20.x and npm 10.x.
2. Clone repo and run npm install.
3. Run npm run start and open http://localhost:4200.

Common commands
- npm run start | build | test | lint | format

Debugging tips
- Use the log panel to inspect renderer state.
- Enable debug log level for shader errors.
- Use browser WebGL inspector and FPS overlay if needed.

Known pitfalls
- WebGL2 required; Safari may require "Experimental Features" enabled.
- High Gaussian counts can drop FPS; use config presets.

## 14. Risks, Assumptions, and Open Questions (Micro-Level)
Risks
- Shader performance on Safari or low-end GPUs; mitigate via quality presets.
- Incorrect Equation 7 interpretation; mitigate via validation against paper.
- Visual clutter if voxel count too high; mitigate via adjustable counts.

Assumptions
- No backend or analytics.
- Fixed split remains acceptable for MVP.
- Baseline/ours mIoU values will be provided.

Open questions
- Final naming/citation details and mobile behavior (see top section).

## 15. Definition of Done (Micro Level)
- App builds in production mode without errors.
- Both views render with independent controls and fixed 50/50 split.
- Gaussian shader implements Equation 7 and matches semantic coloring.
- HUD shows bandwidth (100% vs ~34.6%) and mIoU values.
- Log panel toggle works; logs include level and component.
- WebGL2 unsupported case shows a clear fallback message.
- Unit tests pass and coverage target met.
- Cross-browser smoke test completed (Chrome, Edge, Firefox, Safari).
- Vercel deployment succeeds and URL validated.

## 16. Appendices (optional)
Template: LogLevel enum
```ts
type LogLevel = 'error' | 'warn' | 'info' | 'debug';
```

Template: Environment config
```ts
export const environment = {
  production: false,
  splitRatio: 0.5,
  voxelGridDims: [64, 64, 32],
  gaussianCountTarget: 3000,
  baseGaussianBandwidthPct: 34.6,
  baselineMiou: 0,
  oursMiou: 0,
  logLevel: 'info',
  citationUrl: ''
};
```

---

## Summary and Next Steps
- Key decisions: client-only Angular + Three.js, fixed split, instanced voxel/gaussian renderers, no backend, Vercel hosting.
- Next steps: confirm open questions (names, citation URL, mIoU values, mobile behavior), then proceed with scaffolding and renderer implementation.
