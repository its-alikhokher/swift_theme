# Swift Theme — Architecture

App: `swift_theme` (Frappe v16 theme layer for Desk, Website/Portal, Login).
No ERPNext-specific code — themes ERPNext views via generic Frappe CSS classes.

## Major systems

| System | Entry point | Scope |
|--------|-------------|-------|
| v2 Preference engine | `api/boot.py` + `install.py` + `public/js/swift-boot.js` | Accents, 12 full themes, density/radius/font, feature toggles, per-user prefs |
| v1 Premium login/gradient (legacy) | `doctype/swift_theme_settings/*` + `www/login.html` + `css/login.css` + `js/login.js` | Glassmorphism standalone login, preset themes, custom gradient, sounds |
| Desk UI layer | `public/css/swift-*.css` (9 files) + `public/js/swift-*.js` (7 files) | Theme tokens mapped onto Frappe v16 desk |
| Website/Portal UI layer | `public/css/swift-website.css`, `swift-login.css` + `js/swift-website.js` | Portal + login theming |
| Install/seed | `install.py` | Creates 8 User custom fields + Settings doc seed |
| Fixtures | `hooks.py` → `fixtures` | Custom Fields module export |

## Critical finding — settings schema mismatch (v1 vs v2)

`Swift Theme Settings` DocType JSON defines **v1 fields** only:
`color_mode`, `active_preset`, `gradient_start`, `gradient_end`, `enable_sounds`,
`volume_level`, `sound_events`, `sidebar_variant`, `pin_behavior`.

But `install.py::_seed_settings()` and `api/boot.py` read **v2 fields**
(`default_accent`, `default_density`, `default_radius`, `default_font_*`,
`navbar_variant`, `enable_switcher`, `enable_command_palette`, `enable_focus_mode`,
`enable_perf_mode`, `enable_styled_scrollbar`, `enable_toast_theming`,
`enable_print_theming`, `login_layout`, `auto_dark_*`, brand fields).

- Seed values are silently dropped (unknown doc attrs are not persisted).
- `api/boot.py` falls back to its hardcoded defaults → Settings UI has **no effect** on v2 prefs.
- Only overlap: `sidebar_variant`.
- Risk: HIGH — System Manager edits Settings and sees no change.

## Other gaps found

- `apply_theme()` writes `swift_selected_theme` on User — field is never created (not in `install.py`).
- `play_sound()` returns `/assets/swift_theme/sounds/*.mp3` — `sounds/` dir does not exist.
- `swift-fonts.css` + `swift-perf.js` reference `inter-var.woff2` — file absent; Google CDN fallback + `fonts/README.txt` instructions.
- `public/presets/*.json` (enterprise/neon) — not referenced by any code.
- `swift-desk.css` uses v1 attr `data-swift-sidebar` (floating/attached/minimal) + `--accent-color`; v2 pipeline sets `data-swift-sidebar-variant` (Attached/Floating/Icon-only) — selectors don't line up.
- Two byte-identical `login.html` copies (`swift_theme/www/login.html` + `swift_theme/swift_theme/www/login.html`).

## Dependency graph

```
hooks.py
 ├─ app_include_css/js  → Desk (swift-boot.js first, swift-perf.js last)
 ├─ web_include_css/js   → Website/Portal (swift-boot.js + swift-website.js)
 ├─ boot_session / extend_bootinfo → api/boot.py::get_effective_prefs → Settings + User custom fields
 ├─ website_context      → favicon
 ├─ fixtures             → Custom Field export
 └─ after_install/after_migrate → install.py → User fields + Settings seed

api/boot.py
 ├─ get_effective_prefs  (whitelisted; consumed by JS via frappe.boot.swift_theme + REST)
 └─ set_user_pref        (whitelisted; called by swift-boot.js persist())

swift-boot.js (window.SwiftTheme)
 ├─ localStorage keys (swift_accent, swift_theme_full, swift_density, …)
 ├─ applyPrefs ← frappe.boot.swift_theme  (syncs server prefs)
 ├─ setAccent/setFullTheme/… → persist() → set_user_pref
 └─ auto-dark + custom CSS/JS + favicon injection

doctype/swift_theme_settings
 ├─ SwiftThemeSettings.on_update → publish_realtime("swift_theme_updated")
 └─ get_active_theme_config / play_sound / get_premium_themes / apply_theme (v1)
```

## Execution order (desk load)

1. `bench build` compiles `public/` → `/assets/swift_theme/`
2. frappe desk boot → `boot_session` + `extend_bootinfo` → `bootinfo.swift_theme`
3. `app_include_css` injected in order (fonts, base, accents, themes, layout, density, desk, scrollbar, toast, perf)
4. `app_include_js` injected in order (boot → mode-observer → switcher → palette → sidebar → focus → perf)
5. `swift-boot.js` IIFE applies localStorage attrs immediately (anti-FOUC), then `app_ready`/`DOMContentLoaded` → `syncFromBoot` → server prefs
6. Sidebar/palette/decorators run on `app_ready` + `after_ajax` + MutationObserver

See `BOOT_PROCESS.md` for details.

---

# Phase 2 — GoldElite Architecture Design (Blueprint)

GoldElite is the product evolved from Swift Theme: a **Desktop Experience Layer** for
ERPNext v16. Not a CSS theme. Modular, replaceable, upgrade-safe, optional — every
capability is a toggleable unit that can be swapped for a Frappe default at any time.

## 0. Conventions (apply to every system)

| Convention | Rule |
|---|---|
| Global | `window.GoldElite` (alias `GE`); every system exposed as `GE.<system>.*` |
| Frappe access | ONLY via `services/frappe/*` adapters; no other file touches `frappe.*` globals |
| Styling | CSS-first, `@layer goldelite`; tokens `--ge-*`; attributes `data-ge-*`; classes `.ge-*` |
| Config | every capability behind a feature flag (S14); defaults safe |
| Lifecycle | every system: `init(cfg) → mount() → destroy()`; no listeners leak on `page_change` |
| Contracts | Frappe contract checks run at boot; failure disables the feature gracefully |
| Versioning | `GE` public API frozen at 1.0; plugins declare `ge: ">=1.0"` |
| Upgrade | never edit `apps/frappe` or `apps/erpnext`; any need to = design bug |

## 1. Systems (15)

Format per system: Purpose / Responsibilities / Dependencies / Public API /
Internal modules / Swift connection / Frappe connection / Override strategy /
Extensibility / Risks.

### S1 Theme Engine
| Attribute | Design |
|---|---|
| Purpose | Own all visual identity (accent, mode, density, radius, font, glass) while staying compatible with Frappe light/dark |
| Responsibilities | token sets; `data-ge-*`→CSS vars; accent palette; mode bridge (light/dark/auto); persistence via S7 |
| Dependencies | S7 Settings, S14 Flags, S6 Animation, token CSS layer |
| Public API | `GE.theme.get()/set(partial)/reset()`; `GE.theme.on("change", cb)` |
| Internal modules | `systems/theme/{tokens,accent,mode,frappe-bridge,apply}` |
| Swift connection | supersedes `swift-themes.css` + `swift-mode-observer.js`; keeps same `data-swift-*` contract for compat |
| Frappe connection | observes `<html data-theme-mode>` (MutationObserver); reads Frappe CSS vars; never writes Frappe attrs |
| Override strategy | Inject (tokens at `<html>`), Wrap (theme switch dialog) |
| Extensibility | plugin accent packs, custom fonts, per-route token overrides |
| Risk | Frappe v17 token renames → contract test pins top-20 vars |

### S2 Layout Engine
| Attribute | Design |
|---|---|
| Purpose | Own the desktop skeleton (dock, navbar, content region, status bar, overlays) |
| Responsibilities | render shell; region slots; responsive breakpoints; z-index + overlay stack; keep Frappe view area live |
| Dependencies | S1, S7, S6, S3 |
| Public API | `GE.layout.shell.regions()`; `GE.layout.setSidebar(on)`; `GE.layout.openPanel(id)`; `GE.layout.on("region-changed")` |
| Internal modules | `systems/layout/{shell,regions,responsive,zindex,frappe-chrome}` |
| Swift connection | replaces v1/v2 sidebar pin/off logic; owns `.layout-side-section` wrapper |
| Frappe connection | decorates `frappe.app.make_sidebar`/`make_nav_bar` to suppress default chrome (flag `replace-chrome`); re-parents `#body` content into main region; preserves `body[data-route]` |
| Override strategy | Wrap (boot decorators), Inject (GoldElite shell) |
| Extensibility | layout presets (docked/float/glass), plugin regions |
| Risk | hiding Frappe chrome may confuse Frappe JS → flag OFF by default; hide, never remove |

### S3 Component Library
| Attribute | Design |
|---|---|
| Purpose | GoldElite's own UI kit for every GoldElite-owned surface |
| Responsibilities | primitives (button, input, icon, badge, avatar, menu, tooltip, overlay, skeleton), data comps (table, tree, card), feedback (toast, progress), composed (palette, window frame) |
| Dependencies | tokens, utilities, store; no Frappe |
| Public API | `GE.ui.component(name, opts)`; `GE.ui.render(el, vnode)`; `GE.ui.icon(name)` |
| Internal modules | `components/*`, `vdom/` (tiny hyperscript — NOT a framework), `tokens/bindings`, `skins/*` |
| Swift connection | new comps replace Swift's ad-hoc chips/badges; Swift CSS reused as skins |
| Frappe connection | none direct; accepts Frappe DOM nodes for wrappers (S11) |
| Override strategy | Compose (Frappe untouched) |
| Extensibility | plugin-registered components usable in palette/settings/widgets |
| Risk | look drift vs Frappe → bind to shared token values; avoid duplicating Frappe dialog where its own suffices |

### S4 Navigation Engine
| Attribute | Design |
|---|---|
| Purpose | Own how users reach modules/pages (sidebar tree, groups, pins, nav search) |
| Responsibilities | build tree from boot data; grouping/pinning/hiding; active-state sync; keyboard nav |
| Dependencies | S2 (dock), store, S14, router adapter |
| Public API | `GE.nav.items()`; `GE.nav.setTree(t)`; `GE.nav.pin(name)`; `GE.nav.go(route)` |
| Internal modules | `systems/nav/{tree,groups,pins,active,frappe-data}` |
| Swift connection | replaces `swift-sidebar.js` pins; consumes `data-swift-sidebar-variant` contract |
| Frappe connection | reads `frappe.boot.workspace_sidebar_item` + workspaces (documented boot data); triggers hash routing |
| Override strategy | Replace (GoldElite renders own tree); S2 hides Frappe sidebar |
| Extensibility | plugin nav sections; ERPNext workspace json flows in automatically |
| Risk | boot data shape changes → adapter normalizes; fallback to Frappe sidebar on parse failure |

### S5 Workspace Engine
| Attribute | Design |
|---|---|
| Purpose | Own the GoldElite home dashboard + workspace card surface |
| Responsibilities | home widgets (shortcuts, lists, charts, KPIs), workspace pages, widget registry, per-user arrangement |
| Dependencies | S3, store, query service, S1, S7 |
| Public API | `GE.workspace.config()`; `GE.workspace.setLayout(name)`; `GE.widget.register({type,render})`; `GE.widget.addToHome(id)` |
| Internal modules | `systems/workspace/{registry,dashboard,page,arrangement}` |
| Swift connection | replaces gradient-number-card approach with widget registry skins |
| Frappe connection | subclass `frappe.views.Workspace` + `frappe.views.DashboardView` (extend); consume `frappe.views.widget_group` data |
| Override strategy | Extend/Compose (factories re-registered via router contract; widgets composed) |
| Extensibility | plugin widgets (KPI, feed, doc-table) |
| Risk | Workspace internals change → keep subclass shallow (render wrap only), fallback default on flag off |

### S6 Animation Engine
| Attribute | Design |
|---|---|
| Purpose | unified motion language |
| Responsibilities | motion tokens, transition classes, page-change orchestration, reduced-motion compliance, no external lib |
| Dependencies | S1, S3, S2 |
| Public API | `GE.motion.play(el, "slide-in", {duration})`; `GE.motion.enabled(bool)` |
| Internal modules | `systems/anim/{tokens,driver,pagechange,reduced}` |
| Swift connection | supersedes Swift hover/transition CSS; animation classes move to `scss/animations/` |
| Frappe connection | none (pure layer); animates Frappe view transitions on `page_change` |
| Override strategy | Inject/Wrap |
| Extensibility | plugin motion presets |
| Risk | async-load flicker on transitions → gate flag, honor `prefers-reduced-motion`, transform only |

### S7 Settings Engine
| Attribute | Design |
|---|---|
| Purpose | single source of truth for all GoldElite config |
| Responsibilities | schema (fixes v1/v2), whitelisted API, tiers (user/tenant/global), live cross-tab sync, migration runner, validation |
| Dependencies | Frappe whitelisted methods, store, S14 |
| Public API | `GE.settings.get(key)/set(key,val)/reset()`; `GE.settings.on("change")`; `GE.settings.tier(key)` |
| Internal modules | `systems/settings/{schema,migrate,persist,validation}` + backend `settings_engine/` |
| Swift connection | replaces `api/boot.py` prefs + `_seed_settings`; migrates existing v1 data |
| Frappe connection | whitelisted `goldelite.api.settings.*`; boot via `extend_bootinfo` ONLY (drop duplicate `boot_session`) |
| Override strategy | Replace/Extend (own DocType + API) |
| Extensibility | plugin settings sections (declare schema fields) |
| Risk | migration must be transactional; unknown keys ignored; boot payload sends enabled tiers only |

### S8 Shortcut Engine
| Attribute | Design |
|---|---|
| Purpose | registry + help for all keyboard shortcuts (GoldElite + Frappe) |
| Responsibilities | register via Frappe API, conflict detection, feature-gating, help dialog, scoped keys |
| Dependencies | S14, S3 (help dialog), Frappe keyboard API |
| Public API | `GE.shortcuts.register({shortcut,action,scope,when})`; `GE.shortcuts.unregister(id)`; `GE.shortcuts.help()` |
| Internal modules | `systems/shortcuts/{registry,conflicts,help,frappe-bridge}` |
| Swift connection | replaces Swift ad-hoc handler; Alt+B/Alt+P via Frappe API |
| Frappe connection | uses `frappe.ui.keys.add_shortcut` so keys appear in Ctrl+F1 |
| Override strategy | Extend/Wrap |
| Extensibility | plugin shortcuts with flag gating |
| Risk | modifier normalization changes → conflict detector parses canonical form |

### S9 Search Engine
| Attribute | Design |
|---|---|
| Purpose | unified global search (documents + commands + workspace) |
| Responsibilities | command palette (own comp), doc search (Frappe endpoint), fuzzy match, recent/pinned, plugin command providers |
| Dependencies | S3, S8, Frappe search module |
| Public API | `GE.search.palette.show()`; `GE.search.provider(name, fn)`; `GE.search.query(q)` |
| Internal modules | `systems/search/{palette,providers,fuzzy,recent,frappe-search}` |
| Swift connection | replaces `swift-palette.js`; reuses its overlay skin |
| Frappe connection | uses existing `frappe.search` endpoint for docs; extends `extend_awesome_bar_shortcuts` |
| Override strategy | Compose/Extend |
| Extensibility | plugin command providers |
| Risk | search API changes → palette falls back to in-memory nav search |

### S10 Notification Engine
| Attribute | Design |
|---|---|
| Purpose | unify realtime + in-app notifications + sound |
| Responsibilities | unread bell (extend Frappe), GoldElite toast centre (history + actions), sound events, desktop notifications opt-in, per-type mute |
| Dependencies | S3 (toast), store, Frappe realtime + `sounds` hook |
| Public API | `GE.notify.toast({...})`; `GE.notify.sound(event,file)`; `GE.notify.centre.show()`; `GE.notify.on("unread")` |
| Internal modules | `systems/notify/{toast,centre,sounds,realtime,prefs}` |
| Swift connection | replaces `swift-toast.css` + sounds prefs; keeps `.desk-alert` compat skin |
| Frappe connection | listens realtime `notification` channel; bridges `frappe.show_alert`; sounds from `hooks.sounds` |
| Override strategy | Extend/Wrap |
| Extensibility | plugin notification types |
| Risk | realtime payload shape → dedupe by id, never double-alert |

### S11 Window Management
| Attribute | Design |
|---|---|
| Purpose | detach/dock views into desktop-like windows |
| Responsibilities | window frame, attach/detach, dock + cascade, geometry persistence, focus mgmt |
| Dependencies | S3, S2, S6, S14 (`window-management`) |
| Public API | `GE.windows.detach(name)`; `GE.windows.dock(name)`; `GE.windows.get(name)`; `GE.windows.on("open/close/focus")` |
| Internal modules | `systems/windows/{frames,dock,state,frappe-page}` |
| Swift connection | new capability; reuses desk skins for frames |
| Frappe connection | detach = open a SECOND Form/List instance via route and move its `$body` into a frame; primary window unchanged (never move a live page) |
| Override strategy | Wrap/Compose |
| Extensibility | snap layouts, multi-monitor |
| Risk | HIGH — second instance keeps realtime/timers independent; OFF by default; degrade to read-only "mini view" when doc is dirty |

### S12 Developer APIs
| Attribute | Design |
|---|---|
| Purpose | public contract for all modules + plugins |
| Responsibilities | `GE` namespace, registration APIs, event bus, lifecycle hooks, utils, error handling, versioning |
| Dependencies | store, all systems |
| Public API | `GE.registerComponent/Command/Widget/Provider/Plugin`; `GE.on/off/emit`; `GE.hooks.{onBoot,onReady,onPageChange,onUnload}` |
| Internal modules | `core/{namespace,events,registry,lifecycle,utils}` |
| Swift connection | Swift globals (`SwiftTheme`) deprecated behind `GE.*` facade |
| Frappe connection | none (adapters only) |
| Override strategy | Compose/Inject |
| Extensibility | everything |
| Risk | API churn → freeze surface at 1.0, semver |

### S13 Plugin System
| Attribute | Design |
|---|---|
| Purpose | load and manage modules (built-in + third-party) safely |
| Responsibilities | manifest resolution, dependency graph, load order, lazy loading, feature-flag gating, lifecycle, version compat |
| Dependencies | S12, S14, build system (dynamic imports) |
| Public API | `GE.plugins.load(name)`; `GE.plugins.list()`; `GE.plugins.disable(name)`; manifest `{name,version,ge,systems,flags}` |
| Internal modules | `systems/plugins/{manifest,loader,graph,lifecycle}` |
| Swift connection | built-ins = `core-theme/layout/nav/workspace/palette/windows`; legacy Swift features become `core-*` plugins |
| Frappe connection | none client-side; python plugins via `hooks.py` only if server work needed |
| Override strategy | Compose |
| Extensibility | third-party manifests (trusted) |
| Risk | circular deps/version drift → graph resolver + fail-to-no-plugin state |

### S14 Feature Flags
| Attribute | Design |
|---|---|
| Purpose | every capability independently toggleable |
| Responsibilities | flag registry, tiers, persistence, gating of assets+CSS+JS+shortcuts+settings UI, realtime toggle, audit |
| Dependencies | S7, store, build (asset manifest) |
| Public API | `GE.flags.isEnabled(id)`; `GE.flags.enable(id)`; `GE.flags.list()`; `GE.flags.on("change")` |
| Internal modules | `systems/flags/{registry,resolver,gate,persist}` + backend `feature_flags/` |
| Swift connection | every Swift "always-on" behavior becomes a flag |
| Frappe connection | boot includes only enabled flags (via S7 `extend_bootinfo`) |
| Override strategy | Inject/Wrap |
| Extensibility | plugins declare their flags |
| Risk | flag explosion → curated registry, max ~40, each with description |

### S15 Performance Layer
| Attribute | Design |
|---|---|
| Purpose | keep boot fast and UI smooth |
| Responsibilities | code splitting, conditional asset delivery, CSS containment, observer budget, mutation batching, animation throttling, metrics + budgets |
| Dependencies | build system, S14, S6 |
| Public API | `GE.perf.metrics()`; `GE.perf.observe(name, cb)`; `GE.perf.budget(name)` |
| Internal modules | `systems/perf/{split,containment,observers,metrics,lazy}` |
| Swift connection | replaces `swift-perf.css`/`swift-perf.js` ad-hoc rules |
| Frappe connection | never touches internals; uses rAF/IntersectionObserver |
| Override strategy | Inject |
| Extensibility | plugin perf budgets |
| Risk | over-optimization → budgets soft (warn, not fail) |

## 2. Directory structure (production target — DO NOT CREATE YET)

```
apps/swift_theme/
└── swift_theme/                     # python package
    ├── hooks.py                     # thin: assets, boot, website_context, fixtures
    ├── install.py                   # migration runner (v1→v2), fixtures seed
    ├── api/
    │   ├── settings.py              # whitelisted settings endpoints
    │   ├── flags.py                 # feature-flag read/write (audited)
    │   ├── notifications.py         # sound + centre endpoints
    │   └── boot.py                  # extend_bootinfo assembly (single path)
    ├── settings_engine/
    │   ├── schema.py  migrate.py  validation.py  store.py
    ├── feature_flags/
    │   ├── registry.py  resolver.py  audit.py
    ├── plugins/                     # python plugin entry points (server-side extras)
    ├── fixtures/                    # default settings/custom fields
    ├── doctype/
    │   └── goldelite_settings/      # v2 schema (v1 migrated into it)
    ├── public/                      # ===== FRONTEND =====
    │   ├── js/
    │   │   ├── goldelite/
    │   │   │   ├── core/            # namespace, boot, store, events, registry, lifecycle
    │   │   │   ├── systems/         # S1..S15 (one folder each)
    │   │   │   ├── services/        # frappe adapters, query, realtime, search
    │   │   │   ├── stores/          # per-system reactive stores
    │   │   │   ├── hooks/           # lifecycle hook impls
    │   │   │   ├── animations/      # driver + motion tokens
    │   │   │   ├── layouts/         # shell skeleton templates + presets
    │   │   │   ├── utilities/       # dom, colors, bytes, fn
    │   │   │   ├── components/      # S3 UI kit
    │   │   │   ├── plugins/         # built-in plugins (core-*)
    │   │   │   ├── types/           # jsdoc typedefs / .d.ts
    │   │   │   └── tests/           # unit + integration
    │   │   ├── ge.bundle.js         # core entry (small, non-lazy)
    │   │   └── ge-<system>.bundle.js# code-split chunks (lazy by flag)
    │   ├── scss/
    │   │   ├── tokens/              # design tokens (scss + json)
    │   │   ├── base/                # reset, typography
    │   │   ├── systems/             # per-system styles
    │   │   ├── components/
    │   │   ├── animations/
    │   │   └── legacy/              # swift-*.css skins (compat, frozen)
    │   ├── css/                     # committed dist (bench build)
    │   ├── icons/                   # svg sprite + icon set
    │   ├── fonts/
    │   ├── sounds/
    │   └── assets/
    └── www/                         # docs (existing *.md — append only)
```

Rules: core `ge.bundle.js` stays small (boot + S7 + S12 + S14 only). Every S-system is a
lazy chunk + `scss/systems/<name>.css` chunk, injected by `GE.flags` asset gate.

## 3. Component inventory

Owned by GoldElite (rendered from scratch):
Sidebar tree, Navbar (GoldElite), Status bar, Dock, Window frames, Title bar, Command
Palette, Quick actions tray, Splash, Settings UI, Home dashboard shell, Empty states,
Toast centre, Mode badge, Brand/logo, Login layout.

Extended from Frappe (subclass / re-skin):
Forms (skin + section chrome), Lists (row render), Grids (child tables), Reports +
DataTable (skin), Charts (options/skin), Workspace widgets (reuse), Calendar / Kanban /
Gantt (skin), Dialogs (skin; GoldElite dialog only for owned surfaces), Awesomebar search
(extend + own palette), Notifications bell (extend + own centre), Timeline (skin),
Progress (skin), Indicators / Breadcrumbs / Tree / Tabs (skin), Web Forms (CSS), Login
form logic (Frappe auth + GoldElite layout).

Left unchanged:
Router + view lifecycle + container, permission/model layer, form save / workflow /
client scripts, grid data model, datatable logic, chart SVG rendering, realtime transport,
file uploader, POS, print / PDF / email, Web Form logic, Kanban logic.

## 4. Implementation strategy per system

| System | Strategy | Frappe core touched? |
|---|---|---|
| Theme | Inject + Wrap | no |
| Layout | Wrap + Inject | no (decorate boot) |
| Components | Compose | no |
| Navigation | Replace + Extend | no (boot data read) |
| Workspace | Extend + Compose | no (subclass factories) |
| Animation | Inject + Wrap | no |
| Settings | Replace + Extend | no (own DocType/API) |
| Shortcuts | Extend + Wrap | no |
| Search | Compose + Extend | no (hooks) |
| Notifications | Extend + Wrap | no |
| Windows | Wrap + Compose | no |
| Dev APIs | Inject | no |
| Plugins | Compose | no |
| Flags | Inject + Wrap | no |
| Perf | Inject | no |

None touch Frappe/ERPNext core. The only cross-app edits ever permitted are the
documented hook surfaces (`app_include_*`, `web_include_*`, `extend_bootinfo`, `sounds`,
`website_context`, `website_route_rules`, Website Theme SCSS import).

## 5. Feature flags (starter set)

| Flag | Tier | Default | System |
|---|---|---|---|
| replace-chrome | user | off | S2 (highest risk) |
| floating-sidebar | user | off | S2/S4 |
| glass-mode | user | off | S1 |
| animations | user | on | S6 |
| workspace-home | user | on | S5 |
| command-palette | user | on | S9 |
| global-search | user | on | S9 |
| keyboard-shortcuts | user | on | S8 |
| custom-fonts | user | on | S1 |
| custom-login | user | on | S1 |
| toast-centre | user | on | S10 |
| sound-effects | user | on | S10 |
| desktop-notifications | user | off | S10 |
| compact-density | user | off | S1 |
| developer-mode | user | off | S12/S15 |
| window-management | user | off | S11 |
| detachable-views | user | off | S11 |
| plugin-system | tenant | on | S13 |
| perf-layer | tenant | on | S15 |
| lazy-loading | tenant | on | S15 |
| content-containment | tenant | on | S15 |

Full registry maintained in S14; max ~40 flags. See DECISIONS for the cut-down set.

## 6. Upgrade strategy

High-risk override points (must stay behind flags + contract checks):
view-factory re-registration (S5), boot chrome decorators (S2), login layout (S1),
POS styling, window detach (S11), `frappe.views.Container` interactions.

Low-risk extension points (safe to use freely):
CSS tokens, `app_include_*`, `web_include_*`, `extend_bootinfo`, `sounds`,
`extend_awesome_bar_shortcuts`, `frappe.ui.keys.add_shortcut`, Website Theme SCSS import,
`frappe.ready`, `frappe.boot.*` data reads.

Migration & compatibility:
- one adapter file per Frappe contract in `services/frappe/` (single point to patch).
- boot-time contract checks: assert presence + shape; on failure disable feature + log.
- `frappe-compat.json`: tested frappe + erpnext versions; CI runs upgrade matrix.
- hide (never remove) Frappe DOM; layered CSS; flags default to Frappe behavior.
- v1 settings shim reads legacy keys for one release, then removed.

## 7. Performance (summary — detail in PERFORMANCE_GUIDE.md)

Core bundle = boot + S7 + S12 + S14 only. All other systems lazy (dynamic import) +
CSS chunks injected by enabled flags. One MutationObserver per concern, torn down on
`page_change`. `content-visibility` containment on rows/cards. Metrics surfaced by S15.

See also RULES.md (engineering), PHASES.md / ROADMAP.md (sequencing),
PERFORMANCE_GUIDE.md / SECURITY_GUIDE.md / TESTING_GUIDE.md,
DECISIONS.md (architect review + decision register).
