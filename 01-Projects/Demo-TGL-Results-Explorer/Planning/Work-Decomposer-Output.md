---
tags:
  - planning
  - work-decomposition
project: "[[01-Projects/TGL-Results-Explorer]]"
plan_title: TGL Results Explorer MVP
context_budget_tokens: 6000
created: 2025-10-29
source_plan: "[[01-Projects/Demo-TGL-Results-Explorer/Planning/micro-level-plan]]"
---

# Work Decomposition — TGL Results Explorer MVP

## Overview
- Project: [[01-Projects/TGL-Results-Explorer]]
- Source plan: [[01-Projects/Demo-TGL-Results-Explorer/Planning/micro-level-plan]]
- Context budget (tokens): 6000

## Units

### Unit U01: Define JSON Schemas and validation script
- Goal: Establish manifest/series JSON Schemas and a Node script to validate data artifacts.
- Scope:
  - Create manifest.schema.json and seriesfile.schema.json (abridged per micro plan 5.2).
  - Implement scripts/validate-data.mjs using Ajv; exit non-zero on schema errors.
- Traceability:
  - Micro sections: ["5.2 JSON Schemas (abridged)", "3.2 Scripts (standardized)", "12 WBS → E1 Data Contracts"]
  - Meso refs (optional): ["3. Data and Interface Design → Schemas", "6. Deployment → Caching Strategy"]
- Dependencies: []
- Inputs required: [Assumptions A1–A5]
- Files to read: `01-Projects/TGL-Results-Explorer/Planning/micro-level-plan`
- Files to edit or create: `docs/data/manifest.schema.json`, `docs/data/seriesfile.schema.json`, `scripts/validate-data.mjs`
- Acceptance criteria:
  - [ ] `node scripts/validate-data.mjs` validates provided fixtures and fails on intentional schema error.
  - [ ] Schemas cover required fields from micro 5.2; unknown fields allowed.
- Test plan:
  - Unit: add minimal schema validation test in `scripts/__tests__/validate-data.spec.mjs` (optional if within limits).
  - Manual: Run validator on sample fixtures; verify error messaging clarity.
- Risks/assumptions:
  - Schema fields may evolve; use forwards-compatible JSON Schema.
- Estimates:
  - est_impl_tokens: 1200
  - max_changes: files=3, loc=220

### Unit U02: Seed minimal sample data v0 for dev/tests
- Goal: Provide a tiny, versioned dataset to unblock development and tests.
- Scope:
  - Add `src/assets/data/v0/manifest.json` with 1 dataset, 1 metric (acc_vs_edges), 2 methods (TGL, BaselineA).
  - Add one curves file matching the manifest and schema.
- Traceability:
  - Micro sections: ["5.3 Storage and layout", "5.5 Caching strategy", "12 WBS → E1 Data Contracts"]
  - Meso refs (optional): ["3. Data and Interface Design → Storage & Indexing"]
- Dependencies: [U01]
- Inputs required: [Sample labels for dataset/methods]
- Files to read: `docs/data/manifest.schema.json`
- Files to edit or create: `src/assets/data/v0/manifest.json`, `src/assets/data/v0/cifar10-acc_vs_edges-TGL.json`
- Acceptance criteria:
  - [ ] `scripts/validate-data.mjs` passes on fixtures.
  - [ ] Files follow path conventions from micro 5.3.
- Test plan:
  - Unit: none (covered by validator).
  - Manual: Spot-check units/labels and a few points for reasonableness.
- Risks/assumptions:
  - Placeholder labels OK until final names are decided.
- Estimates:
  - est_impl_tokens: 700
  - max_changes: files=2, loc=150

### Unit U03: Tooling scripts and budgets (package.json + bundle check)
- Goal: Add standardized scripts and a bundle-size guard.
- Scope:
  - Update `package.json` scripts per micro 3.2.
  - Add `scripts/check-bundle.mjs` (budget 1 MB default).
  - Add baseline lint/type/format configs if missing.
- Traceability:
  - Micro sections: ["3.2 Scripts (standardized)", "1.3 Version/deprecation policy", "12 WBS → E1/E2 entry"]
  - Meso refs (optional): ["6. Deployment and Runtime Architecture → CI stages (local equivalents)"]
- Dependencies: []
- Inputs required: [Node LTS version, package manager]
- Files to read: `package.json`
- Files to edit or create: `package.json`, `scripts/check-bundle.mjs`, `.eslintrc.cjs`, `.prettierrc`
- Acceptance criteria:
  - [ ] `npm run check:bundle` exits non-zero if main bundle exceeds 1 MB.
  - [ ] `npm run lint` and `npm run typecheck` exist.
- Test plan:
  - Unit: lightweight script test optional.
  - Manual: Simulate oversize bundle path and confirm failure.
- Risks/assumptions:
  - Exact dist filename may be hashed; script may need a simple glob.
- Estimates:
  - est_impl_tokens: 1000
  - max_changes: files=4, loc=180

### Unit U10: App shell, routes, theming base
- Goal: Scaffold routes and shell with reduced-motion and basic theme tokens.
- Scope:
  - Define routes for `/` (Hero) and `/explore` (Explorer) using standalone APIs.
  - Implement minimal Shell (Header/Footer) and reduced-motion respect.
- Traceability:
  - Micro sections: ["4.1 App Shell (core)", "4.6 Accessibility & Theming", "12 WBS → E2 App Shell & Theming"]
  - Meso refs (optional): ["2. System Decomposition → App Shell"]
- Dependencies: [U03]
- Inputs required: [Browser support matrix (assumed evergreen)]
- Files to read: `src/app/**` (to be discovered)
- Files to edit or create: `src/app/app.routes.ts`, `src/app/core/shell.component.ts`, `src/app/styles/theme.css`, `src/app/core/error-handler.ts`
- Acceptance criteria:
  - [ ] Navigating `/` and `/explore` renders without console errors.
  - [ ] Prefers-reduced-motion disables motion in shell components.
- Test plan:
  - Unit: small test for route config if available.
  - Manual: Verify keyboard focus order and reduced-motion behavior.
- Risks/assumptions:
  - No SSR; prerender can be added later.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=4, loc=240

### Unit U11: Hero module (3-step visual, accessible narration)
- Goal: Implement accessible hero component honoring reduced-motion.
- Scope:
  - Create `HeroComponent` (standalone) with 3 steps and alt text/captions.
  - Provide minimal styles with color-contrast-friendly defaults.
- Traceability:
  - Micro sections: ["4.2 Hero Module", "4.6 Accessibility & Theming", "12 WBS → E2 App Shell & Theming"]
  - Meso refs (optional): ["2. System Decomposition → Hero Module"]
- Dependencies: [U10]
- Inputs required: [Microcopy for steps]
- Files to read: `src/app/features/hero/**` (to be discovered)
- Files to edit or create: `src/app/features/hero/hero.component.ts`, `src/app/features/hero/hero.component.html`, `src/app/features/hero/hero.component.css`
- Acceptance criteria:
  - [ ] Component passes axe-core checks with no critical issues.
  - [ ] Motion disabled when reduced-motion is set.
- Test plan:
  - Unit: basic render test.
  - Manual: Axe scan; tab order; contrast spot-check.
- Risks/assumptions:
  - SVGs kept small to protect bundle budget.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=3, loc=180

### Unit U20: ManifestService with schema validation (Ajv)
- Goal: Load and validate manifest.json with memoization and types.
- Scope:
  - Implement `ManifestService.getManifest(): Observable<Manifest>` with Ajv validation and memoization.
  - Wire to `assets/data/manifest.json` path.
- Traceability:
  - Micro sections: ["4.4 Data Layer (app/data)", "5.2 JSON Schemas", "5.3 Storage and layout", "12 WBS → E3 Data Layer"]
  - Meso refs (optional): ["3. Data → Manifest Loader"]
- Dependencies: [U01, U02]
- Inputs required: [Data base path config]
- Files to read: `docs/data/manifest.schema.json`, `src/assets/data/**`
- Files to edit or create: `src/app/data/manifest.service.ts`, `src/app/data/ajv.ts`, `src/app/data/types.ts`
- Acceptance criteria:
  - [ ] Invalid manifest triggers SchemaError path; valid manifest caches and shares.
  - [ ] Single network fetch per session (memoized).
- Test plan:
  - Unit: mock fetch success/fail; validate error taxonomy.
  - Manual: throttle network; verify cached behavior.
- Risks/assumptions:
  - Ajv bundle size acceptable; consider code-splitting Ajv if needed.
- Estimates:
  - est_impl_tokens: 1700
  - max_changes: files=3, loc=260

### Unit U21: URLStateService (encode/decode shareable state)
- Goal: Implement stable URL query schema and round-trip encode/decode.
- Scope:
  - Support `ds, metric, methods, preset, deltas, smooth, x, dataVersion` params.
  - Provide `encode(state) → string` and `decode(url) → Selection`.
- Traceability:
  - Micro sections: ["4.4 Data Layer (URLStateService)", "6.2 URL state schema", "12 WBS → E3/E6"]
  - Meso refs (optional): ["3. Data and Interface Design → URL State Service", "9. Traceability Matrix → Download/Share"]
- Dependencies: [U10]
- Inputs required: [URL length constraints (assume typical limits)]
- Files to read: `src/app/data/types.ts`
- Files to edit or create: `src/app/data/url-state.service.ts`, `src/app/data/url-state.spec.ts`
- Acceptance criteria:
  - [ ] encode/decode is lossless for supported fields.
  - [ ] Invalid params are clamped/ignored per whitelist.
- Test plan:
  - Unit: round-trip tests and invalid input clamps.
  - Manual: copy/paste URL reproduces view after U41.
- Risks/assumptions:
  - No URL shortening required for MVP.
- Estimates:
  - est_impl_tokens: 1200
  - max_changes: files=2, loc=200

### Unit U22: CurvesRepository (lazy load, cache, concurrency cap)
- Goal: Provide typed access to curves with caching and bounded concurrency.
- Scope:
  - Implement `getCurves(q)` with key-based memoization and `shareReplay`.
  - Cap concurrent fetches; classify errors.
- Traceability:
  - Micro sections: ["4.4 Data Layer (CurvesRepository)", "5.5 Caching strategy", "12 WBS → E3 Data Layer"]
  - Meso refs (optional): ["3. Data and Interface Design → Curves Repository"]
- Dependencies: [U20]
- Inputs required: [Series file URL format]
- Files to read: `src/app/data/types.ts`, `src/assets/data/**`
- Files to edit or create: `src/app/data/curves.repository.ts`, `src/app/data/http.ts`, `src/app/data/key.util.ts`
- Acceptance criteria:
  - [ ] Duplicate requests return same observable (single fetch).
  - [ ] Error taxonomy matches micro 6.3.
- Test plan:
  - Unit: cache hit/miss; error classification.
  - Manual: network panel shows bounded parallelism.
- Risks/assumptions:
  - Large files deferred by chunking in data packaging.
- Estimates:
  - est_impl_tokens: 1600
  - max_changes: files=3, loc=260

### Unit U30: Chart module scaffold (lazy-loaded) and wrapper
- Goal: Integrate chosen charting lib via a lazy-loaded wrapper component.
- Scope:
  - Create `ChartComponent` (standalone) with lazy import and minimal render of Series[].
  - Abstract chart lib behind adapter for portability.
- Traceability:
  - Micro sections: ["4.3 Explorer Module (Chart View)", "1.1 Charting", "12 WBS → E4 Charting Integration"]
  - Meso refs (optional): ["4. Technology Choices → Charting Options"]
- Dependencies: [U22]
- Inputs required: [Charting library choice]
- Files to read: `src/app/features/explorer/chart/**` (to be created), `src/app/data/types.ts`
- Files to edit or create: `src/app/features/explorer/chart/chart.component.ts`, `src/app/features/explorer/chart/chart.adapter.ts`, `src/app/features/explorer/chart/chart.types.ts`
- Acceptance criteria:
  - [ ] Module loads on `/explore` interaction; not in initial bundle.
  - [ ] Renders at least 2 series from fixtures.
- Test plan:
  - Unit: adapter unit tests for prop mapping (optional).
  - Manual: verify code-splitting via bundle analyzer; check render.
- Risks/assumptions:
  - Adapter surface kept small to protect bundle size.
- Estimates:
  - est_impl_tokens: 1800
  - max_changes: files=3, loc=280

### Unit U31: Interactions, hover/tooltip, throttling, and a11y aids
- Goal: Add interactive hover/tooltip with throttling and accessible fallbacks.
- Scope:
  - Implement hover throttling; keyboard focus markers; stacked tooltip skeleton.
  - Provide ARIA live region or summary for screen readers.
- Traceability:
  - Micro sections: ["4.3 Chart View", "4.6 Accessibility", "12 WBS → E4"]
  - Meso refs (optional): ["2. System Decomposition → Chart View"]
- Dependencies: [U30]
- Inputs required: [Tooltip precision/formatting]
- Files to read: `src/app/features/explorer/chart/chart.component.ts`
- Files to edit or create: `src/app/features/explorer/chart/chart.interactions.ts`, `src/app/features/explorer/chart/chart.a11y.ts`, `src/app/features/explorer/chart/chart.component.ts`
- Acceptance criteria:
  - [ ] Hover updates ≤20 Hz; toggle latency measured <50 ms on fixtures.
  - [ ] Keyboard users can traverse series points; tooltip content accessible.
- Test plan:
  - Unit: throttle utility tests.
  - Manual: performance.mark/measure around hover; axe-core scan.
- Risks/assumptions:
  - Precision/rounding TBD may affect tooltip content.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=3, loc=240

### Unit U40: Control Panel component (selection emitter)
- Goal: Implement controls to select dataset(s), metric, methods, preset, and display options.
- Scope:
  - Build `ControlsComponent` emitting `SelectionChanged` per micro spec.
  - Bind to manifest to populate options.
- Traceability:
  - Micro sections: ["4.3 Explorer Module → Control Panel", "6.2 URL state schema", "12 WBS → E5 Explorer UI"]
  - Meso refs (optional): ["2. System Decomposition → Control Panel"]
- Dependencies: [U20, U21]
- Inputs required: [Presets list/names, smoothing algorithm default]
- Files to read: `src/app/data/types.ts`, `src/app/data/url-state.service.ts`
- Files to edit or create: `src/app/features/explorer/controls/controls.component.ts`, `src/app/features/explorer/controls/controls.component.html`, `src/app/features/explorer/controls/controls.component.spec.ts`
- Acceptance criteria:
  - [ ] Emits distinct `Selection` objects on meaningful change only.
  - [ ] Defaults match app-config and micro plan (overlay single dataset by default).
- Test plan:
  - Unit: distinctUntilChanged behavior; option population from manifest.
  - Manual: keyboard navigation through controls.
- Risks/assumptions:
  - Final preset mappings TBD, stub allowed.
- Estimates:
  - est_impl_tokens: 1700
  - max_changes: files=3, loc=280

### Unit U41: Explorer page orchestration (controls ↔ chart/table)
- Goal: Wire selections to chart and table; sync with URL state.
- Scope:
  - Create `ExplorerPageComponent` orchestrating data fetch, deltas flag, and URL sync.
  - Ensure idempotent updates and cancellation on deselect.
- Traceability:
  - Micro sections: ["4.3 Explorer Module", "4.4 Data Layer", "12 WBS → E5"]
  - Meso refs (optional): ["2. System Decomposition → Explorer Module"]
- Dependencies: [U22, U40]
- Inputs required: [Multi-dataset behavior]
- Files to read: `src/app/features/explorer/controls/controls.component.ts`, `src/app/data/curves.repository.ts`
- Files to edit or create: `src/app/features/explorer/explorer.page.ts`, `src/app/features/explorer/explorer.page.html`
- Acceptance criteria:
  - [ ] URL changes reflect selection; reload reproduces view.
  - [ ] Cancels in-flight requests on selection change.
- Test plan:
  - Unit: selection → URL sync round-trip (with U21 tests).
  - Manual: verify overlay/facet behavior as decided.
- Risks/assumptions:
  - Faceting may be deferred if out of scope.
- Estimates:
  - est_impl_tokens: 1600
  - max_changes: files=2, loc=260

### Unit U42: Table view component
- Goal: Implement sortable, consistent table view of visible series points.
- Scope:
  - Render flattened rows; sort; optional pagination for multi-dataset.
- Traceability:
  - Micro sections: ["4.3 Explorer Module → Table View", "12 WBS → E5"]
  - Meso refs (optional): ["2. System Decomposition → Table View"]
- Dependencies: [U41]
- Inputs required: [Default sort]
- Files to read: `src/app/features/explorer/explorer.page.ts`
- Files to edit or create: `src/app/features/explorer/table/table.component.ts`, `src/app/features/explorer/table/table.component.html`, `src/app/features/explorer/table/table.component.spec.ts`
- Acceptance criteria:
  - [ ] Table rows match chart filter/selection.
  - [ ] Sorting stable and accessible (aria-sort).
- Test plan:
  - Unit: mapping from series → rows; sort behavior.
  - Manual: keyboard navigation; screen-reader announcements.
- Risks/assumptions:
  - Large row counts mitigated by virtualization/pagination if needed.
- Estimates:
  - est_impl_tokens: 1600
  - max_changes: files=3, loc=280

### Unit U43: Delta calculation spec and tests
- Goal: Implement delta vs “best baseline” calculation with tests.
- Scope:
  - Define baseline set selection and interpolation at nearest x; tie-breaking per micro A5.
  - Expose `computeDeltas(series[], policy)` utility.
- Traceability:
  - Micro sections: ["4.3 Explorer Module (Chart View) → deltas", "1.1 A5 Best baseline", "10.4 Sample cases", "12 WBS → E5"]
  - Meso refs (optional): ["2. System Decomposition → Deltas vs best baseline"]
- Dependencies: [U22]
- Inputs required: [Baseline set definition, interpolation policy]
- Files to read: `src/app/data/types.ts`
- Files to edit or create: `src/app/features/explorer/chart/delta.ts`, `src/app/features/explorer/chart/delta.spec.ts`
- Acceptance criteria:
  - [ ] Tests cover mismatched x-grids and tie-breaking.
  - [ ] Utility is pure and deterministic.
- Test plan:
  - Unit: golden cases from micro 10.4.
  - Manual: spot-check tooltips reflect delta results.
- Risks/assumptions:
  - Final policy may change; keep flags/params configurable.
- Estimates:
  - est_impl_tokens: 1400
  - max_changes: files=2, loc=240

### Unit U50: ExportService (CSV/JSON) and share link UX
- Goal: Enable CSV/JSON export and copy shareable URL.
- Scope:
  - Implement `ExportService.toCSV/toJSON` using visible series.
  - Add `ShareMenuComponent` with copy-to-clipboard.
- Traceability:
  - Micro sections: ["4.4 Data Layer (ExportService)", "6.2 URL state schema", "12 WBS → E6 Export & Share"]
  - Meso refs (optional): ["2. System Decomposition → Export API"]
- Dependencies: [U41]
- Inputs required: [File naming pattern]
- Files to read: `src/app/features/explorer/explorer.page.ts`
- Files to edit or create: `src/app/data/export.service.ts`, `src/app/features/explorer/controls/share-menu.component.ts`
- Acceptance criteria:
  - [ ] Downloaded CSV/JSON exactly match chart data.
  - [ ] Share link reproduces view after paste.
- Test plan:
  - Unit: CSV/JSON round-trip vs in-memory series.
  - Manual: Clipboard works across browsers; long URLs acceptable.
- Risks/assumptions:
  - Locale/precision formatting standardized (micro 6.2/10.4).
- Estimates:
  - est_impl_tokens: 1300
  - max_changes: files=2, loc=220

### Unit U51: Chart PNG export
- Goal: Provide PNG export for current chart view.
- Scope:
  - Implement `toPNG(chart)` and trigger from controls.
- Traceability:
  - Micro sections: ["4.4 Data Layer (ExportService) → toPNG", "12 WBS → E6"]
  - Meso refs (optional): ["4. Technology Choices → Chart exports"]
- Dependencies: [U30, U50]
- Inputs required: [Export DPI and filename pattern]
- Files to read: `src/app/features/explorer/chart/chart.component.ts`
- Files to edit or create: `src/app/features/explorer/chart/export.ts`, `src/app/features/explorer/chart/chart.component.ts`
- Acceptance criteria:
  - [ ] PNG export renders current view with legend.
  - [ ] File size reasonable (<1 MB for fixture view).
- Test plan:
  - Unit: none practical; mock canvas export.
  - Manual: visual compare PNG vs on-screen.
- Risks/assumptions:
  - Export path varies by chart lib; keep adapter abstraction.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=2, loc=160

### Unit U60: Run Details panel with provenance
- Goal: Implement details panel showing selected point context and provenance.
- Scope:
  - Display method/config, edges breakdown, seeds/variance if available, provenance link.
- Traceability:
  - Micro sections: ["4.3 Run Details (details/)", "5.1 TypeScript contracts → Provenance", "12 WBS → E7"]
  - Meso refs (optional): ["2. System Decomposition → Run Details Panel"]
- Dependencies: [U41]
- Inputs required: [Run details field list]
- Files to read: `src/app/features/explorer/explorer.page.ts`
- Files to edit or create: `src/app/features/explorer/details/details.component.ts`, `src/app/features/explorer/details/details.component.html`, `src/app/features/explorer/details/details.component.css`
- Acceptance criteria:
  - [ ] Opening details from a point shows consistent values with tooltip.
  - [ ] Provenance information is always visible.
- Test plan:
  - Unit: formatting utilities; simple render test.
  - Manual: keyboard open/close; screen-reader labels.
- Risks/assumptions:
  - Some fields optional; handle missing gracefully.
- Estimates:
  - est_impl_tokens: 1300
  - max_changes: files=3, loc=240

### Unit U70: ErrorBeaconService and consent toggle
- Goal: Capture errors/metrics and gate sending via explicit consent.
- Scope:
  - Implement `ErrorBeaconService.captureError` and metrics marks summary.
  - Add `ConsentService` and simple `ConsentToggleComponent` in shell.
- Traceability:
  - Micro sections: ["4.5 Observability (app/obs)", "8.2 Metrics", "9.2 Input validation", "12 WBS → E8"]
  - Meso refs (optional): ["5. Integration Points → Error Reporting"]
- Dependencies: [U10]
- Inputs required: [Beacon endpoint/provider]
- Files to read: `src/app/core/shell.component.ts`
- Files to edit or create: `src/app/obs/error-beacon.service.ts`, `src/app/core/consent.service.ts`, `src/app/core/consent-toggle.component.ts`
- Acceptance criteria:
  - [ ] No beacons sent by default; enabling toggle sends summarized payloads.
  - [ ] Errors are captured and buffered; best-effort send on visibilitychange.
- Test plan:
  - Unit: payload shape and gating logic.
  - Manual: network tab verifies no traffic until consent.
- Risks/assumptions:
  - CSP must allow the beacon domain if configured.
- Estimates:
  - est_impl_tokens: 1500
  - max_changes: files=3, loc=240

### Unit U71: Privacy notice and CSP baseline
- Goal: Provide privacy copy and minimal CSP compatible with static hosting and optional beacon.
- Scope:
  - Add privacy notice doc and link in footer.
  - Add CSP meta tag restricting script/connect-src appropriately.
- Traceability:
  - Micro sections: ["9. Security and Privacy Controls → CSP", "8. Observability and Operational Readiness", "12 WBS → E8"]
  - Meso refs (optional): ["6. Deployment → Caching Strategy (CSP implications)"]
- Dependencies: [U10, U70]
- Inputs required: [Beacon/analytics host list]
- Files to read: `src/index.html` (to be discovered), `src/app/core/shell.component.ts`
- Files to edit or create: `docs/privacy.md`, `src/index.html`
- Acceptance criteria:
  - [ ] Default CSP blocks inline scripts and eval; app still runs.
  - [ ] Beacon host whitelisted only when configured.
- Test plan:
  - Unit: n/a.
  - Manual: open console for CSP violations; verify no regressions.
- Risks/assumptions:
  - Some chart libs require relaxed CSP; adapter must avoid unsafe-eval.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=2, loc=80

### Unit U80: Feature flags and runtime config
- Goal: Implement runtime config loading and feature flags for Phase 2 metrics.
- Scope:
  - Add `assets/app-config.json` and `ConfigService` with precedence rules.
  - Flags: `latency`, `roundsToTarget` default false.
- Traceability:
  - Micro sections: ["7. Configuration and Secrets", "12 WBS → E9 Phase 2 Metrics"]
  - Meso refs (optional): ["6. Deployment → Environments"]
- Dependencies: [U10]
- Inputs required: [Default dataset/metric/methods]
- Files to read: `01-Projects/TGL-Results-Explorer/Planning/micro-level-plan`
- Files to edit or create: `src/assets/app-config.json`, `src/app/core/config.service.ts`
- Acceptance criteria:
  - [ ] Config loads at runtime and overrides build-time defaults.
  - [ ] Phase 2 toggles disabled by default.
- Test plan:
  - Unit: precedence tests for config.
  - Manual: flip flags and verify UI changes are gated.
- Risks/assumptions:
  - Ensure config fetch doesn’t block TTI (lazy after shell).
- Estimates:
  - est_impl_tokens: 1100
  - max_changes: files=2, loc=180

### Unit U81: Metrics controls for Phase 2 (flag-gated)
- Goal: Add UI controls for latency and rounds-to-target, hidden unless enabled.
- Scope:
  - Implement metric toggles in controls and guard rendering by feature flags.
- Traceability:
  - Micro sections: ["3. Metrics (Open Questions)", "12 WBS → E9"]
  - Meso refs (optional): ["2. System Decomposition → Control Panel"]
- Dependencies: [U80, U40]
- Inputs required: [Datasets with latency, default target X%]
- Files to read: `src/app/features/explorer/controls/controls.component.ts`
- Files to edit or create: `src/app/features/explorer/controls/metrics-toggle.component.ts`, `src/app/features/explorer/explorer.page.ts`
- Acceptance criteria:
  - [ ] When flags off, controls hidden; when on, additional metrics available.
  - [ ] URL state handles new params without breaking older links.
- Test plan:
  - Unit: rendering guards; URL schema backward compatibility.
  - Manual: toggle flags and verify expected UI.
- Risks/assumptions:
  - Data availability for latency may be partial.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=2, loc=160

### Unit U90: Accessibility and theming enhancements
- Goal: Implement color-blind safe palettes, high-contrast, and focus management.
- Scope:
  - Add a11y stylesheet and theme service to toggle high contrast.
  - Ensure focus outlines and ARIA labels on key components.
- Traceability:
  - Micro sections: ["4.6 Accessibility & Theming", "10. Testing Strategy (a11y)"]
  - Meso refs (optional): ["7. Non-Functional Requirements Mapping → Accessibility"]
- Dependencies: [U10, U11, U30]
- Inputs required: [Approved palette]
- Files to read: `src/app/styles/theme.css`
- Files to edit or create: `src/styles/a11y.css`, `src/app/core/theme.service.ts`, `src/app/features/hero/hero.component.html`
- Acceptance criteria:
  - [ ] Axe-core shows no serious a11y issues on key pages.
  - [ ] High-contrast mode toggles and persists.
- Test plan:
  - Unit: theme service behavior.
  - Manual: axe scan; keyboard traversal; contrast check.
- Risks/assumptions:
  - Palette approval pending.
- Estimates:
  - est_impl_tokens: 1200
  - max_changes: files=3, loc=200

### Unit U95: Performance budgets and lighthouse check (local)
- Goal: Add local Lighthouse check and enforce budgets via script.
- Scope:
  - Add `.lighthouserc.json` and `scripts/lighthouse-check.mjs` to run against `/` and `/explore`.
  - Wire `npm run lighthouse` and include budgets.
- Traceability:
  - Micro sections: ["10. Testing Strategy (Performance)", "1.3 Budgets", "12 WBS → E2 exit"]
  - Meso refs (optional): ["7. Non-Functional → Performance"]
- Dependencies: [U10, U30]
- Inputs required: [Budget thresholds]
- Files to read: `package.json`
- Files to edit or create: `.lighthouserc.json`, `scripts/lighthouse-check.mjs`, `package.json`
- Acceptance criteria:
  - [ ] `npm run lighthouse` exits non-zero if performance score < 0.9 or budgets exceeded.
  - [ ] Initial bundle size under 1 MB is enforced.
- Test plan:
  - Unit: n/a.
  - Manual: run script; inspect report.
- Risks/assumptions:
  - Headless run available in local env.
- Estimates:
  - est_impl_tokens: 900
  - max_changes: files=3, loc=120

## Open Questions
- [ ] Q1: Final baseline list and whether FL/federated variants are included; parity definition for “edges/round.” — blocks: U02, U40, U43
- [ ] Q2: Canonical preset names and parameter mappings; global vs dataset-specific. — blocks: U40
- [ ] Q3: Datasets with latency; defaults for rounds-to-X%; precision/rounding standards. — blocks: U81, U31, U50
- [ ] Q4: Multi-dataset default behavior (overlay vs facet vs tabs). — blocks: U41, U30
- [ ] Q5: “Best baseline” definition and interpolation details for mismatched x. — blocks: U43, U31
- [ ] Q6: Browser support matrix (minimum versions, mobile). — blocks: U10, U90
- [ ] Q7: Hosting/CDN choice and cache headers for /data/. — blocks: U71 (CSP allowances), U20 (manifest path TTL)
- [ ] Q8: Error/analytics provider and endpoints; default off but which domain(s) to allow. — blocks: U70, U71
- [ ] Q9: Final data spec (schemas and directory layout) sign-off. — blocks: U01, U20, U22
- [ ] Q10: Charting library choice balancing features vs bundle size. — blocks: U30, U31
- [ ] Q11: Smoothing algorithm and parameters; scope and UI affordance. — blocks: U40, U31
- [ ] Q12: Tooltip number formatting, units, and default table sort. — blocks: U31, U42, U50

> [!tip] Persistence
> Write this note to: 01-Projects/<Project-Name>/Planning/Work-Decomposer-Output.md
> Overwrite if the file already exists.
