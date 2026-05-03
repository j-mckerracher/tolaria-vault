---
tags: [planning, work-decomposition]
project: "[[C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\Demo-Gaussian-Splat\]]"
plan_title: "Micro-Level Plan (Demo Gaussian Splat)"
context_budget_tokens: 6000
created: "2026-02-07"
source_plan: "[[C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\Demo-Gaussian-Splat\Planning\micro-level-plan.md]]"
---

# Work Decomposition — Gaussian Splat Demo

## Overview
- Project: [[C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\Demo-Gaussian-Splat\Demo Gaussian Splat]]
- Source plan: [[C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\Demo-Gaussian-Splat\Planning\micro-level-plan.md]]
- Context budget (tokens): 6000

## Units

### Unit U01: Dependency pins and lint baseline
- Goal: Pin framework/runtime versions and establish Node + lint configuration.
- Scope:
  - Update package.json/package-lock with exact Angular 18, RxJS 7.8, Three r160, and @types/three versions.
  - Align angular.json and ESLint with strict TypeScript settings; add Node 20.x version file.
- Traceability:
  - Micro sections: ["1. Technology Stack and Version Pins", "2. Repository Structure and Conventions", "3. Build, Dependency, and Environment Setup", "12. Work Breakdown Structure"]
- Dependencies: []
- Inputs required: []
- Files to read: `package.json`, `angular.json`, `.eslintrc.json`
- Files to edit or create: `package.json`, `package-lock.json`, `angular.json`, `.eslintrc.json`, `.nvmrc`
- Acceptance criteria:
  - [ ] Build/lint scripts reference the pinned versions and strict TypeScript mode.
  - [ ] Node version file specifies 20.x LTS.
- Test plan:
  - Unit: none.
  - Manual: run `npm run build` and `npm run lint`.
- Risks/assumptions:
  - Assumes an Angular workspace already exists or is scaffolded separately.
- Estimates:
  - est_impl_tokens: 1400
  - max_changes: files=5, loc=250

### Unit U02: Formatting and editor config
- Goal: Establish formatting rules and editor consistency.
- Scope:
  - Add Prettier configuration aligned with repo conventions.
  - Add .editorconfig for consistent line endings and indentation.
- Traceability:
  - Micro sections: ["1. Technology Stack and Version Pins", "2. Repository Structure and Conventions"]
- Dependencies: [U01]
- Inputs required: []
- Files to read: `.eslintrc.json`
- Files to edit or create: `.prettierrc`, `.editorconfig`
- Acceptance criteria:
  - [ ] Prettier config exists and aligns with ESLint formatting expectations.
  - [ ] .editorconfig present with consistent whitespace rules.
- Test plan:
  - Unit: none.
  - Manual: run `npm run format`.
- Risks/assumptions:
  - Formatting rules remain stable for MVP.
- Estimates:
  - est_impl_tokens: 700
  - max_changes: files=2, loc=120

### Unit U03: Data models and configuration service
- Goal: Define core types and centralized configuration with environment overrides.
- Scope:
  - Add `types.ts` interfaces for voxels, gaussians, telemetry, and logs.
  - Implement ConfigService defaults with environment overrides.
- Traceability:
  - Micro sections: ["5. Data Model and Persistence", "7. Configuration and Secrets", "4.10 ConfigService", "12. Work Breakdown Structure"]
- Dependencies: [U01]
- Inputs required: [baselineMiou, oursMiou, citationUrl]
- Files to read: `src/environments/environment*.ts`
- Files to edit or create: `src/app/models/types.ts`, `src/app/services/config.service.ts`, `src/environments/environment.ts`, `src/environments/environment.prod.ts`
- Acceptance criteria:
  - [ ] TypeScript compiles without type assertions under strict mode.
  - [ ] Environment values override ConfigService defaults at runtime.
- Test plan:
  - Unit: `src/app/services/config.service.spec.ts` (override precedence).
  - Manual: inject ConfigService and verify values in dev mode.
- Risks/assumptions:
  - mIoU and citation values may be placeholders until finalized.
- Estimates:
  - est_impl_tokens: 1200
  - max_changes: files=4, loc=250

### Unit U04: Scene generator (procedural)
- Goal: Generate deterministic scene data from a seeded config.
- Scope:
  - Implement seeded RNG and procedural road/vehicle/obstacle generation.
  - Output SceneData with voxels and gaussians for a given seed.
- Traceability:
  - Micro sections: ["4.4 SceneGeneratorService", "5. Data Model and Persistence", "10. Testing Strategy and Plan", "12. Work Breakdown Structure"]
- Dependencies: [U03]
- Inputs required: [sceneSeed, voxelGridDims, gaussianCountTarget]
- Files to read: `src/app/scene/scene-models.ts`, `src/app/models/types.ts`
- Files to edit or create: `src/app/scene/scene-generator.service.ts`, `src/app/scene/scene-models.ts`, `src/app/scene/scene-generator.service.spec.ts`
- Acceptance criteria:
  - [ ] Same seed yields identical counts and positions.
  - [ ] Output respects configured voxel dims and gaussian target.
- Test plan:
  - Unit: `scene-generator.service.spec.ts` deterministic counts.
  - Manual: log a generated SceneData snapshot.
- Risks/assumptions:
  - Procedural density is sufficient for visual comparison.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=3, loc=350

### Unit U05: Split view component + view controller service
- Goal: Provide fixed 50/50 split layout and independent camera controls.
- Scope:
  - Build SplitViewComponent with left/right containers and resize handling.
  - Implement ViewControllerService with per-panel OrbitControls and ViewState stream.
- Traceability:
  - Micro sections: ["4.2 SplitViewComponent", "4.3 ViewControllerService", "4.1 UI Shell", "10. Testing Strategy and Plan"]
- Dependencies: [U03]
- Inputs required: [splitRatio, cameraConfig]
- Files to read: `src/app/components/**`, `src/app/rendering/**`
- Files to edit or create: `src/app/components/split-view/split-view.component.ts`, `src/app/components/split-view/split-view.component.html`, `src/app/components/split-view/split-view.component.scss`, `src/app/components/split-view/split-view.component.spec.ts`, `src/app/rendering/view-controller.service.ts`
- Acceptance criteria:
  - [ ] Split view maintains fixed 50/50 layout on resize.
  - [ ] Each panel supports independent orbit/zoom/pan controls.
- Test plan:
  - Unit: add ViewControllerService tests in a separate UoW if needed.
  - Manual: resize window and verify controls are independent.
- Risks/assumptions:
  - OrbitControls API matches pinned Three.js version.
- Estimates:
  - est_impl_tokens: 1600
  - max_changes: files=5, loc=350

### Unit U06: Render coordinator service
- Goal: Orchestrate render loop with scissor/viewport rendering for both panels.
- Scope:
  - Implement RenderCoordinatorService with shared WebGLRenderer and rAF loop.
  - Wire resize/viewport calculations and telemetry hooks.
- Traceability:
  - Micro sections: ["4.7 RenderCoordinatorService", "8. Observability and Operational Readiness", "10. Testing Strategy and Plan"]
- Dependencies: [U05]
- Inputs required: [viewport sizing rules]
- Files to read: `src/app/rendering/**`
- Files to edit or create: `src/app/rendering/render-coordinator.service.ts`, `src/app/rendering/render-coordinator.service.spec.ts`
- Acceptance criteria:
  - [ ] Scissor rectangles render left/right scenes in correct bounds.
  - [ ] Render loop pauses when container dimensions are zero.
- Test plan:
  - Unit: `render-coordinator.service.spec.ts` scissor math.
  - Manual: observe resize behavior and FPS.
- Risks/assumptions:
  - Single renderer supports both scenes without context loss.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=2, loc=300

### Unit U07: Voxel renderer
- Goal: Render dense voxel grid with instanced cubes and semantic colors.
- Scope:
  - Implement VoxelRenderer using InstancedMesh with per-instance color/opacity.
  - Provide setVoxels and render methods for coordinator integration.
- Traceability:
  - Micro sections: ["4.5 VoxelRenderer", "4.7 RenderCoordinatorService"]
- Dependencies: [U04, U06]
- Inputs required: [VoxelGrid]
- Files to read: `src/app/rendering/voxel-renderer.ts`, `src/app/models/types.ts`
- Files to edit or create: `src/app/rendering/voxel-renderer.ts`, `src/app/rendering/voxel-renderer.spec.ts`
- Acceptance criteria:
  - [ ] Voxels render with semi-transparent cluttered appearance.
  - [ ] Updates reuse buffers when voxel count is unchanged.
- Test plan:
  - Unit: `voxel-renderer.spec.ts` buffer sizing and update.
  - Manual: visual check of opacity and color mapping.
- Risks/assumptions:
  - Instance counts remain within GPU limits.
- Estimates:
  - est_impl_tokens: 1400
  - max_changes: files=2, loc=300

### Unit U08: Gaussian renderer + Equation 7 shader
- Goal: Render sparse Gaussian primitives with custom shader implementing Equation 7.
- Scope:
  - Implement GaussianRenderer with instanced spheres and per-instance attributes.
  - Add GLSL vertex/fragment shaders with premultiplied alpha.
- Traceability:
  - Micro sections: ["4.6 GaussianRenderer (Equation 7)", "8. Observability and Operational Readiness"]
- Dependencies: [U04, U06]
- Inputs required: [GaussianPrimitive[], equation7Params]
- Files to read: `src/app/rendering/gaussian-renderer.ts`, `src/app/shaders/*`
- Files to edit or create: `src/app/rendering/gaussian-renderer.ts`, `src/app/shaders/gaussian.vert`, `src/app/shaders/gaussian.frag`, `src/app/rendering/gaussian-renderer.spec.ts`
- Acceptance criteria:
  - [ ] Shaders compile under WebGL2 with #version 300 es.
  - [ ] Renderer surfaces shader errors and avoids silent failures.
- Test plan:
  - Unit: `gaussian-renderer.spec.ts` material setup smoke test.
  - Manual: verify Gaussian falloff and semantic coloring.
- Risks/assumptions:
  - Equation 7 parameters are validated against the paper.
- Estimates:
  - est_impl_tokens: 1800
  - max_changes: files=4, loc=350

### Unit U09: Telemetry service + HUD component
- Goal: Compute bandwidth/accuracy telemetry and display it in the HUD.
- Scope:
  - Implement TelemetryService math (bandwidth, mIoU, FPS sampling).
  - Build HUD component to render TelemetryState.
- Traceability:
  - Micro sections: ["4.8 TelemetryService", "4.1 UI Shell", "10. Testing Strategy and Plan"]
- Dependencies: [U03, U06]
- Inputs required: [baselineMiou, oursMiou, baseGaussianBandwidthPct]
- Files to read: `src/app/services/telemetry.service.ts`, `src/app/components/hud/*`
- Files to edit or create: `src/app/services/telemetry.service.ts`, `src/app/services/telemetry.service.spec.ts`, `src/app/components/hud/hud.component.ts`, `src/app/components/hud/hud.component.html`, `src/app/components/hud/hud.component.scss`
- Acceptance criteria:
  - [ ] HUD shows baseline vs Gaussian bandwidth and mIoU values.
  - [ ] FPS updates at configured sampling interval.
- Test plan:
  - Unit: `telemetry.service.spec.ts` clamp and percentage math.
  - Manual: interact with views and confirm HUD updates.
- Risks/assumptions:
  - Telemetry inputs are available from RenderCoordinator.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=5, loc=300

### Unit U10: Logger service + log panel UI
- Goal: Provide level-gated logging with a UI log panel.
- Scope:
  - Implement LoggerService with ring buffer and log-level gating.
  - Build LogPanelComponent for viewing entries and toggling visibility.
- Traceability:
  - Micro sections: ["4.9 LoggerService + Log Panel", "8. Observability and Operational Readiness", "10. Testing Strategy and Plan"]
- Dependencies: [U03]
- Inputs required: [logLevel]
- Files to read: `src/app/services/logger.service.ts`, `src/app/components/log-panel/*`
- Files to edit or create: `src/app/services/logger.service.ts`, `src/app/services/logger.service.spec.ts`, `src/app/components/log-panel/log-panel.component.ts`, `src/app/components/log-panel/log-panel.component.html`, `src/app/components/log-panel/log-panel.component.scss`
- Acceptance criteria:
  - [ ] Ring buffer caps entries at configured size and drops oldest.
  - [ ] Log level filter hides lower-priority messages.
- Test plan:
  - Unit: `logger.service.spec.ts` ring buffer + level gating.
  - Manual: toggle panel and confirm live updates.
- Risks/assumptions:
  - UI rendering remains responsive at 200 entries.
- Estimates:
  - est_impl_tokens: 1300
  - max_changes: files=5, loc=300

### Unit U11: Summary component + citation link
- Goal: Present summary text and citation link in a dedicated component.
- Scope:
  - Build SummaryComponent with approved copy and link styling.
  - Bind citation URL from config or inputs.
- Traceability:
  - Micro sections: ["4.1 UI Shell", "12. Work Breakdown Structure"]
- Dependencies: [U03]
- Inputs required: [summaryCopy, citationUrl, projectName]
- Files to read: `src/app/components/summary/*`
- Files to edit or create: `src/app/components/summary/summary.component.ts`, `src/app/components/summary/summary.component.html`, `src/app/components/summary/summary.component.scss`, `src/app/components/summary/summary.component.spec.ts`
- Acceptance criteria:
  - [ ] Summary renders approved copy with citation link.
  - [ ] Citation link opens the configured URL.
- Test plan:
  - Unit: `summary.component.spec.ts` verifies text and link.
  - Manual: confirm dark-mode styling.
- Risks/assumptions:
  - Final copy is provided before release.
- Estimates:
  - est_impl_tokens: 1000
  - max_changes: files=4, loc=200

### Unit U12: App shell layout integration
- Goal: Compose split view, HUD, summary, and log panel in the app shell.
- Scope:
  - Update AppComponent template and styles for fixed 50/50 layout.
  - Wire log panel toggle and HUD/summary placement.
- Traceability:
  - Micro sections: ["4.1 UI Shell", "12. Work Breakdown Structure", "15. Definition of Done"]
- Dependencies: [U05, U09, U10, U11]
- Inputs required: [splitRatio]
- Files to read: `src/app/app.component.*`
- Files to edit or create: `src/app/app.component.ts`, `src/app/app.component.html`, `src/app/app.component.scss`, `src/app/app.component.spec.ts`, `to be discovered (bootstrap file: search for bootstrapApplication or AppModule)`
- Acceptance criteria:
  - [ ] Layout maintains fixed 50/50 split with HUD and summary visible.
  - [ ] Log panel toggle shows/hides panel without layout shift.
- Test plan:
  - Unit: update AppComponent spec if present.
  - Manual: verify component composition and dark-mode styling.
- Risks/assumptions:
  - Bootstrap file location depends on Angular setup (standalone vs module).
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=5, loc=300

### Unit U13: WebGL2 capability fallback
- Goal: Detect WebGL2 support and show fallback messaging.
- Scope:
  - Add WebGL2 feature detection helper and guard render startup.
  - Display fallback message in AppComponent when unsupported.
- Traceability:
  - Micro sections: ["8. Observability and Operational Readiness", "15. Definition of Done"]
- Dependencies: [U06, U12]
- Inputs required: []
- Files to read: `src/app/app.component.*`, `src/app/rendering/**`
- Files to edit or create: `src/app/rendering/webgl-support.ts`, `src/app/app.component.ts`, `src/app/app.component.html`
- Acceptance criteria:
  - [ ] Unsupported browsers see a clear fallback message.
  - [ ] Render loop does not start when WebGL2 is unavailable.
- Test plan:
  - Unit: `webgl-support.spec.ts` (feature detection helper).
  - Manual: disable WebGL2 and verify message.
- Risks/assumptions:
  - Feature detection is consistent across target browsers.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=3, loc=200

### Unit U14: Performance and cross-browser validation notes
- Goal: Document performance targets, tuning notes, and browser results.
- Scope:
  - Record FPS targets and any tuning adjustments or presets.
  - Capture Chrome/Edge/Firefox/Safari smoke-check outcomes.
- Traceability:
  - Micro sections: ["7. Performance tuning + cross-browser validation", "13. Runbooks and Developer Onboarding", "15. Definition of Done"]
- Dependencies: [U06, U07, U08, U12]
- Inputs required: [fpsTargets, browserResults]
- Files to read: `README.md`, `docs/**`
- Files to edit or create: `docs/performance.md`
- Acceptance criteria:
  - [ ] Document lists measured FPS and mitigation steps.
  - [ ] Cross-browser smoke test results recorded.
- Test plan:
  - Unit: none.
  - Manual: verify doc matches latest test runs.
- Risks/assumptions:
  - Browsers are available for validation.
- Estimates:
  - est_impl_tokens: 700
  - max_changes: files=1, loc=150

### Unit U15: Release readiness (Vercel)
- Goal: Define Vercel build settings and release checklist without CI automation.
- Scope:
  - Add Vercel config for static build output.
  - Document production build and deploy steps (no GitHub Actions).
- Traceability:
  - Micro sections: ["3. Build, Dependency, and Environment Setup", "8. Release readiness", "15. Definition of Done"]
- Dependencies: [U01, U12]
- Inputs required: [vercelUrl]
- Files to read: `README.md`, `angular.json`
- Files to edit or create: `vercel.json`, `README.md`
- Acceptance criteria:
  - [ ] Vercel config targets production build output.
  - [ ] README includes manual deploy steps and URL placeholder.
- Test plan:
  - Unit: none.
  - Manual: run production build before deploy.
- Risks/assumptions:
  - Vercel free tier constraints are sufficient.
- Estimates:
  - est_impl_tokens: 800
  - max_changes: files=2, loc=150

## Open Questions
- [ ] Q: What are the final {Project_Name}, {Primary_Audience}, and {Stakeholder_Group_*} labels? — blocks: U11
- [ ] Q: What is the exact {Reference_Paper} title and citation URL? — blocks: U03, U11
- [ ] Q: What baseline and ours mIoU values should display? — blocks: U03, U09
- [ ] Q: What is the approved summary copy text? — blocks: U11
- [ ] Q: Minimum acceptable mobile behavior (view-only vs limited touch)? — blocks: U05, U12
- [ ] Q: What is the performance acceptance threshold (minimum FPS range)? — blocks: U14
- [ ] Q: Confirm no analytics/telemetry beyond in-app logging. — blocks: U10, U14
- [ ] Q: Confirm Equation 7 implementation details and parameter ranges. — blocks: U08

> [!tip] Persistence
> Write this note to: C:\Users\jmckerra\ObsidianNotes\Main\01-Projects\Demo-Gaussian-Splat\Planning\Work-Decomposer-Output.md
> Overwrite if the file already exists.
