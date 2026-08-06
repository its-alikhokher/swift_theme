# Swift Theme — Boot Process

## 1. Installation / migration

`bench migrate` / `bench install-app swift_theme`
→ `hooks.py:after_install` / `after_migrate` → `install.py`
→ `_ensure_user_fields()`: inserts 8 Custom Fields on `User` (module "Swift Theme")
   - `swift_follow_frappe` (Check), `swift_mode`, `swift_accent`, `swift_theme`,
     `swift_density`, `swift_radius`, `swift_font_scale`, `swift_font_family`
→ `_seed_settings()`: tries to insert `Swift Theme Settings` with v2 fields
   (⚠ fields don't exist on the DocType — seed silently dropped, see ARCHITECTURE.md)

## 2. Asset build

`bench build --app swift_theme`
→ `public/**` compiled/served at `/assets/swift_theme/{css,js,icons,fonts}/`
→ inclusion order fixed by `hooks.py` lists (see FILE_STRUCTURE.md)

## 3. Server boot (Desk)

`frappe/boot.py:93` → `hooks.boot_session` → `api/boot.py::boot_session(bootinfo)`
`frappe/sessions.py:167` → `hooks.extend_bootinfo` → `api/boot.py::extend_bootinfo(bootinfo)`

Both call `get_effective_prefs()` (whitelisted) and set `bootinfo.swift_theme`.
Precedence: User custom fields → Settings default → hardcoded default.
⚠ Because Settings fields are missing, effectively User field → default.

## 4. Client boot (Desk) — no-FOUC chain

1. `swift-boot.js` IIFE (first JS, in `<head>` via app_include_js)
   - reads `localStorage` keys `swift_accent, swift_theme_full, swift_density,
     swift_radius, swift_font_family, swift_font_scale, swift_navbar,
     swift_sidebar_variant, swift_perf, swift_anim, swift_scrollbar,
     swift_toast, swift_focus, swift_reading, swift_hex`
   - sets `data-swift-*` attrs on `<html>` immediately
   - exposes `window.SwiftTheme` (`applyPrefs, setAccent, setFullTheme, setDensity,
     setRadius, setFontScale, setFontFamily, toggleFocus, toggleReading`)
2. CSS token layers react to attrs (fonts → accents → themes → layout → …)
3. `app_ready` / `DOMContentLoaded` → `syncFromBoot()`:
   - `applyPrefs(frappe.boot.swift_theme)`
   - auto-dark window (if `auto_dark` + user not forcing a mode) → `frappe.ui.set_theme()`
   - inject `custom_css` / `custom_js` (once, ids `swift-custom-css/js`)
   - inject `brand_favicon`
4. `swift-switcher.js` → `frappe.after_ajax` → inject navbar chip (if `enable_switcher`)
5. `swift-sidebar.js` → `app_ready` + `after_ajax` + MutationObserver → pin decorate
6. `swift-mode-observer.js` → watches `[data-theme]` / `[data-theme-mode]` → fires `swift:mode-changed`

Preference writes: any SwiftTheme setter → `persist()` → `POST swift_theme.api.boot.set_user_pref`
(only if session user ≠ Guest; localStorage is source of truth across reloads).

## 5. Website / Portal boot

1. `web_include_css` (fonts, base, accents, themes, website, login, scrollbar)
2. `web_include_js` (boot, website)
3. `swift-website.js` on `DOMContentLoaded`:
   - applies `swift_accent`/`swift_theme_full` from localStorage to `<html>`
   - on login pages → `GET /api/method/swift_theme.api.boot.get_effective_prefs`
     → sets `data-swift-login` layout, login bg, brand, tagline, signup toggle
   - hides `.swift-splash` after 300ms

## 6. v1 standalone login boot (separate path)

`GET /login` (see LOGIN_REFERENCE.md — core template, not this file)
`www/login.html` + `css/login.css` + `js/login.js` (if ever served):
- `loadThemeConfig()` → `GET get_active_theme_config` (v1) → applies `--primary/--secondary/--bg1/--bg2`
- form submit → `POST /api/method/login` (with CSRF header) → redirect

## Realtime

`SwiftThemeSettings.on_update` → `publish_realtime("swift_theme_updated")` — no subscriber in repo.
