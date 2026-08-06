# Swift Theme — Routing Guide

## Layer 1 — Frappe desk SPA (`/app/...`)

- All desk routes handled by core `frappe` (forms/lists/reports/workspace).
- Swift Theme adds **no** client-side routes. It layers CSS + `data-swift-*` attrs over core views.
- `config/desktop.py` registers module "Swift Theme" → visible as a workspace module card (route `Swift Theme`).

## Layer 2 — Whitelisted API methods (REST)

| Method | Route | Auth |
|--------|-------|------|
| `get_effective_prefs` | `/api/method/swift_theme.api.boot.get_effective_prefs` | whitelisted (works for Guest) |
| `set_user_pref` | `/api/method/swift_theme.api.boot.set_user_pref` | whitelisted; rejects Guest, allowlist of 8 fields |
| `get_active_theme_config` | `/api/method/swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings.get_active_theme_config` | whitelisted |
| `play_sound` | `.../swift_theme_settings.play_sound` | whitelisted |
| `get_premium_themes` | `.../swift_theme_settings.get_premium_themes` | whitelisted |
| `apply_theme` | `.../swift_theme_settings.apply_theme` | whitelisted (writes User row) |

## Layer 3 — Website pages (`www/`)

- `swift_theme/www/login.html` → static route `/login.html` (standalone v1 page; **not** the `/login` route — see LOGIN_REFERENCE.md).
- `.md` docs in `www/` are technically servable as markdown pages (frappe renders `*.md` in www/). Keep them if website routing exposes them; no explicit `website_route_rules` restrict them.

## Layer 4 — Module workspace

- `config/desktop.py::get_data()` → module card `Swift Theme` (icon `octicon-paintbrush`, color `#7c7cff`) linking to the settings Single.

## Layer 5 — Settings form route

- `Form/Swift Theme Settings/Swift Theme Settings` (reachable via command palette command "Open Swift Theme Settings").

## Routing extension points (core frappe, available)

- `website_route_rules`, `app_include_js`, `override_whitelisted_methods`, custom `www/*.py` page controllers — none currently used by this app.
