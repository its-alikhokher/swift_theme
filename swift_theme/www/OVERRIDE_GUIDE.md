# Swift Theme — Override Guide

Every extension point in the app, from safest to riskiest.

## 1. CSS (primary extension surface)

Add/modify by layering on `data-swift-*` attribute selectors:

| Attribute on `<html>` | Values | CSS file | Purpose |
|----------------------|--------|----------|---------|
| `data-swift-accent` | indigo, violet, blue, sky, teal, emerald, amber, rose, pink, slate | swift-accents.css | accent token set |
| `data-swift-theme` | obsidian, graphite, midnight, monochrome, porcelain, aurora, sandstone, carbon, emerald, sapphire, rose-gold, ivory | swift-themes.css | full surface + accent override |
| `data-swift-radius` | Sharp / Rounded / Pill | swift-base.css | radius scale |
| `data-swift-font-scale` | S / M / L / XL | swift-base.css | base font-size |
| `data-swift-density` | Compact / Comfortable / Cozy | swift-base.css, swift-density.css | spacing + row height |
| `data-swift-font` | Inter / Poppins / Manrope / Roboto / System | swift-fonts.css | font stack |
| `data-swift-navbar` | Solid / Glass / Transparent | swift-layout.css | navbar variant |
| `data-swift-sidebar-variant` | Attached / Floating / Icon-only | swift-layout.css | sidebar variant |
| `data-swift-perf` | on/off | swift-perf.css | perf layer |
| `data-swift-anim` | on/off | swift-perf.css | animation kill-switch |
| `data-swift-scrollbar` | on/off | swift-scrollbar.css | scrollbar styling |
| `data-swift-toast` | on/off | swift-toast.css | toast theming |
| `data-swift-focus` | on | (attached via layout-main rules) | focus mode |
| `data-swift-reading` | on | (widen content) | reading mode |
| `data-swift-sidebar` | off | swift-sidebar.js only | sidebar hidden (v1 attr, don't reuse) |
| `data-swift-login` | Split/Centered/Minimal | swift-login.css | login layout (`<body>`) |

Tokens consumed: `--swift-accent`, `--swift-accent-hover`, `--swift-accent-fg`,
`--swift-accent-soft`, `--swift-radius`, `--swift-font-size`, `--swift-row-h`,
`--swift-space-*`, `--swift-ambient`, `--swift-login-bg`, `--swift-print-font`,
`--swift-print-accent`. Frappe bridge vars: `--primary`, `--btn-primary`, `--focus-default`.

New theme = add a block in swift-themes.css + entry in `api/boot.py::FULL_THEMES`
(+ optional User custom-field option). See README.md for the same recipe.

## 2. JS API hooks

| Hook point | Where | Use |
|-----------|-------|-----|
| `window.SwiftTheme.*` | swift-boot.js | programmatic accent/theme/density setters |
| `window.SwiftSidebar.*` | swift-sidebar.js | pin/unpin/toggle-off sidebar |
| `swift:mode-changed` event | swift-mode-observer.js | react to Frappe L/D/A switch |
| `swift:cmdk:open` event | swift-palette.js | open command palette |
| `frappe.boot.swift_theme` | api/boot.py | server-side prefs dict |

## 3. Backend extension points

- Add settings fields → must add to DocType JSON + `install.py::_seed_settings()` + `api/boot.py::get_effective_prefs()` (all three or it silently breaks).
- New whitelisted method → mirror `api/boot.py` pattern (`@frappe.whitelist()`).
- User preference fields → append to `install.py::USER_FIELDS`, `_ensure_user_fields`, `api/boot.py::_user_prefs` + `ALLOWED` in `set_user_pref`.

## 4. Frappe core overrides available (currently unused)

- `override_whitelisted_methods` (e.g. wrap core `login` to theme flow)
- `on_login`, `session_creation`, `website_route_rules`, `print_style`
- DocEvents via `doc_events` (e.g. `User` save → re-derive prefs)
- Realtime subscriber for `swift_theme_updated` (event is published but unhandled)

## 5. Risk notes

- ⚠ Settings schema mismatch (v1 JSON vs v2 seed/boot reads) — any work on Settings must resolve this first.
- ⚠ Do not touch Frappe's own `[data-theme]` Light/Dark/Auto attribute (boot.js contract: "we NEVER touch that"). Full themes do call `frappe.ui.set_theme()` intentionally.
- ⚠ `swift-desk.css` uses legacy selectors (`--accent-color`, `data-swift-sidebar`) that may not bind to v2 attrs.
