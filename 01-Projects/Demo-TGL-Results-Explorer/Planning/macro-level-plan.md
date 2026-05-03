# Macro-Level Plan

## 1) Requirement Clarification

- Purpose and outcome
  - Build a static, no-backend TGL Results Explorer that demonstrates push–gossip–pull via a simple 3-step hero and lets users explore precomputed results.
  - Primary value: compare TGL presets versus baselines by Accuracy vs Edges per Round (MVP), with options to view latency and rounds-to-target (Phase 2).
- Audience
  - Reviewers, practitioners, decision makers; no math background required.
- Primary user journeys
  - Landing hero: 3-step visual walkthrough (Push → Gossip → Pull) with short captions and subtle, accessible motion.
  - Results Explorer: select dataset(s) (CIFAR‑10, FEMNIST, AG‑News), choose methods (TGL + baselines), view curves, inspect tooltips/deltas, click points for run details, download/share exact view.
  - Learn more: brief recap + pseudocode + links to paper/code.
- Information architecture & layout
  - Header (title + anchors: Explore, Learn, Data, Paper)
  - Hero (3 SVG steps, reduced motion respected)
  - Explore (left control panel; right chart; table below; Phase 2: Ablations tab)
  - Footer (recap, resources, licenses, provenance)
- Explore controls (MVP unless noted)
  - Dataset picker (single or multi-select; default 1)
  - Metric group: Accuracy vs Edges/round (default); Latency vs Edges (if available, Phase 2); Rounds-to‑X% (Phase 2; X configurable)
  - Methods: checkboxes (TGL + baselines), color-coded legend sync
  - TGL presets: radio options (Leaf‑light, Balanced, Relay‑rich, High‑mixing) mapped to nr/blr/brr/brl with tooltips
  - Display options: deltas vs best baseline, smoothing on/off, log/linear X
  - Share/download: Copy link, Download JSON/CSV, Reset
- Charts & interactions
  - Multi-series line chart (primary: Accuracy vs Edges/round)
  - Hover crosshair + stacked tooltip with series values and deltas vs selected baseline
  - Legend toggles; series focus on hover
  - Click point → Run Details panel (method/config, edges breakdown, seeds/variance, provenance, link to raw JSON slice)
- Data model & ingestion (static hosting)
  - Collection manifest enumerating datasets, metrics, methods
  - Curves payload per dataset+metric (or aggregated) with precomputed edges_per_round and provenance; table view is flattened CSV equivalent
  - All data versioned and loaded from /data/
- MVP vs Phase 2
  - MVP: hero; Results Explorer with Accuracy vs Edges; dataset selector; method toggles; 3–4 TGL presets; tooltips; run details; download/share; basic table; footer
  - Phase 2: latency, rounds-to-target; Ablations; variance bands; figure drill‑down
- Non-functional requirements
  - Performance: initial load <1 MB; TTI <2 s; charts render <50 ms on toggle; 60 fps animations; graceful reduced-motion
  - Accessibility: keyboard nav, ARIA, color‑blind safe palette, high contrast option, alt text for hero
  - Privacy/security: no tracking by default; optional anonymized analytics via explicit toggle; no server-side storage
  - Observability: client‑side error reporting (console + beacon) and visible data provenance
- Tech suggestions (non-binding)
  - Frontend: React/Svelte/Vue with Vite
  - Charts: Vega‑Lite or ECharts; export PNG/CSV/JSON
  - State/share links: URL query params
  - Content: SVG hero, CSS transitions only
- Data acquisition plan
  - Prefer author-provided CSV/JSON for figures; else digitized curves; else minimal reproductions; include seeds/variance when feasible; document provenance and licenses
- Success criteria
  - Within 30s, a visitor can select a dataset and see TGL outperforming at lower/equal communication for at least one preset
  - Shareable link reproduces exact view
  - Downloaded CSV/JSON matches chart series exactly; checksum logged at build
  - Hero communicates push–gossip–pull at a glance

### Ambiguities, contradictions, and missing information
- Project namespace
  - Exact project folder/name and branding (site name, logo, favicon).
- Baselines & scope
  - Final baseline list for launch; whether FL is included and how to define edges/round for FL to maintain fairness.
- TGL presets
  - Canonical preset names and parameter mappings (nr, blr, brr, brl, nl) per dataset; are presets global or dataset-specific?
- Metrics
  - Which datasets have latency; default targets for rounds-to‑X%; rounding/precision standards for tooltips/tables.
- Multi-dataset behavior
  - When multiple datasets are selected, are series overlaid in one chart, faceted, or tabbed? Default behavior?
- Deltas vs baseline
  - What constitutes the "best baseline" (among which set; by max accuracy at same x; nearest‑x interpolation allowed)? Handling of unequal x-grids between series.
- Smoothing
  - Smoothing method (moving average, LOESS, Savitzky–Golay), window/params, and whether it applies to y, x, or both; visual affordance when smoothing is on.
- Run details
  - Required fields for edges/round breakdown; how variance is represented (std, CI, quantiles); handling missing seeds.
- Data format & versioning
  - Final file organization under /data/; naming scheme; version tags in filenames vs a manifest; URL share scheme includes data version?
- Observability
  - Destination for beacon (no backend): third‑party endpoint, static host analytics API, or disabled by default? Error taxonomy to report.
- Accessibility & design system
  - Color palette (color‑blind safe), typography, dark/high‑contrast modes, keyboard flow order, focus styling.
- Performance budget enforcement
  - Target devices/network for TTI measurement; bundle size allocation (app vs chart lib vs SVG); lazy-loading strategy for charts/data.
- Charting library choice
  - Vega‑Lite vs ECharts vs lighter alternatives (e.g., uPlot); impact on <1 MB budget and export requirements.
- Sharing
  - Exact URL param schema; max URL length constraints; whether to support URL shortening.
- Downloads
  - File naming, CSV delimiter/locale, timezone/number formatting; whether to include provenance columns by default.
- Hosting & CI
  - Chosen static host; CI steps for data validation and checksum logging; cache headers for /data/; invalidation/versioning policy.
- Legal & compliance
  - Licenses and attributions for curves/assets; embargo or approval requirements for publishing numbers/labels.
- Browser support
  - Minimum browser versions; mobile/responsive requirements.

## 2) Questions

1) Scope and data
- Which baselines are in-scope at launch? Include/exclude FL? If FL is included, how do we define edges/round for FL?
- Can you provide the canonical TGL preset names and parameter values (nr, blr, brr, brl, nl) per dataset?
- Which datasets include latency measurements? What default targets should we use for rounds-to‑X% (per dataset)?
- Do we overlay multiple datasets in a single chart, facet them, or restrict to one at a time by default?
- How should we compute deltas vs "best baseline" (candidate set, tie-breaking, interpolation for mismatched x-values)?

2) Data packaging & versioning
- Confirm the /data/ directory structure and file naming conventions (per dataset+metric vs aggregated files).
- Should data files embed a version field, or do we encode versioning in filenames/manifest? Include data version in shareable URLs?
- What variance fields will be present (std, CI 95%, quantiles), and at what granularity (per point, per series)?

3) UX specifics
- Preferred smoothing algorithm and parameters; default on/off state.
- Tooltip precision/units and number formatting; default sort in the table (by method, accuracy, edges?).
- For Run Details, confirm required fields and the exact formula text to display for edges/round breakdown.
- For sharing, define the URL schema (datasets, methods, presets, metric, axes scale, smoothing, baseline target). Any URL length constraints or need for a shortlink?
- For downloads, confirm CSV/JSON column set and file naming pattern; include provenance fields by default?

4) Design & accessibility
- Approve or provide a color‑blind safe palette and typography; do we support dark and high-contrast modes at launch?
- Any branding assets (name, logo, favicon) or style guidelines to follow?
- Accessibility requirements beyond ARIA/keyboard/alt text (e.g., WCAG level target)?

5) Performance & technical choices
- Target device and network profile for measuring TTI <2 s (e.g., "modern laptop" spec)?
- Charting library preference given <1 MB initial load (Vega‑Lite vs ECharts vs lighter alternatives) and need for PNG/CSV export.
- Hosting choice among {A|B|C}; CDN/caching strategy for /data/; desired cache headers and invalidation approach.
- Browser support matrix and mobile responsiveness expectations.

6) Observability, privacy, and legal
- Should client-side beacons be enabled by default? If yes, what endpoint/provider to use without a backend?
- Preferred privacy-friendly analytics provider for the optional toggle (e.g., Plausible, Umami) or defer entirely?
- Licenses/attributions for datasets, curves, and assets; any publication embargo or approval workflow?
