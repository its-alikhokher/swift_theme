# Swift Theme — Memory

## Completed discoveries (Phase 0 — discovery only, no implementation)

- [x] Repository = Frappe v16 theme app `swift_theme` (fork of GoldElite lineage; **repo named Swift Theme**).
- [x] App wiring fully mapped: hooks.py, install.py, api/boot.py, config/desktop.py.
- [x] Two doctypes mapped: `Swift Theme Settings` (Single, v1 fields) + `Swift Theme Sound Event` (child).
- [x] Desk pipeline: 14 CSS files (9 desk, 7 web), 9 JS files, load orders captured.
- [x] Client boot chain (localStorage → attrs → bootinfo sync → after_ajax) documented.
- [x] Login: core frappe login page is the active route; themed via web_include assets + swift-website.js.
- [x] Whitelisted API surface (6 methods), realtime event, JS custom events, shortcuts.
- [x] Extension points catalogued (attributes, tokens, JS APIs, hooks).
- [x] **Critical bug found**: `Swift Theme Settings` DocType fields (v1) do NOT match what `install.py` seeds and `api/boot.py` reads (v2) → Settings has no effect on v2 prefs; seeds silently dropped.
- [x] **Other gaps**: missing `sounds/*.mp3`, missing `inter-var.woff2`, unwired `presets/*.json`, legacy v1 selectors in swift-desk.css, duplicate login.html, `swift_selected_theme` field never created, redundant `boot_session`+`extend_bootinfo`.

## Current task

Phase 0 repository discovery — documentation only.
Populated: ARCHITECTURE, FILE_STRUCTURE, BOOT_PROCESS, HOOKS_REFERENCE,
LOGIN_REFERENCE, ROUTING_GUIDE, OVERRIDE_GUIDE, MEMORY, CHANGELOG.

## Phase 1 — UI Entry-Point Discovery (DONE)

- [x] Frappe v16 desk shell mapped (`www/desk.py`+`desk.html`, `desk.js`, router, container/factory/pageview, workspace).
- [x] Frappe UI components mapped (page, toolbar/navbar, sidebar, dialog, messages, keyboard, theme_switcher, notifications).
- [x] Frappe website + login mapped (base.html/web.html, www/*.py pages, login.js, Website Theme).
- [x] Form/list/report/view subsystems mapped (form/, list/, views/ subdirs, widgets/, grids).
- [x] ERPNext UI surface mapped (hooks app_include/web_include/boot/sounds/route_rules, bundles, workspaces, portal templates, website_theme.js SCSS import).
- [x] Build pipeline mapped (frappe/build.py bundles, per-app dist).
- [x] Populated: UI_MAP, PAGES_REFERENCE, FORM_REFERENCE, LIST_REFERENCE, REPORT_REFERENCE,
  WEBSITE_REFERENCE, PORTAL_REFERENCE, COMPONENT_LIBRARY, DESIGN_SYSTEM, STYLING_GUIDE,
  SHORTCUTS_REFERENCE, EVENTS_REFERENCE, BUILD_SYSTEM, API_REFERENCE, DEPENDENCY_GRAPH, DECISIONS.
- [x] Architect Review written (DECISIONS.md W1–W6, D1–D6).
- [x] CHANGELOG.md appended with Phase 1 entry.

## Phase 2 — GoldElite Architecture Design (DONE)

- [x] Blueprint appended to ARCHITECTURE.md: 15 systems (S1–S15) each with purpose/responsibilities/
  dependencies/API/modules/Swift+Frappe connections/override/extensibility/risks.
- [x] Production directory structure designed (frontend/backend/components/services/stores/hooks/
  animations/layouts/styles/utilities/plugins/assets/icons/fonts/types/tests) — no files created.
- [x] Component inventory classified (Owned / Extended from Frappe / Left unchanged).
- [x] Implementation strategy per system (Replace/Extend/Inject/Wrap/Override/Compose) — zero frappe edits.
- [x] Feature flag registry designed (starter set, tiers, defaults).
- [x] Upgrade strategy (high/low-risk surfaces, adapter+contract-check, migration, frappe-compat.json).
- [x] Populated: PRD, RULES, PHASES, ROADMAP, PERFORMANCE_GUIDE, SECURITY_GUIDE, TESTING_GUIDE.
- [x] Phase 2 architect review appended to DECISIONS.md (A1–A8 cuts, D7–D13).
- [x] CHANGELOG.md appended with Phase 2 entry.

## Phase 3.1 — P0 Foundation: GoldElite runtime (DONE)

- [x] 10 infrastructure modules created under `public/js/goldelite/` (no features, no visual changes).
- [x] Single global `window.GoldElite` (`GE`); frozen `states` + `eventNames` (`ge:*`).
- [x] `hooks.py`: 10 GoldElite scripts appended to `app_include_js` (dependency-ordered, after the 7 swift files); `hooks.py` is the ONLY modified file.
- [x] `GE.util` (DOM-free helpers), `GE.log` (levels + ns), `GE.error` (typed codes/reporters/try/guard).
- [x] `GE.events` typed bus (pre-registers `ge:*` types, rejects unknown emits); `GE.registry` → `GE.services`/`GE.components`.
- [x] `GE.settings` schema-driven (defineSchema/get/set/validate/applyBoot); no v1→v2 migration yet (P0 scope boundary).
- [x] `GE.flags` (user/tenant/global tiers; 21-flag starter catalog seeded, safe defaults).
- [x] `GE.compat` contract registry (declarations only, no overrides; probes on demand).
- [x] `GE.lifecycle` (init/destroy/isReady/onReady, initializer registry, DOM-ready auto-init, multi-init guard).
- [x] Verified: `node --check` on all 10 files; full smoke test (load order → auto-init → 21 assertions) PASS; no leaked globals; `hooks.py` parses.

### Verification notes
- Two bugs caught by smoke test and fixed: `util.js` and `log.js` referenced `GE` without `var GE = global.GoldElite;` (strict-mode ReferenceError).
- Load order corrected: namespace MUST precede util (util sets `GE.util`).
- Design: `flags.isEnabled(unknown)` returns false (graceful); `flags.set(unknown)` throws (explicit).

## Phase 3.2 — P0 Foundation: Settings engine v1→v2 (DONE)

Resolved the #1 blocker (W1/D3/D4): canonical settings schema + migration layer + single boot path.
No UI/theme/feature work — migration layer only.

- [x] `settings_engine/` package (schema.py, validation.py, migrate.py, adapter.py, boot.py): canonical registry
  (36 fields, schema version 2) + legacy registry (all v1 fields marked deprecated), preset catalog, user prefs,
  `validate_doc`/`sanitize`, idempotent non-destructive migration, `adapter.get/set/legacy`, single boot assembly.
- [x] `api/boot.py` rewritten: `extend_bootinfo`/`get_effective_prefs`/`set_user_pref` delegate to settings_engine;
  `boot_session` removed; legacy `user_values()` kept as deprecation shim. `hooks.py` now has ONE boot hook.
- [x] `install.py`: seeds from `schema.defaults()` (deduped catalogs), runs `migrate.run()` on install/migrate,
  keeps `_ensure_user_fields()` (creates legacy `swift_selected_theme`).
- [x] `swift_theme_settings.json`: 36 canonical fields added; all v1 fields kept in a "Legacy (deprecated)"
  collapsible section; `sidebar_variant` options reconciled; orphaned `sidebar_section` re-homed.
- [x] Controller `swift_theme_settings.py`: `validate()` → `validation.validate_doc(self)`; legacy methods
  (`get_active_theme_config`, `play_sound`, `get_premium_themes`, `apply_theme`) marked DEPRECATED; `apply_theme`
  also writes canonical `swift_theme` when mapped.
- [x] Client `goldelite/systems/settings.js`: `GE.settings.adoptBoot(flat, ns)` + `init()` reads
  `frappe.boot.swift_theme` into the `"swift"` namespace.
- [x] Backend runs in host Python (no node/test runner): `python3 swift_theme/tests/run.py` runs 4 unittest modules.

### Verification
- 42 unit tests PASS (`python3 swift_theme/tests/run.py`).
- 40-check smoke `/tmp/opencode/settings_smoke.py` PASS (stubbed frappe).
- `node --check` PASS on settings.js, swift-boot.js, swift-website.js.
- DocType JSON not bench-validated (running site — Frappe restores from DB during a session).

### Key rules encoded (see DECISIONS.md D14–D18)
- Migration is idempotent + fill-if-empty: reruns are no-ops; a set canonical value is never overwritten.
- Legacy fields are NEVER removed (kept in the doc, marked deprecated).
- Unknown keys are ignored (whitelist); deprecated keys readable via `adapter.legacy`, not settable.
- Payload shape stays backward compatible: `swift-boot.js` local-storage keys + `swift-website.js`
  `get_effective_prefs` unchanged; CSS `data-swift-sidebar-variant` values unchanged (v1 "Minimal"→"Icon-only").

## Phase 3.3 — D-003 Layout Engine Foundation (DONE)

Infrastructure only. Central layout system for future GoldElite components; no visual changes, no Frappe
rendering changes (wrap only), no styling.

- [x] `systems/layout/` module tree (7 new files): `manager.js` (registerLayout/activateLayout/
  deactivateLayout/destroyLayout), `context.js` (viewport, mode, sidebar/navbar/floating state, content
  bounds, debounced resize observation), `layers.js` (logical layer order only — no styling), `regions.js`
  (8 standard regions + add/remove events), `responsive.js` (breakpoints, no CSS), `frappe-chrome.js`
  (read-only probe/wrap of existing Frappe chrome), `index.js` (assembles `GE.layout`, init/destroy/on,
  short-name event forwarders).
- [x] Events: `ge:layout:ready|resize|region-added|region-removed|changed` pre-registered in `namespace.js`;
  short names (`layout:*`) defined and forwarded for the documented contract.
- [x] `hooks.py`: 6 layout files appended to `app_include_js` (before `lifecycle.js`); `lifecycle.js` registers
  layout initializer (order 40) — same pattern as settings/flags/compat.

### Verification
- Headless smoke `/tmp/opencode/layout_smoke.js` — 39/39 PASS (load order, auto-init READY, ready/resize/
  region/changed events incl. short aliases, region register/remove, layer order, breakpoints, manager
  lifecycle, context bounds recompute, chrome probe/wrap, destroy/re-init, zero console errors).
- `node --check` PASS on all JS (goldelite + swift); `hooks.py` parses.
- Regression: settings unit tests (42) + settings smoke (40) still PASS.

### Boundaries
- S2 Layout Engine is deliberately NOT built out (no chrome replacement, no sidebar/navbar redesign).
- No CSS, no z-index/overlay stack yet — layers are logical ordering only.
- Chrome module is read-only (probe/describe/wrap); it never re-parents or hides Frappe elements.

## Phase 3.4 — D-004 Component Runtime (DONE)

Single lifecycle manager for every GoldElite UI module. Infrastructure only — no DOM work, no rendering,
no visible UI. Replaces the placeholder `GE.components` registry from P0.

- [x] `systems/components.js` — `GE.components`: state machine `created -> mounted -> enabled <-> disabled`,
  terminal `destroyed`; explicit `OP` transition table (invalid transitions rejected, idempotent no-ops);
  lazy creation on first mount; dependency-first resolution (`resolve`/`runDeps`) with `CIRCULAR_DEPENDENCY`
  rejection and cycle-stack guard; shared per-component context (`GE/settings/layout/events/flags/registry/
  services/compat/log`); typed events `ge:component:created|mounted|enabled|disabled|destroyed`;
  error isolation (`failed` + `lastError` per entry, one component's failure never blocks others);
  dev tools `list/state/health/order/inspect`; manager `register/unregister/resolve/mount/unmount/enable/
  disable/update/destroy/destroyAll/shutdown`.
- [x] `core/errors.js` +`CIRCULAR_DEPENDENCY` code; `core/namespace.js` +5 component event names;
  `core/registry.js` placeholder `GE.components` removed (real runtime owns the namespace now).
- [x] `core/lifecycle.js` initializer (order 45) — `init: GE.components.init`, `destroy: GE.components.shutdown`
  (runtime teardown is separate from per-component `destroy`).
- [x] `hooks.py`: `components.js` inserted between layout modules and `lifecycle.js`.

### Verification
- Headless smoke `/tmp/opencode/components_smoke.js` — 46/46 PASS (auto-init READY, transitions + idempotency,
  invalid transitions rejected, deps-first + circular rejection, lazy create, error isolation + `health().ok`,
  shared context, dev tools, shutdown/re-init, zero console errors).
- Bug caught and fixed by smoke: `GE.components.destroy` was bound to the runtime teardown (which wiped all
  `entries`); moved runtime teardown to `shutdown()` so `destroy(name)` is per-component as specified.
- Regression: layout smoke 39/39 PASS (order updated to include `components.js`, mirroring `hooks.py`),
  settings unit tests (42) + settings smoke (40) PASS, `node --check` PASS on all JS, `hooks.py` parses.

### Boundaries
- No element binding in the runtime (component-region binding deferred to S2). No visible UI.
- `update` only transitions within mounted/enabled/disabled; unmount emits no event (created is not a
  documented lifecycle event).

## Phase 3.5 — D-005 Design Token Engine (DONE)

Single source of truth for every GoldElite design value. Infrastructure only — no visible UI, no CSS
redesign, no theme values baked in. Ships the category taxonomy; themes define/import/override tokens later.

- [x] `systems/tokens/` module tree (5 new files): `registry.js` (store + 14-category taxonomy + validation +
  immutable-core protection + runtime overrides kept separate from declared values), `resolver.js`
  (get/resolve, alias refs `{path}`, declared `fallback`, `extends` inheritance, cycle detection),
  `io.js` (schema version 1 + migration registry + JSON import/export + reset), `css-bridge.js`
  (`--ge-*` custom-property bridge: varName/generate/apply/clear — infra only, never auto-applied),
  `index.js` (façade `GE.tokens`, runtime `set`/`setMany` (atomic), events, lifecycle, boot adoption).
- [x] `core/namespace.js` +4 token events; `core/errors.js` +`INVALID_TOKEN|UNKNOWN_TOKEN|IMMUTABLE_TOKEN|TOKEN_CYCLE`.
- [x] `core/lifecycle.js` tokens initializer (order 35 — before layout 40/components 45 so consumers can read tokens);
  `systems/components.js` `makeContext` gains `tokens` (Component Runtime integration).
- [x] `hooks.py`: 5 token files appended before `lifecycle.js`.

### Verification
- Headless smoke `/tmp/opencode/tokens_smoke.js` — 68/68 PASS (registry integrity, inheritance, alias chains +
  cycles, fallback behavior, runtime set/setMany atomicity + immutability, event emission, import/export
  round-trip + replace/merge + immutable skip, version handling, CSS bridge varName/generate/apply/clear +
  never-auto-applied, component-context integration, zero console errors).
- Regression: components smoke 46/46, layout smoke 39/39, settings unit tests (42) + settings smoke (40) PASS;
  `node --check` all JS; `hooks.py` parses. Smoke load orders updated to include token files.
- Bugs caught by smoke and fixed: `var overrides` (store) shadowed the `overrides()` getter; `valueOf` read the
  renamed store via the old identifier.

### Boundaries
- No theme-specific values in the engine — only the taxonomy and mechanism. Boot token payloads
  (`frappe.boot.swift_theme.tokens`) are adopted if present (future themes).
- CSS bridge is opt-in infrastructure; it is never invoked automatically, so no visible UI change.

## Next recommended task

1. **Phase 3.3** per PHASES.md: `ge.bundle.js` build/code-split scaffold + remaining P0 infra; then move to
   Pillar 1 (Theme & Motion) feature work on top of the now-canonical settings engine.
2. During P0: migrate legacy v1 selectors (W4) and collapse duplicate login templates (W3/D5).
3. Clean junk: `__pycache__/`, `*.pyc`, `*:Zone.Identifier` files.
4. Remaining empty placeholders (only if non-duplicative): REVERSE_ENGINEERING, AI_CONTEXT, README.
