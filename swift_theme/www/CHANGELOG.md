# Swift Theme — Changelog

## Phase 0 — Repository Discovery (2026-08-06)

Documentation-only phase. No code, CSS, JS, or schema changes.

### Updates made

| Doc | Change |
|-----|--------|
| ARCHITECTURE.md | Created — major systems, dependency graph, execution order, v1/v2 schema mismatch finding |
| FILE_STRUCTURE.md | Created — full tree with responsibilities, CSS/JS load-order tables, junk-file notes |
| BOOT_PROCESS.md | Created — install/migrate → server boot → client boot → website boot chains |
| HOOKS_REFERENCE.md | Created — all hooks, whitelisted methods, custom events, shortcuts |
| LOGIN_REFERENCE.md | Created — active (core) vs standalone (v1) login paths, CSRF notes |
| ROUTING_GUIDE.md | Created — desk SPA / API / www / workspace routing layers |
| OVERRIDE_GUIDE.md | Created — attribute/token/JS-API/backend extension surface + risks |
| MEMORY.md | Created — discovery checklist, current task, next tasks |
| CHANGELOG.md | Created — this file |

### Key findings recorded

1. Settings DocType field set (v1) does not match install.py seed + api/boot.py reads (v2).
2. Missing assets: sounds/*.mp3, fonts/inter-var.woff2.
3. Unwired: public/presets/*.json, `swift_theme_updated` realtime event, standalone www/login.html route.
4. Legacy v1 selectors in swift-desk.css vs v2 attribute naming.

## Phase 1 — UI Entry-Point Discovery (2026-08-06)

Documentation-only phase. Reverse-engineered the Frappe v16 + ERPNext UI layer only;
no code, CSS, JS, or schema changes.

### Docs populated (empty placeholders → filled)

| Doc | Content |
|-----|---------|
| UI_MAP.md | Master map — 8 UI areas (login, desk shell, forms, lists, reports, dialogs, website, ERPNext) with element/renderer/JS/CSS/hook/override/risk tables |
| PAGES_REFERENCE.md | Desk shell chrome: boot, navbar, sidebar, workspace, page container, breadcrumbs, search, notifications, user menu, theme switcher, splash |
| FORM_REFERENCE.md | FormFactory → `frappe.ui.form.Form`, toolbar, timeline, form sidebar, grids, quick entry, save/workflow |
| LIST_REFERENCE.md | ListFactory/ListView, rows/sidebar/filters, alternate views (report/kanban/calendar/tree/gantt/image/file/dashboard/map) |
| REPORT_REFERENCE.md | QueryReport, datatable, frappe-charts, dashboard widgets |
| WEBSITE_REFERENCE.md | base.html/web.html template stack, server pages (login/error/404/me/list/printview/portal), web forms, Website Theme |
| PORTAL_REFERENCE.md | portal.py row rendering, ERPNext `website_route_rules` (`/orders`, `/invoices`, `/supplier-quotations`), portal templates, SCSS |
| COMPONENT_LIBRARY.md | Modal/Dialog/Confirm/Prompt, toast/alert, awesomebar, dropdowns, tables/grids, filters, indicators |
| DESIGN_SYSTEM.md | Frappe tokens (`css_variables.scss`, `--navbar-height`, `--page-max-width`), dark.scss, Swift layer/attribute system |
| STYLING_GUIDE.md | Principles, selector scoping, accent maps, density/radius, file responsibilities, verification |
| SHORTCUTS_REFERENCE.md | `frappe.ui.keys` API, standard shortcuts, Swift shortcuts |
| EVENTS_REFERENCE.md | `app_ready`, `page_change`, `toolbar_setup`, `boot`, `shown.bs.modal`, MutationObserver theme events, realtime channels, Swift custom events |
| BUILD_SYSTEM.md | `frappe/build.py` bundle pipeline, frappe/erpnext/Swift bundles, rebuild command, risk notes |
| API_REFERENCE.md | Swift whitelisted endpoints, frappe endpoints consumed, context injection, v1/v2 boot issue |
| DEPENDENCY_GRAPH.md | Swift↔Frappe↔ERPNext dependency + load-order tables |
| DECISIONS.md | **Architect Review** — weaknesses (W1–W6), complexity, compatibility risks, recommended architecture, decision register |

### Key Phase 1 findings

1. Desk = JS SPA (`desk.py`+`desk.html` shell → `frappe.app` boot → `Sidebar`/`Toolbar`/`Container`); website = server-rendered Jinja. Swift CSS-first approach fits both.
2. Frappe owns `data-theme`/`data-theme-mode` + `frappe.ui.set_theme()`; Swift layers `data-swift-*` on top (must never overwrite).
3. Native override surface: `app_include_*`, `web_include_*`, `boot_session`/`extend_bootinfo`, `sounds`, `website_route_rules`, Website Theme SCSS import (ERPNext `website_theme.js` precedent).
4. High-risk targets: router, core login method, desk shell, POS. Safe: token/variable + attribute-scoped CSS.
5. Confirmed Phase 0 critical bug still the #1 blocker (settings schema v1/v2 mismatch) — full analysis in DECISIONS.md (W1–W6, D1–D6).

## Phase 2 — GoldElite Architecture Design (2026-08-06)

Architecture-only phase. No files created, no code, no CSS/JS/Vue.

### Docs updated

| Doc | Change |
|-----|--------|
| ARCHITECTURE.md | Appended **Phase 2 blueprint**: conventions, 15 systems S1–S15 (purpose/responsibilities/dependencies/API/modules/Swift+Frappe connections/override/extensibility/risks), production directory structure, component inventory (Owned/Extended/Unchanged), implementation-strategy matrix, feature-flag registry, upgrade strategy |
| PRD.md | Populated — vision, principles, personas, scope, non-goals, success criteria |
| RULES.md | Populated — R1–R10 engineering rules, code conventions, safety gates, doc rules |
| PHASES.md | Populated — P0–P6 sequencing with exit criteria + dependencies |
| ROADMAP.md | Populated — M1–M7 milestones, estimates, critical path, gate reviews, risks |
| PERFORMANCE_GUIDE.md | Populated — budgets, boot impact, asset gating, DOM discipline, metrics |
| SECURITY_GUIDE.md | Populated — backend/client/flag security + test requirements |
| TESTING_GUIDE.md | Populated — test pyramid, key cases, CI gates, regression discipline |
| DECISIONS.md | Appended **Phase 2 architect review**: A1–A8 over-engineering/cut list, "smallest architecture that scales" (core + 3 pillars), D7–D13 decisions |
| MEMORY.md | Updated — Phase 2 done, next = Phase 3 P0 implementation |
| CHANGELOG.md | Appended — this entry |

### Key decisions (see DECISIONS.md)

1. GoldElite = Desktop Experience Layer, not a CSS theme; zero edits to frappe/erpnext core.
2. All Frappe access via `services/frappe/*` adapters + boot-time contract checks (upgrade safety).
3. v1 = core (GE namespace, store, events, flags, settings) + 3 pillars (Theme&Motion, Layout&Nav,
   Components/Workspace/Search/Shortcuts/Notify). Windows (S11) + full plugin graph (S13) deferred.
4. Every capability behind a feature flag (S14) with safe default; lazy-loaded assets per flag.
5. Settings v1→v2 migration is P0 (Phase 3) top priority — remains the #1 blocker (W1/D3/D4).

## Phase 3.1 — P0 Foundation: GoldElite runtime (2026-08-06)

First implementation phase. Infrastructure only — no user-facing features, no visual changes,
no Frappe/ERPNext core edits, no CSS/Vue.

### Changed files

| File | Change |
|------|--------|
| `hooks.py` | Appended 10 GoldElite scripts to `app_include_js` after the existing 7 swift files (dependency-ordered) |

### Created files (`public/js/goldelite/`)

| Module | API |
|--------|-----|
| `core/namespace.js` | `window.GoldElite` (`GE`), frozen `states` + `eventNames`, idempotent creation |
| `utilities/util.js` | `GE.util` — type checks, clone/merge/assign/pick/omit, get/setPath, guid, defer, once, debounce, throttle, isEqual |
| `core/log.js` | `GE.log` — levels debug<info<warn<error<silent, `ns()`, setLevel/getLevel/isEnabled |
| `core/events.js` | `GE.events` — typed bus, pre-registered `ge:*` types, define/on/once/off/emit/…, unknown-emit rejected |
| `core/errors.js` | `GE.error` — `GoldEliteError` + 14 codes, report/onReport/try/guard, `ge:error:reported` |
| `core/registry.js` | `GE.registry.create` → `GE.services` + `GE.components` (lazy singletons, deps, teardown) |
| `systems/settings.js` | `GE.settings` — schema-driven defineSchema/get/set/validate/applyBoot, memory cache, events |
| `systems/flags.js` | `GE.flags` — user/tenant/global tiers, 21-flag starter catalog seeded, safe defaults |
| `services/compat.js` | `GE.compat` — contract registry (declarations only, on-demand probes, no overrides) |
| `core/lifecycle.js` | `GE.lifecycle`/`GE.init`/`GE.destroy`/`GE.isReady`/`GE.onReady`, initializer registry, DOM-ready auto-init |

### Verification

1. `node --check` passed on all 10 modules.
2. Headless smoke test (mock window/document, exact hooks load order): load → DOM-ready auto-init →
   READY; 21 assertions on util/settings/flags/compat/events/registry/lifecycle/errors all PASS.
3. No leaked globals beyond the single `GoldElite`.
4. Bugs found & fixed during verification: `util.js` and `log.js` missing `var GE = global.GoldElite;`
   (strict-mode ReferenceError); load order corrected so `namespace.js` precedes `util.js`.

### Notes / boundaries

- Settings **v1→v2 migration is NOT in this prompt's scope** — foundation only; migration is next
  (Phase 3.2, #1 blocker W1/D3/D4).
- No backend (`api/boot.py`), no `extend_bootinfo` changes, no build changes yet.

## Phase 3.2 — P0 Foundation: Settings engine v1→v2 migration (2026-08-06)

Resolved the #1 blocker (W1/D3/D4): one canonical settings schema, a migration layer + compatibility adapter,
a single boot path, centralized validation, and deprecation markers. No UI/theme/feature work.

### Created files

| File | Change |
|------|--------|
| `settings_engine/__init__.py` | Package exports; public API `run_migration()` (renamed from `migrate()` to avoid module shadowing) |
| `settings_engine/schema.py` | Canonical registry (36 fields, `SCHEMA_VERSION = 2`, `settings_schema_version` field), legacy registry, preset catalog, user-pref fields, `defaults()` |
| `settings_engine/validation.py` | `validate_doc`, `sanitize`, `normalize_*` helpers, `_is_empty` (fill-if-empty support) |
| `settings_engine/migrate.py` | Pure `apply_settings_migrations`/`apply_user_migration` + `migrate_settings`/`migrate_user_prefs`/`run` (idempotent, non-destructive) |
| `settings_engine/adapter.py` | `get`/`set`/`legacy`/`get_all`/`deprecated` — canonical values regardless of storage |
| `settings_engine/boot.py` | `extend_bootinfo` payload assembly, `get_effective_prefs`, `set_user_pref` (whitelisted, validated) |
| `swift_theme/tests/` | `__init__.py`, `run.py` (runner + frappe stub), `test_settings_{schema,validation,migration,adapter}.py` |

### Changed files

| File | Change |
|------|--------|
| `api/boot.py` | Rewritten — `extend_bootinfo`/`get_effective_prefs`/`set_user_pref` delegate to settings_engine; `boot_session` removed; `user_values()` kept as deprecation shim |
| `hooks.py` | Removed duplicate `boot_session` hook — single `extend_bootinfo` boot path |
| `install.py` | Seeds from `schema.defaults()` (deduped catalogs), runs `migrate.run()` on after_install/after_migrate, keeps `_ensure_user_fields()` |
| `doctype/swift_theme_settings/swift_theme_settings.json` | +36 canonical fields; v1 fields kept in "Legacy (deprecated)" section; `sidebar_variant` options reconciled; orphaned `sidebar_section` re-homed. Not bench-validated (running site) |
| `doctype/swift_theme_settings/swift_theme_settings.py` | `validate()` → `validation.validate_doc`; legacy methods (`get_active_theme_config`, `play_sound`, `get_premium_themes`, `apply_theme`) marked DEPRECATED; `apply_theme` also writes canonical `swift_theme` |
| `public/js/goldelite/systems/settings.js` | `GE.settings.adoptBoot(flat, ns)` + `init()` reads `frappe.boot.swift_theme` into `"swift"` namespace |

### Verification

1. `python3 swift_theme/tests/run.py` — 42 unit tests PASS (schema/validation/migration/adapter).
2. `/tmp/opencode/settings_smoke.py` (stubbed frappe) — 40/40 PASS incl. idempotency, boot payload, user-pref migration, `boot_session` removal.
3. `node --check` PASS on settings.js, swift-boot.js, swift-website.js.
4. Backward-compat preserved: `swift-boot.js` localStorage keys, `swift-website.js` `get_effective_prefs`, and `data-swift-sidebar-variant` CSS values unchanged.

### Notes / boundaries

- Migration is idempotent + fill-if-empty: reruns are no-ops; canonical values already set are never overwritten;
  legacy fields are never removed (kept in the doc, marked deprecated).
- DocType JSON edited by hand, not run through `bench validate` (running site — Frappe restores DocType JSON from
  DB during a session). Needs a bench-side verification before any site sync.

## Phase 3.3 — D-003 Layout Engine Foundation (2026-08-06)

Infrastructure only. Centralized layout system for future GoldElite components — the single source of truth
for page structure. No visual changes by default; wraps existing Frappe layout, never modifies it. No styling.

### Created files (`public/js/goldelite/systems/layout/`)

| File | API |
|------|-----|
| `manager.js` | Layout Manager — `registerLayout`, `activateLayout`, `deactivateLayout`, `destroyLayout`, `active`, `isActive`, `has`, `list`, `reset` |
| `context.js` | Layout Context — viewport, desktop/mobile mode, sidebar/navbar/floating state, content bounds; debounced resize observation (`observe`/`stop`/`set`/`get`/`update`) |
| `layers.js` | Layer System — logical layer registry (background/content/floating/overlay/modal/toast/tooltip) with ordering (`register`/`unregister`/`exists`/`index`/`above`/`below`/`list`). No styling |
| `regions.js` | Region Registry — 8 standard regions (header/sidebar/content/footer/right-panel/overlay/command-palette/notification-area); `register`/`has`/`get`/`setVisibility`/`remove`/`list`; emits region-added/region-removed |
| `responsive.js` | Responsive Service — `define` breakpoints (mobile<768, tablet 768–1023, desktop≥1024), `match`/`current`/`isMobile`/`isTablet`/`isDesktop`. No CSS |
| `frappe-chrome.js` | Compatibility — read-only `probe`/`describe`/`wrap` of existing Frappe chrome (`#navbar`, `.layout-side-section`, `.main-section`); never re-parents or hides |
| `index.js` | Façade — assembles `GE.layout`, `init`/`destroy`/`on`, `snapshot`, short-name event forwarders |

### Changed files

| File | Change |
|------|--------|
| `core/namespace.js` | +5 layout event names pre-registered: `ge:layout:ready`, `ge:layout:resize`, `ge:layout:region-added`, `ge:layout:region-removed`, `ge:layout:changed` |
| `core/lifecycle.js` | Registered layout initializer (order 40) — init/destroy with GE |
| `hooks.py` | 6 layout modules appended to `app_include_js` after `compat.js`, before `lifecycle.js` (dependency order preserved) |

### Events (typed, via existing `GE.events` bus)

Canonical `ge:layout:*` names are mirrored onto the documented short names (`layout:ready`, `layout:resize`,
`layout:region-added`, `layout:region-removed`, `layout:changed`). Subscribe with either form.

### Verification

1. Headless smoke `/tmp/opencode/layout_smoke.js` — 39/39 PASS (load order, auto-init READY, all five events
   incl. short aliases, region add/remove, layer ordering + rejection, breakpoint matching, manager lifecycle,
   content-bounds recompute, chrome probe/wrap, destroy/re-init, zero console errors).
2. `node --check` PASS on every JS file (goldelite + swift); `hooks.py` parses.
3. Regression: settings unit tests (42) + settings smoke (40) still PASS.

### Notes / boundaries

- S2 Layout Engine is NOT built out yet: no chrome replacement, no sidebar/navbar redesign, no z-index stack.
  This is the foundation (state + registry + events) only.
- `layers.js` is logical ordering only — explicit "no styling" per D-003.
- `frappe-chrome.js` is a read-only wrapper: probe/describe/wrap never mutate the DOM.

---

## Phase 3.4 — D-004 Component Runtime (2026-08-06)

Unified lifecycle manager for every GoldElite UI module. Infrastructure only — no DOM work, no rendering,
no visible UI. Replaces the P0 placeholder `GE.components` registry.

### Created file (`public/js/goldelite/systems/components.js`)

`GE.components` — Component Runtime:

| Area | API |
|------|-----|
| State machine | `created -> mounted -> enabled <-> disabled`, terminal `destroyed`; explicit `OP` transition table; invalid transitions return `false`, idempotent operations are safe no-ops |
| Manager | `register`, `unregister`, `resolve`, `get`, `has`, `mount`, `unmount`, `enable`, `disable`, `update`, `destroy` (per-component), `destroyAll`, `shutdown` (runtime teardown) |
| Deps | `resolve`/`runDeps` — dependency-first initialization; `CIRCULAR_DEPENDENCY` rejected (cycle-stack guard); unknown deps rejected |
| Context | `makeContext` — shared `GE/settings/layout/events/flags/registry/services/compat/log` per component |
| Events | `ge:component:created|mounted|enabled|disabled|destroyed` (typed bus, pre-registered) |
| Isolation | per-entry `failed` + `lastError`; a create/hook failure marks that component only — others unaffected |
| Dev tools | `list`, `state`, `size`, `inspect`, `health` (`report.ok`), `order` |

### Changed files

| File | Change |
|------|--------|
| `core/namespace.js` | +5 component event names pre-registered (`ge:component:*`) |
| `core/errors.js` | +`CIRCULAR_DEPENDENCY` error code |
| `core/registry.js` | Removed the placeholder `GE.components = createRegistry(...)`; registry docstring updated (`GE.services` + `GE.registry.create` kept) |
| `core/lifecycle.js` | Registered components initializer (order 45) — `init: GE.components.init`, `destroy: GE.components.shutdown` |
| `hooks.py` | `components.js` appended between the layout modules and `lifecycle.js` in `app_include_js` |

### Verification

1. Headless smoke `/tmp/opencode/components_smoke.js` — 46/46 PASS (auto-init READY; full transition matrix
   + idempotency; invalid transitions rejected; deps-first + circular rejection; lazy create on mount; error
   isolation with `health().ok`; shared context; dev tools; shutdown/re-init; zero console errors).
2. Regression: layout smoke 39/39 PASS (`layout_smoke.js` order updated to include `components.js`, mirroring
   `hooks.py`); settings unit tests (42) + settings smoke (40) PASS.
3. `node --check` PASS on all JS (goldelite + swift); `hooks.py` parses.

### Notes / boundaries

- No element binding in the runtime — component-to-region binding is deferred to S2.
- `update` only transitions within mounted/enabled/disabled; `unmount` emits no event (created is not a
  documented lifecycle event).
- Runtime teardown (`shutdown`) is intentionally separate from per-component `destroy` — the smoke caught a
  bug where `GE.components.destroy` wiped every registered entry.

---

## Phase 3.5 — D-005 Design Token Engine (2026-08-06)

Centralized design-token system — the single source of truth for design values. Infrastructure only:
no visible UI, no CSS redesign, no theme values baked in.

### Created files (`public/js/goldelite/systems/tokens/`)

| File | API |
|------|-----|
| `registry.js` | Token store — `define`, `getDefinition`, `has`, `list`, `count`, `allDefinitions`, `categoryOf`, `validateValue`, `validate`, `valueOf`, `setValue`, `overrides`, `clearOverride`, `resetOverrides`, `clear`, `categories`. 14-category taxonomy (color/typography/spacing/radius/border/elevation/opacity/motion/breakpoint/layout/icon/shadow/z-index/timing) with per-category value validation; immutable-token protection; runtime overrides stored separately from declared values |
| `resolver.js` | Resolution — `resolve` (strict), `get` (safe), `resolveMap`. Alias references `{path}`, declared `fallback`, `extends` inheritance, cycle detection across the whole chain |
| `io.js` | Serialization — schema `goldelite.tokens` v1, `version`, `registerMigration`/`migrate`, `export`/`exportJSON`, `import`/`importJSON` (replace/merge, immutable skip), `reset` |
| `css-bridge.js` | CSS bridge — `varName`, `generate`, `apply`, `clear` (`--ge-*`); opt-in only, never auto-applied |
| `index.js` | Façade `GE.tokens` — `Events`, `define`, `has`, `get`, `resolve`, `set`, `setMany` (atomic), `reset`, `import`, `importJSON`, `export`, `exportJSON`, `schemaVersion`, `registerMigration`, `list`, `count`, `categories`, `all`, `describe`, `validate`, `init`, `destroy` |

### Changed files

| File | Change |
|------|--------|
| `core/namespace.js` | +4 event names pre-registered: `ge:tokens:loaded`, `ge:tokens:changed`, `ge:tokens:reset`, `ge:tokens:validated` |
| `core/errors.js` | +`INVALID_TOKEN`, `UNKNOWN_TOKEN`, `IMMUTABLE_TOKEN`, `TOKEN_CYCLE` codes |
| `core/lifecycle.js` | Registered tokens initializer (order 35) — between compat (30) and layout (40) |
| `systems/components.js` | Component context (`makeContext`) gains `tokens: GE.tokens` |
| `hooks.py` | 5 token files appended between `components.js` and `lifecycle.js` in `app_include_js` |

### Events (typed, via the existing `GE.events` bus)

`ge:tokens:loaded` (count/imported/skipped/version), `ge:tokens:changed` (names/values/previous),
`ge:tokens:reset` (count of cleared overrides), `ge:tokens:validated` (ok/issues/count).

### Verification

1. Headless smoke `/tmp/opencode/tokens_smoke.js` — 68/68 PASS.
2. Regression: components smoke 46/46, layout smoke 39/39 (both load orders updated to include token files),
   settings unit tests (42) + settings smoke (40) PASS.
3. `node --check` PASS on all JS; `hooks.py` parses.

### Notes / boundaries

- The engine ships with no design values — only the category taxonomy and the mechanism. Themes
  (future deliverables) define/import/override tokens; boot payloads (`frappe.boot.swift_theme.tokens`)
  are adopted when present.
- The CSS bridge is opt-in infrastructure only and is never invoked automatically.
