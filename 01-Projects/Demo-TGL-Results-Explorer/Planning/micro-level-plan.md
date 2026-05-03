Session Inputs Restatement
- Meso Summary: Static, no-backend {Project_Name} Results Explorer (Angular SPA) with 3-step hero and interactive explorer to compare {Primary_Method} presets vs {Baseline_Methods} using Accuracy vs Edges/round (MVP); optional Latency and Rounds-to-Target (Phase 2). Precomputed, versioned static data; shareable URLs; downloads; visible provenance.
- Constraints: Static hosting; no server state; initial bundle < 1 MB; TTI < 2 s; chart toggle < 50 ms; 60 fps animations; WCAG-aligned accessibility; privacy-by-default; optional analytics via explicit toggle; client-side error beacons; provenance display.
- NFRs: Performance budgets; accessibility; privacy/security; maintainability/extensibility; simple operability; low scale expected.
- Standards (inferred): Angular for web UI; modular, layered front-end; data contracts and validation; CI gates for budgets and schema.

Open Questions and Blocked Decisions
Requirements
1) Baselines & scope: Final baseline list; whether federated variants are included; parity definition for “edges/round.”
2) Presets: Canonical preset names and param mappings ({Param_1..Param_5}); global vs dataset-specific.
3) Metrics: Datasets with latency; defaults for rounds-to-X%; precision/rounding standards.
4) Multi-dataset: Overlay vs faceting vs tabs; default behavior.
5) “Best baseline” definition: Candidate set; tie-breaking; interpolation across misaligned x-grids.
Assumptions (provisional) and validation
- A1: Baselines include {Baseline_Set_A}, FL excluded initially; edges/round parity definition recorded in docs. Validate in design review, update tests.
- A2: Presets are global for MVP; dataset-specific allowed later; store resolver in data manifest. Validate with data owners.
- A3: Rounds-to-target default X=90%; latency available for {Subset_of_Datasets}. Validate via sample artifacts.
- A4: Default view overlays a single dataset; multiple datasets facet by rows. Validate via UX review and Lighthouse.
- A5: “Best baseline” = max accuracy at same x with linear interpolation to nearest x; ties prefer simpler method. Validate with golden cases.
Constraints & NFRs
6) Browser support: Minimum versions and mobile targets TBD. Assumption: evergreen browsers (last 2), Safari ≥ 16, Android Chrome ≥ 120.
7) Hosting/CDN: {Static_Host_A|Static_Host_B|Static_Host_C}. Assumption: {Static_Host_A} with immutable asset caching, short TTL for manifest.
Dependencies
8) Error/analytics provider: {Error_Provider_A|B}, {Privacy_Analytics_Provider_A|B}. Assumption: disabled by default; opt-in toggle wires provider URLs.
9) Data spec: Final manifest/curves JSON schemas and directory layout under /data/. Assumption: versioned subfolders (e.g., /data/v{N}/...).
Risks
10) Bundle budget risk from charting lib; data file sizes impacting interactivity; ambiguity in delta calculations; a11y regressions. Mitigations integrated below.
Validation Plan
- Hold a 30–45 min decision review to resolve 1–9; merge outcomes into schemas, constants, and tests. Fallback to A1–A5 until resolved; track deltas in CHANGELOG.

1. Technology Stack and Version Pins
1.1 Primary languages and frameworks (mandated/selected)
- Language: TypeScript {TS_Version_Min}+ (target {TS_Version_Target}).
- Framework: Angular {Angular_Major}+ (standalone APIs, SSR prerender).
- State: Angular Signals for local UI; RxJS for async data streams.
- Charting: {Charting_Option_B} (recommended) with lazy-loaded module; fall back to {Charting_Option_A} if bundle pressure; {Charting_Option_C} acceptable with strict code-splitting.
- Tooling: Node {Node_LTS_Version}; {pnpm|npm|yarn} (recommend pnpm ≥ {PNPM_Version}); ESLint + typescript-eslint; Prettier; Husky + lint-staged; commitlint (Conventional Commits).
- Testing: {Jest|Vitest} for unit; Playwright for e2e; Axe-core for a11y; Lighthouse CI.
- Data validation: Ajv for JSON Schema; zod (optional) for TS runtime contracts.
- Observability: navigator.sendBeacon to {Error_Provider_A|B}; optional analytics {Privacy_Analytics_Provider_A|B} behind toggle.
- Build: Angular builder, prerender shell/hero, code-splitting, brotli/gzip.
1.2 Alternatives and trade-offs
- Charting: {Charting_Option_A} (fast/small, fewer exports, add a11y aids) vs {Charting_Option_B} (balanced features/size) vs {Charting_Option_C} (expressive, heavier, declarative specs).
- Package manager: pnpm (fast, strict, fewer dupes) vs npm (ubiquitous) vs yarn (ok, less momentum).
- Test runner: Vitest (fast, ESM-native) vs Jest (mature ecosystem); choose per team familiarity.
1.3 Version/deprecation policy
- Pin major.minor in package.json; renovate weekly for patch bumps; no breaking upgrades within a minor release cycle unless budget/security demands.
- Compatibility: ES2022 targets; evergreen browsers; polyfills only when necessary and budgeted.

2. Repository Structure and Conventions
2.1 Directory tree (Angular workspace)
- root/
  - src/
    - app/
      - core/ (app-shell, theming, routes, guards)
      - features/
        - hero/
        - explorer/
          - controls/
          - chart/
          - table/
          - details/
      - data/ (manifest loader, repository, url-state, export)
      - obs/ (observability: beacon, consent)
      - shared/ (ui primitives, pipes)
    - assets/
      - data/ (copied/linked versioned artifacts)
      - images/, icons/
    - styles/
  - scripts/ (schema validate, data copy, bundle-size check)
  - e2e/ (Playwright)
  - docs/ (architecture, data spec, runbooks)
  - .editorconfig, .eslintrc.cjs, .prettierrc, commitlint.config.cjs
2.2 Conventions
- Naming: kebab-case files; PascalCase components; camelCase functions.
- Code style: Prettier; ESLint ruleset with strict TS; Angular ESLint plugin.
- Docs: ADRs in docs/adr/; data schema docs in docs/data/.
- Ownership: CODEOWNERS per folder (core, features/explorer, data, obs).
- Commits: Conventional Commits; squash merge; branch naming feat|fix|chore/<scope>/<short-desc>.

3. Build, Dependency, and Environment Setup
3.1 Package and lock policy
- Package manager: pnpm; lockfile committed; "engine" fields enforce Node and pnpm versions; .nvmrc for Node.
3.2 Scripts (standardized)
- format:prettier → prettier --write "**/*.{ts,js,json,md,css,html}"
- lint → eslint .
- typecheck → tsc -p tsconfig.json --noEmit
- test:unit → {vitest|jest}
- test:e2e → playwright test
- build → ng build --configuration=production
- prerender → ng run app:prerender
- serve → ng serve
- validate:data → node scripts/validate-data.mjs
- check:bundle → node scripts/check-bundle.mjs --budget 1mb
- ci → run lint,typecheck,test:unit,validate:data,build,check:bundle,lighthouse
3.3 Bootstrap steps
- Prereqs: Node {Node_LTS_Version}; pnpm; browsers (Playwright).
- Steps: pnpm i; pnpm validate:data (with sample data); pnpm serve; pnpm test:unit; pnpm test:e2e.
3.4 Cross-platform
- All scripts are Node-based; avoid bashisms; Windows-compatible path handling.

4. Detailed Module/Component Specifications
4.1 App Shell (core)
- Responsibilities: Routing, layout (Header/Footer), theming (reduced-motion, contrast), consent toggle, version banner.
- Inputs: environment config, prefers-reduced-motion/media queries.
- Outputs: Router outlets; global providers.
- Public interface (routes): 
  - "/" → Hero; "/explore" → Explorer; "/learn" (optional).
- Error handling: GlobalErrorHandler → captureError(event) → console + beacon (if consented).
- Concurrency: N/A; UI-thread only.
- Pseudocode:
```ts path=null start=null
export const routes: Routes = [
  { path: '', component: HeroPageComponent },
  { path: 'explore', loadComponent: () => import('./features/explorer/explorer.page') },
];
```
4.2 Hero Module (features/hero)
- Responsibilities: 3-step visual; accessible narration; respects reduced-motion.
- Inputs: media query, theme.
- Outputs: CTA links.
- Error handling: none; ensure a11y alt text.
- Pseudocode:
```ts path=null start=null
@Component({ selector: 'app-hero', standalone: true })
export class HeroComponent { @Input() reducedMotion = false; }
```
4.3 Explorer Module (features/explorer)
- Subcomponents and contracts
  a) Control Panel (controls/)
  - Inputs: Manifest, URL state.
  - Outputs: SelectionChanged event { datasetIds, metricId, methodIds, presetId, display: { deltas, smoothing, xScale } }.
  - Idempotency: emitting same selection ignored via distinctUntilChanged.
  - Pseudocode:
```ts path=null start=null
export interface Selection {
  datasetIds: string[]; metricId: string; methodIds: string[]; presetId?: string;
  display: { deltas: boolean; smoothing: boolean; xScale: 'linear'|'log' };
}
@Output() selectionChanged = new EventEmitter<Selection>();
```
  b) Chart View (chart/)
  - Inputs: Series[]; display options; baseline policy.
  - Outputs: Hover/Focus events; Export events.
  - Performance: virtualize series; throttle hover; lazy init chart lib.
  - Error handling: render fallback on data gaps; tooltip marks missing.
  c) Table View (table/)
  - Inputs: Flattened rows from Series; sort; pagination (if multi-dataset).
  - Outputs: RowSelected → Details panel.
  d) Run Details (details/)
  - Inputs: Selected point context; provenance.
  - Outputs: Link to raw slice; copy JSON.
4.4 Data Layer (app/data)
- Services
  - ManifestService: getManifest(): Observable<Manifest> (memoized, schema-validated).
  - CurvesRepository: getCurves(q: {datasetId, metricId, methodId, presetId?}): Observable<Series> (lazy, cache Map, shareReplay).
  - URLStateService: encode(state: Selection) → string; decode(url) → Selection.
  - ExportService: toCSV(series[]): string; toJSON(series[]): string; toPNG(chart): Blob.
- Error handling: classify errors {NetworkError, SchemaError, NotFound, ParseError}; retries for network with backoff; no retries for schema errors.
- Idempotency: cache keys as `${datasetId}:${metricId}:${methodId}:${presetId ?? '-'}`.
- Concurrency: concurrent fetch capped (e.g., 6); cancel on deselect.
- Pseudocode:
```ts path=null start=null
@Injectable({providedIn:'root'})
export class CurvesRepository {
  private cache = new Map<string, Observable<Series>>();
  getCurves(q: Q): Observable<Series> {
    const key = keyOf(q);
    if (this.cache.has(key)) return this.cache.get(key)!;
    const stream = defer(() => fetchJson(urlOf(q))).pipe(
      map(validateSeries), shareReplay({ bufferSize: 1, refCount: true })
    );
    this.cache.set(key, stream);
    return stream;
  }
}
```
4.5 Observability (app/obs)
- ErrorBeaconService: captureError(event, context) → buffer → sendBeacon(endpoint, payload) if consented; retry best-effort on visibilitychange.
- Metrics: mark/measure TTI, chart render, toggle latency; aggregate to summary for beacon.
4.6 Accessibility & Theming (core)
- Color-blind safe palettes; high-contrast theme; focus management; ARIA labels; keyboard flow order; reduced-motion toggles.

5. Data Model and Persistence
5.1 TypeScript contracts
```ts path=null start=null
export interface Dataset { id: string; label: string; tags?: string[] }
export interface Metric { id: string; label: string; unit?: string; axis: 'x'|'y' }
export interface Method { id: string; type: 'Primary'|'Baseline'; colorKey?: string }
export interface Preset { id: string; label: string; params: Record<string, number|string>; scope: 'global'|'per-dataset' }
export interface CurvePoint { x: number; y: number; xUnit?: string; yUnit?: string; n?: number; seed?: number; ciLo?: number; ciHi?: number }
export interface Series { datasetId: string; metricId: string; methodId: string; presetId?: string; variant?: string; points: CurvePoint[]; variance?: unknown }
export interface Provenance { source: string; license?: string; checksum?: string; createdAt?: string; version?: string }
export interface SeriesHeader { datasetId: string; metricId: string; methodId: string; presetId?: string; xLabel?: string; yLabel?: string; units?: Record<string,string>; provenance?: Provenance }
export interface SeriesFile { header: SeriesHeader; points: CurvePoint[] }
export interface Manifest {
  version: string;
  datasets: Dataset[]; metrics: Metric[]; methods: Method[]; presets: Preset[];
  seriesIndex: Array<{ datasetId: string; metricId: string; methodId: string; presetId?: string; file: string }>
}
```
5.2 JSON Schemas (abridged)
```json path=null start=null
{
  "$id": "manifest.schema.json",
  "type": "object",
  "required": ["version","datasets","metrics","methods","seriesIndex"],
  "properties": {
    "version": {"type":"string"},
    "datasets": {"type":"array","items": {"type":"object","required":["id","label"],"properties":{"id":{"type":"string"},"label":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}}}}},
    "metrics": {"type":"array","items": {"type":"object","required":["id","label","axis"],"properties":{"id":{"type":"string"},"label":{"type":"string"},"unit":{"type":"string"},"axis":{"enum":["x","y"]}}}},
    "methods": {"type":"array","items": {"type":"object","required":["id","type"],"properties":{"id":{"type":"string"},"type":{"enum":["Primary","Baseline"]},"colorKey":{"type":"string"}}}},
    "presets": {"type":"array","items": {"type":"object","required":["id","label","params","scope"],"properties":{"id":{"type":"string"},"label":{"type":"string"},
      "params":{"type":"object","additionalProperties": {"type":["number","string"]}},"scope":{"enum":["global","per-dataset"]}}}},
    "seriesIndex": {"type":"array","items": {"type":"object","required":["datasetId","metricId","methodId","file"],
      "properties":{"datasetId":{"type":"string"},"metricId":{"type":"string"},"methodId":{"type":"string"},"presetId":{"type":"string"},"file":{"type":"string"}}}}
  }
}
```
5.3 Storage and layout
- Directory: /data/v{dataVersion}/{datasetId}/{metricId}/{methodId}[-{presetId}].json (content-hash optional).
- Index: manifest at /data/manifest.json (short TTL); files immutable long TTL.
5.4 Migrations/rollbacks
- New version creates /data/v{N+1}/; older versions remain; app defaults to latest; share URLs may specify dataVersion.
- Seeding: include sample minimal dataset for dev/tests.
5.5 Caching strategy
- In-memory Map per key; HTTP cache honors ETag; optional SW for offline deferred.

6. API and Message Contracts
6.1 Static endpoints
- GET {Public_Base}/data/manifest.json → Manifest
- GET {Public_Base}/data/v{ver}/{...}.json → SeriesFile
6.2 URL state schema (query params)
- ds, metric, methods (comma-separated), preset, deltas=0|1, smooth=0|1, x=lin|log, dataVersion=vN.
- Example: ?ds=cifar10&metric=acc_vs_edges&methods=TGL,SGD&preset=balanced&deltas=1&smooth=0&x=lin&dataVersion=v1
6.3 Error taxonomy and codes
- NetworkError (status 0, 408, 5xx), NotFound (404), SchemaError (local validation), ParseError (JSON). UI shows non-blocking toast with retry.
6.4 Versioning and compatibility
- Manifest.version semver; forwards-compatible additive fields; clients ignore unknown fields.
6.5 Rate limits/pagination
- N/A; throttle UI events; cap concurrent fetches.

7. Configuration and Secrets
7.1 Config precedence
- Build-time env (environment.ts) < runtime config (assets/app-config.json) < URL flags.
- Environments: development, preview, production.
7.2 Keys
- appName, dataBasePath, defaultDataset, defaultMetric, defaultMethods[], defaultPreset, featureFlags { latency, roundsToTarget }, budgets { initialBundle, ttiMs, toggleLatencyMs }.
- observability { beaconEnabledDefault=false, beaconEndpoint, analyticsEnabledDefault=false, analyticsSrc }.
7.3 Secrets management
- Third-party keys stored as build secrets in CI; injected into app-config.json for prod only; never committed; local dev uses .env.local consumed by a prep script that writes assets/app-config.local.json (gitignored).
7.4 Secure defaults
- Beacons/analytics default off; CSP strict default; no PII in payloads; provenance always shown.

8. Observability and Operational Readiness
8.1 Logging
- Structured: { level, ts, event, message, context } printed to console; debug gated by flag.
- Correlation: sessionId (uuid v4), pageId, selectionHash.
8.2 Metrics
- Counters: errors.total, exports.csv/json/png, selections.changed.
- Histograms: chart.render.ms, toggle.latency.ms, tti.ms.
- Tracing: simple span-like nested measures via performance.mark/measure.
8.3 Dashboards/alerts
- If analytics enabled, wire basic charts for tti, errors; no paging alerts (static app).
8.4 Health checks
- Static app: expose version.json with {appVersion, buildTime, dataVersion}; add “About” panel.

9. Security and Privacy Controls
9.1 AuthN/Z
- None for browsing; consent gate for beacons/analytics stored in localStorage.
9.2 Input validation and output encoding
- Validate URL params; clamp/whitelist; escape outputs in tooltips; sanitize HTML if any.
9.3 Least privilege
- CSP: script-src 'self'; connect-src 'self' {Error_Provider_Host?}; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'.
- No unsafe-eval; no inline scripts.
9.4 Data protection
- HTTPS only; no PII collected; provenance fields limited to public sources.
9.5 Supply chain
- Enable dependency scanning ({CI_Scan_Option}); lockfile update policy; SCA gate on CI.
- Secure coding checklist in docs/security-checklist.md.

10. Testing Strategy and Plan
10.1 Pyramid and targets
- Unit (>70% statements, >80% critical modules); Integration (data loader + chart rendering); Contract (JSON Schema validation against fixtures); E2E (happy paths + a11y); Performance (Lighthouse: budgets enforced).
10.2 Data management
- Test fixtures: small manifest + 2–3 series files; golden images for chart via Playwright screenshot tests (tolerances set low); mocks for fetch.
10.3 Flakiness controls
- Deterministic seeds; network mocked; retry policy isolated.
10.4 Sample cases
- Load manifest success/fail; Selection enc/dec roundtrip; Delta calc against baselines with mismatched x; Export CSV matches visible series; Reduced-motion disables animations; Bundle size guard under 1 MB.

11. CI/CD Pipeline Definition
11.1 Stages
- checkout → setup-node+pnpm → install → lint → typecheck → unit tests → schema validate data → build + prerender → bundle-size check → a11y (axe) → lighthouse-ci → upload artifact → deploy preview ({CI_CD_Option_A|B}) → manual approve → prod deploy → cache invalidation.
11.2 Required checks
- ESLint clean; typecheck pass; tests pass; data schemas validated; budgets enforced; CSP present.
11.3 Versioning & release
- App semver in package.json; changelog via conventional commits; dataVersion in manifest; release notes include data changes and checksums.
11.4 Rollback
- Promote prior artifact; revert CDN alias; no DB migrations.

12. Work Breakdown Structure (WBS)
Epics and sequencing (→ denotes dependency)
1) Data Contracts & Packaging → 2) App Shell & Theming → 3) Data Layer → 4) Charting Integration → 5) Explorer UI → 6) Export & Share → 7) Run Details & Provenance → 8) Observability & Privacy → 9) Phase 2 Metrics.
Key tasks per epic (entry/exit criteria abbreviated)
- E1 Data Contracts
  - Define TS types + JSON Schemas; write scripts/validate-data.mjs; create sample /data/v0. Entry: open questions A1–A5 draft; Exit: fixtures + CI job green.
- E2 App Shell & Theming
  - Routes, layout, theme service, reduced-motion; prerender shell/hero. Exit: Lighthouse TTI < 2s with empty explorer.
- E3 Data Layer
  - Manifest loader, repository, URL state, caching, error taxonomy. Exit: unit tests + contract tests passing.
- E4 Charting Integration
  - Choose {Charting_Option}; lazy module; tooltip/legend; perf budget. Exit: toggle latency < 50 ms on fixtures.
- E5 Explorer UI
  - Controls, chart-table orchestration, presets resolver stub, delta calc spec + tests. Exit: shareable URL reproduces view.
- E6 Export & Share
  - CSV/JSON/PNG exports; clipboard; URL encode/decode. Exit: downloads match chart data.
- E7 Run Details & Provenance
  - Panel UI; link to raw slices; checksum display. Exit: manual QA.
- E8 Observability & Privacy
  - Error beacon (opt-in); analytics toggle; privacy notice; CSP config. Exit: beacons gated; CSP validated.
- E9 Phase 2 Metrics
  - Latency, rounds-to-target; variance bands. Exit: feature flags off by default.
Parallelization
- E2 and E1 can run in parallel; E4 starts after E3 minimal; E6 after E5; E8 parallel from mid E5.

13. Runbooks and Developer Onboarding
- Setup
  1) Install Node {Node_LTS_Version} and pnpm.
  2) pnpm install.
  3) pnpm validate:data (uses fixtures in src/assets/data/v0).
  4) pnpm serve and open /explore.
- Common commands
  - pnpm lint | test:unit | test:e2e | build | prerender | check:bundle | lighthouse
- Debug tips
  - Enable debug logs via ?debug=1; use Angular DevTools; profile chart interactions; verify cache hits in Network tab.
- Known pitfalls
  - Importing charting lib in root bundle (must lazy-load); forgetting to validate data.

14. Risks, Assumptions, and Open Questions (Micro-Level)
- Risks: bundle size; large data; ambiguous deltas; a11y regressions; CSP breakage with third-party scripts.
- Mitigations: lazy load; data chunking; formal delta spec and tests; automated a11y checks; strict CSP with hashes.
- Assumptions: A1–A5; evergreen browsers; {Static_Host_A}.
- Open Questions: consolidate from Session section; block E4/E5 if unresolved beyond agreed deadline.

15. Definition of Done (Micro Level)
- Code: typed, lint/type clean; modules documented; public APIs stable.
- Tests: unit/integration ≥ targets; contract tests for data; e2e smoke green; performance budgets pass.
- Security: CSP present; dependency scan clean; URL validation; no PII.
- Docs: README, runbooks, data schema docs, CHANGELOG; provenance visible.
- Observability: version.json present; error beacon gated; metrics marks instrumented.
- Delivery: CI artifact built; preview deployed; release notes prepared; rollback path verified.

16. Appendices (optional)
A) Example app-config.json
```json path=null start=null
{
  "appName": "{Project_Name}",
  "dataBasePath": "/data",
  "defaultDataset": "cifar10",
  "defaultMetric": "acc_vs_edges",
  "defaultMethods": ["TGL","BaselineA"],
  "defaultPreset": "balanced",
  "featureFlags": { "latency": false, "roundsToTarget": false },
  "budgets": { "initialBundle": 1048576, "ttiMs": 2000, "toggleLatencyMs": 50 },
  "observability": { "beaconEnabledDefault": false, "beaconEndpoint": "", "analyticsEnabledDefault": false, "analyticsSrc": "" }
}
```
B) Example Lighthouse CI config
```json path=null start=null
{
  "ci": {
    "collect": { "startServerCommand": "pnpm serve", "url": ["http://localhost:4200/", "http://localhost:4200/explore"], "numberOfRuns": 3 },
    "assert": { "assertions": { "categories:performance": ["error", { "minScore": 0.9 }] } }
  }
}
```
C) Bundle size check script (sketch)
```js path=null start=null
import { statSync } from 'node:fs';
const budget = parseInt(process.argv.find(a=>a.startsWith('--budget'))?.split('=')[1]||"1048576",10);
const size = statSync('dist/app/browser/main.js').size; // adjust for hashed filename via glob
if (size > budget) { console.error(`Bundle ${size} > budget ${budget}`); process.exit(1); }
```
D) Environment variable catalog
- BUILD_DATA_VERSION, BEACON_ENDPOINT, ANALYTICS_SRC, ENABLE_ANALYTICS_DEFAULT, ENABLE_BEACON_DEFAULT.

Summary for Kickoff
- Decisions: Angular SPA with prerender; pnpm; JSON Schema + Ajv; lazy-loaded charting ({Charting_Option_B} default); static /data/vN layout; strict budgets/CSP; opt-in observability.
- Next steps: Resolve A1–A5; finalize schemas and sample data; scaffold Angular workspace with modules; wire manifest loader + URL state; choose charting lib; implement controls + chart with fixtures; set up CI with budgets and lighthouse; draft CSP and privacy copy.
