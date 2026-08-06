# Swift Theme — Decisions & Architect Review

Phase 1 output. Review of the Swift Theme architecture against the discovered
Frappe v16 + ERPNext UI layer. Written by the Lead Software Architect.

## Context

Swift Theme is a CSS/JS-first theme layer over Frappe v16 Desk + Website + Login,
with a server settings doctype, per-user boot prefs, accent/radius/density switching,
and a v1 glassmorphism login theme layered alongside a v2 rewrite.

## 1. Weaknesses

| # | Finding | Severity | Detail |
|---|---------|----------|--------|
| W1 | **v1/v2 settings schema mismatch** | **HIGH** | `doctype/swift_theme_settings/swift_theme_settings.json` still declares v1 fields (`color_mode`, `active_preset`, `gradient_*`, `pin_behavior`, sounds) while `install.py::_seed_settings()` and `api/boot.py` read v2 keys (`default_accent`, `default_density`, `default_radius`, `default_font_*`, `navbar_variant`, `enable_switcher`, `enable_command_palette`, `enable_focus_mode`, `enable_perf_mode`, `enable_styled_scrollbar`, `enable_toast_theming`, `enable_print_theming`, `login_layout`, brand fields). Result: users edit settings, nothing changes at boot — silent data loss / non-functional admin UI |
| W2 | **Redundant boot plumbing** | MED | `hooks.boot_session` AND `hooks.extend_bootinfo` both call `get_effective_prefs()`; two code paths, two sources of truth, double work per boot |
| W3 | **Duplicate login templates** | MED | Two byte-identical `www/login.html` copies (v1 path + v2 path); drift risk, wasted maintenance |
| W4 | **Legacy CSS selectors alive** | MED | `swift-desk.css` still targets legacy `data-swift-sidebar` + `#body .sidebar` while v2 JS writes `data-swift-sidebar-variant`; and v2 `data-swift-sidebar` semantics differ from v1 — pins/restore may silently no-op |
| W5 | **Dist committed, not built** | MED | Pre-built `public/css|js/*` committed; if SCSS sources exist, rebuild drift is likely; no `bench build` verification in CI |
| W6 | **Huge erpnext.bundle.js appended** | LOW | Whole ERPNext desk bundle loads for theme layer; unavoidable (framework), but Swift's own JS must not duplicate it |

## 2. Unnecessary complexity

- **Two theme modes / two sidebar code paths** (v1 `swift-sidebar.js` pinned group + v2 variant) — one should own it.
- **Custom shortcut handler** in Swift instead of `frappe.ui.keys.add_shortcut` (keys not shown in Frappe's Ctrl+F1 dialog).
- **Splash duplication**: frappe native `.splash` (desk) + Swift website `.swift-splash` + login glass intro — three loading screens to coordinate.
- **`swift-toast.css` + `swift-perf.css` + `swift-base.css`/`themes`/`desk`/`login`/`web`**: many small files vs one layered stylesheet — acceptable but must be documented (done in STYLING_GUIDE.md).

## 3. Future compatibility risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frappe v17 changes `data-theme`/`data-theme-mode` contract | Swift theming breaks wholesale | Pin to v16; watch frappe changelog; keep all selectors attribute-driven |
| Frappe drops `#body` container or renames `.layout-side-section` | sidebar/desk CSS breaks | Avoid deep DOM ids; prefer class hooks |
| Frappe moves from `esbuild` bundle names | `app_include_*` paths stale | Use hooks, never hardcoded dist paths |
| ERPNext `website_theme.js` SCSS import conflict | Portal theming breaks | Coordinate `@import` ordering with erpnext's injection |
| BS5 → BS6 in Frappe v17 | modal/navbar classes change | Layer over tokens, not components |

## 4. Better approach (recommended architecture)

1. **Reconcile settings schema now (pre-code):** migrate Doctype JSON to v2 field names; write `_seed_settings` from v2 keys; single `get_effective_prefs()` read in `extend_bootinfo` only; drop `boot_session` duplicate. Keep backward-compat reader for v1 keys during one release.
2. **Single source of truth for prefs:** one dataclass-like dict; JS reads only `bootinfo.swift_theme`; settings page writes via one whitelisted method.
3. **CSS layers, single entry:** one `swift-theme.bundle.scss` (or committed dist) using `@layer` — kills multi-file ordering bugs.
4. **Delete v1 login path**; keep v2 login + one `www/login.html` (or a `login_layout` switch inside one template).
5. **Sidebar: one variant contract.** Define `data-swift-sidebar="v2"` semantics; migrate v1 selectors; keep pins as pure CSS + one small JS, not two implementations.
6. **Register shortcuts via `frappe.ui.keys.add_shortcut`** so they appear in the help dialog.

## 5. Challenge the architecture

- **"CSS-first, no JS" is not quite true** — pins, palette, mode observer, toast already need JS; be honest that it's "CSS-first with thin JS decorators."
- **Is a full `swift_theme` app warranted vs a Website Theme?** Yes — desk theming requires hooks/app_include; a Website Theme alone can't do desk. Justified.
- **Double boot plumbing** proves the settings layer grew organically; the v1→v2 cutover was unfinished (schema + seeds + boot disagree). This is the #1 blocker to any feature work.
- **`get_effective_prefs` returns computed dict**; JS should treat it as immutable cache, recompute on save.

## 6. Tech-debt warnings before coding

- Fix W1 (settings schema) first — it blocks everything (admin edits no-op).
- Remove W2 duplicate boot read before adding any new pref.
- Collapse W3 duplicate login templates before touching login theming.
- Rename/migrate W4 legacy selectors; do not add new v1-style features.
- Add `bench build --app swift_theme` to a smoke check; ensure dist in sync with sources.
- Keep a compatibility shim reading v1 keys for one release; document removal.

## Decision register

| D# | Decision | Status |
|----|----------|--------|
| D1 | Stay CSS-first, thin-JS decorators, never patch `frappe.ui.*`/`frappe.views.*` | ADOPTED |
| D2 | Attribute-driven theming (`data-swift-*`) layered over Frappe tokens | ADOPTED |
| D3 | Drive all pref reads from `extend_bootinfo` single path | ADOPTED (Phase 3.2) |
| D4 | Reconcile settings schema v1→v2 before feature work | ADOPTED (Phase 3.2) |
| D5 | Collapse to one login template | RECOMMENDED |
| D6 | Single `@layer` stylesheet entry | RECOMMENDED |

---

# Phase 2 — Architect Review of the GoldElite Blueprint

Challenge of my own architecture. Where it is over-engineered, what to cut,
and the smallest architecture that still scales.

## Over-engineering risks

| # | Item | Verdict |
|---|------|---------|
| A1 | **Window Management (S11) + detachable views** | Biggest risk/reward gap. A full dock/cascade/multi-window metaphor is a product on its own. **Cut from v1** (already flagged off); keep the "detach = second route instance" idea as a spike only. Everything else ships without it |
| A2 | **Custom hyperscript/VDOM for S3** | Unnecessary. Frappe is DOM+jQuery; a tiny element builder (hyperscript) is enough. Do NOT build a mini framework or adopt a reactive library |
| A3 | **Plugin manifest + dependency graph (S13)** | Over-built for v1. Built-in modules need no manifest. Ship a **plain directory loader** (`plugins/` + `GE.registerPlugin`) with load-order array; grow a graph resolver only if third-party demand proves it |
| A4 | **15 systems** | Too many to reason about. Four pillars + core is the real shape (below). Several "systems" (perf layer, dev APIs) are horizontal slices, not systems |
| A5 | **Reactive store** | Over-engineering. Need: event emitter + localStorage sync + boot merge. No observables/subscriptions framework |
| A6 | **JS accent ladder (HSL math)** | Modern CSS `color-mix()`/`hsl()` can derive accent shades in stylesheet; drop the JS palette generator to a fallback |
| A7 | **z-index manager (S2)** | YAGNI. One documented z-index scale in tokens is enough |
| A8 | **Per-contract adapter file sprawl** | Group adapters by domain (boot, view, chrome, data) — ~4 files, not 15 |

## Unnecessary abstractions (cut list)

- Adapter class wrappers around plain functions; `Observable`-style wrappers; DI containers.
- Separate "hook" layer (S) distinct from systems — lifecycle hooks live inside `core/lifecycle.js`.
- Typed accessor layer over `frappe.boot.*` — read the object once, freeze a GE-side copy.

## Simplification: smallest architecture that scales

```
Core (P0):  GE namespace + events + registry + lifecycle + store
            + feature flags + settings (v1→v2)          → small, frozen API
Pillars:    1. Theme & Motion      (S1+S6)
            2. Layout & Navigation (S2+S4)              → 3 pillars ship in v1
            3. Components, Workspace, Search,
               Shortcuts, Notifications (S3+S5+S8+S9+S10)
Optional:   4. Windows (S11)                            → spike/flag, not v1
Horizontal: Dev APIs (S12) = core contract; Perf (S15) = discipline, not a system
```

- S13 Plugin System v1 = directory loader only (A3).
- S9 palette reuses Frappe's search endpoint; S8 wraps `frappe.ui.keys`; S10 extends
  realtime/`show_alert` — all thin, none replace Frappe infrastructure.
- Keep the **adapter + contract-check** pattern — it is the entire upgrade-safety story,
  not optional.

## What this cuts vs the full blueprint

- S11 windows: deferred (spike). S13 graph resolver: deferred. A5 store, A6 palette
  generator, A7 zindex: simplified. S15 perf: folded into RULES/PERFORMANCE_GUIDE.
- Effective v1 = core + 3 pillars (≈ S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S12,S14) with
  S11/S13-simple. Everything else stays as documented extensibility targets.

## Decision register (Phase 2 additions)

| D# | Decision | Status |
|----|----------|--------|
| D7 | Windows (S11) deferred to post-v1 spike; flag stays off | ADOPTED |
| D8 | S3 uses a hyperscript element builder, no VDOM/framework | ADOPTED |
| D9 | Plugin system v1 = directory loader + registration; graph later | ADOPTED |
| D10 | Store = emitter + localStorage sync (no reactive framework) | ADOPTED |
| D11 | Accent shades via CSS `color-mix()`; JS generator is fallback | ADOPTED |
| D12 | Adapters grouped into ~4 domain files (boot/view/chrome/data) | ADOPTED |
| D13 | Adapter + contract-check pattern is mandatory (upgrade safety) | ADOPTED |

---

# Phase 3.2 — Settings Engine Migration Decisions

Implementation decisions recorded during the v1→v2 settings cutover (Phase 3.2).

| D# | Decision | Status |
|----|----------|--------|
| D14 | Canonical settings schema versioned (`settings_schema_version = 2`); migration is idempotent + fill-if-empty — reruns are no-ops and never overwrite a set canonical value | ADOPTED |
| D15 | Legacy v1 fields are retained in the DocType inside a "Legacy (deprecated)" section and are never removed (backward-compat contract; removal deferred) | ADOPTED |
| D16 | Whitelisted API: unknown keys ignored, deprecated keys readable (`adapter.legacy`) but not settable; `set_user_pref` validates | ADOPTED |
| D17 | DocType JSON edited by hand (running site — Frappe restores from DB); requires bench-side validation before site sync | ADOPTED |
| D18 | Payload shape unchanged for clients: `swift-boot.js` localStorage keys, `swift-website.js` `get_effective_prefs`, and CSS `data-swift-sidebar-variant` values (`Attached|Floating|Icon-only`; v1 "Minimal" normalizes to "Icon-only") | ADOPTED |

---

# Phase 3.3 — D-003 Layout Engine Decisions

Implementation decisions recorded during the Layout Engine Foundation (Phase 3.3).

| D# | Decision | Status |
|----|----------|--------|
| D19 | Layout engine ships as a foundation only (state + registries + typed events); the S2 build-out (chrome replacement, sidebar/navbar redesign, z-index stack) is deferred to its own deliverable | ADOPTED |
| D20 | Layout events use the canonical `ge:layout:*` names (typed bus convention) and are mirrored onto the documented short names (`layout:ready`, etc.) so both contracts hold | ADOPTED |
| D21 | `layers.js` defines logical stacking order only — no styling, no z-index computation (explicit D-003 scope) | ADOPTED |
| D22 | Compatibility = read-only wrap: `frappe-chrome.js` probes/describes/wraps existing Frappe chrome and never re-parents, hides, or mutates it | ADOPTED |
| D23 | Layout lifecycle registers as a standard initializer (order 40) so it starts/stops with `GE.lifecycle` — no visual impact by default | ADOPTED |

---

# Phase 3.4 — D-004 Component Runtime Decisions

Implementation decisions recorded during the Component Runtime (Phase 3.4).

| D# | Decision | Status |
|----|----------|--------|
| D24 | Lifecycle is an explicit `OP` transition table (`created -> mounted -> enabled <-> disabled`, terminal `destroyed`); invalid transitions return `false`, idempotent operations are safe no-ops | ADOPTED |
| D25 | Dependencies initialize before their dependents; circular deps are rejected (`CIRCULAR_DEPENDENCY`, cycle-stack guard) and unknown deps are hard errors | ADOPTED |
| D26 | Creation is lazy — instances are built on first `mount`, never at `register`; a component-region element binding is out of scope (deferred to S2) | ADOPTED |
| D27 | Error isolation is per-entry (`failed` + `lastError`); a create/hook failure marks only that component and never blocks `destroyAll` or other mounts; `health()` exposes it | ADOPTED |
| D28 | Shared context is a single object per component exposing `GE/settings/layout/events/flags/registry/services/compat/log` — no direct global access | ADOPTED |
| D29 | Runtime teardown (`shutdown`) is separate from the per-component `destroy` (deliverable requirement); lifecycle order-45 registers `init`/`shutdown` | ADOPTED |
| D30 | `update` transitions only within mounted/enabled/disabled; `unmount` returns to `created` and emits no event (created is not a documented lifecycle event) | ADOPTED |

---

# Phase 3.5 — D-005 Design Token Engine Decisions

Implementation decisions recorded during the Design Token Engine (Phase 3.5).

| D# | Decision | Status |
|----|----------|--------|
| D31 | The engine ships theme-independent: it owns the 14-category taxonomy and mechanism only; no design values are baked in — themes define/import/override tokens later, and boot payloads (`frappe.boot.swift_theme.tokens`) are adopted when present | ADOPTED |
| D32 | Token names are dotted paths with lowercase kebab segments; category is explicit metadata or inferred from the first segment (unknown segments become the `semantic` category) | ADOPTED |
| D33 | Values are scalar (string/number/boolean) with per-category validation (`length`, `opacity` 0–1, integer `z-index`, etc.); alias values (`{path}`) skip type checks and resolve at read time | ADOPTED |
| D34 | Three reference mechanisms are distinct: aliases (`{path}`) resolve another token's value, `extends` inherits a parent's value, `fallback` supplies a value only when the token is unresolvable; all chains are cycle-detected | ADOPTED |
| D35 | Runtime overrides are stored separately from declared definitions — `set`/`setMany` never mutate definitions, making `reset()` a clean undo; `setMany` is atomic (validate-all-then-apply) | ADOPTED |
| D36 | Immutable tokens are protected at every write path (define-force, `set`, `setMany`, import replace) and preserved across `import` replace | ADOPTED |
| D37 | The CSS bridge (`--ge-*`) is opt-in infrastructure only and is never auto-applied — no visible UI change by default | ADOPTED |
| D38 | Import/export is schema-versioned (`goldelite.tokens` v1) with a forward migration registry; newer-than-supported payloads are rejected with a clear error | ADOPTED |
