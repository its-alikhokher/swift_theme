# Swift Theme — API Reference

Phase 1. Swift's server API + Frappe endpoints it consumes. No implementation.

## Swift whitelisted endpoints (`swift_theme/api/*.py`)

| Endpoint | Purpose | Files |
|----------|---------|-------|
| `swift_theme.api.boot.get_swift_theme_prefs` | effective theme prefs for boot | `api/boot.py` |
| `swift_theme.api.boot.set_swift_theme_prefs` | save user prefs | `api/boot.py` |
| `swift_theme.api.boot.reset_swift_theme` | reset to defaults | `api/boot.py` |
| settings CRUD | settings doctype API | `doctype/swift_theme_settings/*` |

## Frappe endpoints Swift relies on

| Endpoint | Used for |
|----------|----------|
| `POST /api/method/login` | login form |
| `POST /api/method/frappe.core.doctype.user.user.reset_password` | forgot password |
| `frappe.sessions.get` boot | desk boot (Swift prefs via `extend_bootinfo`) |
| `/api/method/frappe.client.get_list` | lists (Swift doesn't use directly) |

## Context injection

| Method | Where |
|--------|-------|
| `hooks.boot_session` (`swift_theme.boot.boot_session`) | desk + website boot context |
| `hooks.extend_bootinfo` | appends Swift prefs to bootinfo |
| `hooks.website_context` | login/website page context (favicon/logo) |
| `hooks.app_include_js/css`, `web_include_js/css` | asset injection |

## Known issue (v1/v2)

Settings Doctype JSON defines v1 fields (`color_mode`, `active_preset`, `gradient_*`,
`pin_behavior`, sounds) while `_seed_settings` + `api/boot.py` read v2 keys (`default_accent`,
`default_density`, `default_radius`, `default_font_*`, `navbar_variant`, `enable_switcher`,
`enable_command_palette`, `enable_focus_mode`, `enable_perf_mode`, `enable_styled_scrollbar`,
`enable_toast_theming`, `enable_print_theming`, `login_layout`, brand fields).
→ Settings edits appear to do nothing (no matching boot read) — must reconcile in
DECISIONS.md. Both `boot_session` and `extend_bootinfo` call `get_effective_prefs` (redundant).
