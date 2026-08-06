# Swift Theme — Hooks Reference

Source: `swift_theme/hooks.py`

| Hook | Value | Called by (Frappe core) | Purpose |
|------|-------|------------------------|---------|
| `app_include_css` | 9 `/assets/swift_theme/css/*.css` | desk page | Desk theming layer |
| `app_include_js` | 7 `/assets/swift_theme/js/*.js` | desk page | Desk JS pipeline |
| `web_include_css` | 7 css files | website pages | Portal/login theming |
| `web_include_js` | `swift-boot.js`, `swift-website.js` | website pages | Portal bootstrap |
| `extend_bootinfo` | `swift_theme.api.boot.extend_bootinfo` | `frappe/sessions.py:167` | Adds `bootinfo.swift_theme` |
| `boot_session` | `swift_theme.api.boot.boot_session` | `frappe/boot.py:93` | Same payload (redundant w/ above) |
| `website_context` | `{"favicon": "/assets/swift_theme/icons/favicon.svg"}` | website render | Site favicon |
| `fixtures` | Custom Field, module "Swift Theme" | `bench export-fixtures` | Sync User custom fields |
| `after_install` | `swift_theme.install.after_install` | install-app | User fields + settings seed |
| `after_migrate` | `swift_theme.install.after_migrate` | migrate | Idempotent re-seed |

## Whitelisted methods (REST, called from JS)

| Method | Source | Called by |
|--------|--------|-----------|
| `swift_theme.api.boot.get_effective_prefs` | api/boot.py:43 | boot hooks, swift-website.js, Settings "Apply Now" |
| `swift_theme.api.boot.set_user_pref` | api/boot.py:108 | swift-boot.js `persist()` |
| `...swift_theme_settings.get_active_theme_config` | settings .py:181 | login.js (v1) |
| `...swift_theme_settings.play_sound` | settings .py:216 | login.js (v1) |
| `...swift_theme_settings.get_premium_themes` | settings .py:255 | external (none in repo) |
| `...swift_theme_settings.apply_theme` | settings .py:269 | external (none in repo) |

## Hooks NOT used (extension opportunities)

- No `override_whitelisted_methods`, `app_include_js` override, `doc_events`,
  `on_login`, `print_style`, `website_route_rules`, `scheduler_events`.

## Events (JS custom events)

| Event | Dispatcher | Consumers |
|-------|-----------|-----------|
| `swift:mode-changed` | swift-mode-observer.js | none in repo (extensions) |
| `swift:cmdk:open` | swift-palette.js, swift-switcher.js | swift-palette.js |
| `swift_theme_updated` (realtime) | settings .py on_update | none in repo |
| `app_ready`, `DOMContentLoaded` | frappe/browser | swift-boot.js, swift-sidebar.js, swift-website.js, swift-perf.js |

## Keyboard shortcuts (client)

| Key | Action | Source |
|-----|--------|--------|
| F | toggle focus mode | swift-focus.js |
| R | toggle reading mode | swift-focus.js |
| Alt+B | toggle sidebar off | swift-sidebar.js |
| Ctrl+Shift+T | open command palette | swift-palette.js |
| Ctrl+Enter | submit v1 login form | login.js |
