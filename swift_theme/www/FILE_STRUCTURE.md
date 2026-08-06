# Swift Theme — File Structure

## Repository tree (responsibilities)

```
swift_theme/                        (app root)
├── README.md                       App readme (v2 feature list, install)
├── pyproject.toml / setup.py       Packaging (flit + setuptools)
├── requirements.txt                frappe~=16.0.0
├── MANIFEST.in                     Package asset includes
├── license.txt / .gitignore
└── swift_theme/
    ├── __init__.py                 __version__ = "2.0.0"
    ├── hooks.py                    ALL frappe hook registration (assets, boot, fixtures, install)
    ├── install.py                  after_install/after_migrate → 8 User custom fields + Settings seed
    ├── modules.txt                 module "Swift Theme"
    ├── patches.txt                 empty
    ├── api/
    │   ├── __init__.py             empty
    │   └── boot.py                 v2 preference engine (get_effective_prefs, set_user_pref, catalogs)
    ├── config/
    │   ├── __init__.py             empty
    │   └── desktop.py              Workspace/module card definition
    ├── docs/
    │   └── USER_MANUAL.md          End-user manual (v1/v2 mixed feature set)
    ├── public/                     static assets (served at /assets/swift_theme/)
    │   ├── css/                    see CSS table below
    │   ├── js/                     see JS table below
    │   ├── fonts/README.txt        inter-var.woff2 download instructions (file absent)
    │   ├── icons/favicon.svg       gradient lightning bolt (hooks website_context)
    │   └── presets/*.json          enterprise/neon setting presets (unwired — no loader)
    ├── swift_theme/
    │   └── doctype/
    │       ├── swift_theme_settings/      Single DocType (v1 fields) + 4 whitelisted methods
    │       └── swift_theme_sound_event/   Child table DocType (event_key/label/sound_file/category)
    ├── templates/__init__.py       empty
    └── www/
        ├── login.html              Standalone glassmorphism login (v1; duplicate below)
        ├── *.md                    THIS doc set (frappe serves .md/.html in www/ as web pages)
        └── (nested) swift_theme/www/login.html   byte-identical duplicate
```

## CSS assets (`public/css/`)

| File | Role | Loaded via |
|------|------|-----------|
| swift-fonts.css | @font-face (Inter/Poppins/Manrope), font-family map | desk + web |
| swift-base.css | Radius/density/font-scale design tokens + row spacing | desk + web |
| swift-accents.css | 10 accent palettes, bridge to `--primary`/`--btn-primary` | desk + web |
| swift-themes.css | 12 full themes, ambient gradients, premium desk chrome | desk + web |
| swift-layout.css | Navbar (Solid/Glass/Transparent) + sidebar variants | desk |
| swift-density.css | Component density fine-tuning (rows, tables, buttons) | desk |
| swift-desk.css | v1 premium views (list/report/kanban/dashboard) + legacy sidebar | desk |
| swift-scrollbar.css | Styled scrollbars (opt-in `data-swift-scrollbar=on`) | desk + web |
| swift-toast.css | Toast/alert theming (opt-in) | desk |
| swift-perf.css | content-visibility, animation kill-switch, reduced-motion | desk |
| swift-website.css | Portal navbar/buttons/cards/links | web |
| swift-login.css | Login layouts (Split/Centered/Minimal), brand, splash | web |
| swift-print.css | Print formats — NOT in hooks; loaded via Custom HTML block in Print Settings | manual |
| login.css | v1 standalone glassmorphism login page | www/login.html only |

Load order (desk): fonts → base → accents → themes → layout → density → desk → scrollbar → toast → perf
Load order (web): fonts → base → accents → themes → website → login → scrollbar

## JS assets (`public/js/`)

| File | Role |
|------|------|
| swift-boot.js | Anti-FOUC attr application, `window.SwiftTheme` API, localStorage, boot sync, auto-dark, CSS/JS/favicon injection |
| swift-mode-observer.js | MutationObserver on `[data-theme]`; fires `swift:mode-changed` |
| swift-switcher.js | Navbar chip + palette popover (themes/accents/density/shape/size/toggles) |
| swift-palette.js | Command palette (Ctrl+Shift+T), `swift:cmdk:open` event |
| swift-sidebar.js | `window.SwiftSidebar` — hide/off mode, pin/unpin items, Alt+B |
| swift-focus.js | F/R keyboard shortcuts (focus/reading mode) |
| swift-perf.js | Idle-time font preload, lazy images, paint hints |
| swift-website.js | Portal accent apply, login brand/tagline/signup injection, splash hide |
| login.js | v1 standalone login form → `/api/method/login`, CSRF + remember user |

Load order (desk): boot → mode-observer → switcher → palette → sidebar → focus → perf
Load order (web): boot → website

## DocType files

| File | Purpose |
|------|---------|
| `swift_theme_settings.json` | Single DocType, System Manager only. v1 fields (see ARCHITECTURE.md mismatch) |
| `swift_theme_settings.py` | validate() gradient check; on_update → realtime `swift_theme_updated`; whitelisted get_active_theme_config/play_sound/get_premium_themes/apply_theme |
| `swift_theme_settings.js` | Client script: Apply Now preview + field visibility toggles |
| `swift_theme_sound_event.json` | Child table (istable), autoname field:event_key |
| `swift_theme_sound_event.py` | Empty Document class |

## Docs (`www/`)

`AI_CONTEXT, API_REFERENCE, ARCHITECTURE, BOOT_PROCESS, BUILD_SYSTEM, CHANGELOG,
COMPONENT_LIBRARY, DECISIONS, DEPENDENCY_GRAPH, DESIGN_SYSTEM, EVENTS_REFERENCE,
FILE_STRUCTURE, FORM_REFERENCE, HOOKS_REFERENCE, LIST_REFERENCE, LOGIN_REFERENCE,
MEMORY, OVERRIDE_GUIDE, PAGES_REFERENCE, PERFORMANCE_GUIDE, PHASES, PORTAL_REFERENCE,
PRD, README, REPORT_REFERENCE, REVERSE_ENGINEERING, ROADMAP, ROUTING_GUIDE, RULES,
SECURITY_GUIDE, SHORTCUTS_REFERENCE, STYLING_GUIDE, TESTING_GUIDE, UI_MAP,
WEBSITE_REFERENCE`

Populated in Phase 0: ARCHITECTURE, FILE_STRUCTURE, BOOT_PROCESS, HOOKS_REFERENCE,
LOGIN_REFERENCE, ROUTING_GUIDE, OVERRIDE_GUIDE, MEMORY, CHANGELOG.
Remainder are empty placeholders (see MEMORY.md next steps).

## Junk / artifacts

- `*.pyc` + `__pycache__/` committed (remove-worthy).
- `*.py:Zone.Identifier` files — Windows download metadata, committed by accident.
