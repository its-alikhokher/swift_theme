# Swift Theme — Login Reference

## Two login implementations coexist

### A. Frappe core login page (ACTIVE — this is what /login serves)

- Route: `GET /login`, `/?cmd=login`; core page controller `frappe/www/login.py` + template `frappe/templates/pages/login.html`.
- Frappe resolves the first app (core) with a `www/login.*` file → **the standalone `www/login.html` below is not served at `/login`** unless app ordering changes.
- Theming: app adds `web_include_css` (`swift-login.css`, `swift-themes.css`, `swift-accents.css`, …) + `web_include_js` (`swift-boot.js`, `swift-website.js`).
- `swift-website.js` login bootstrap (targets `body.for-login, body[data-path='login'], .for-signup, .for-forgot`):
  - `GET /api/method/swift_theme.api.boot.get_effective_prefs` → sets `body[data-swift-login]` layout (Split/Centered/Minimal)
  - login bg image, brand logo/name, tagline, hide signup links (`login_show_signup`)
- Layouts styled in `swift-login.css`:
  - Split: full-left gradient hero via `body::before`, card right, navbar hidden
  - Centered: radial accent gradients, 420px card
  - Minimal: flat, transparent card
- Post-login redirect is handled by Frappe core (no JS override).

### B. Standalone glassmorphism login (v1 — likely dead route)

- Files: `swift_theme/www/login.html` (+ byte-identical copy at `swift_theme/swift_theme/www/login.html`).
- Assets: `css/login.css` (blobs/glass card), `js/login.js`.
- `login.js` behavior:
  - `loadThemeConfig()` → `get_active_theme_config` (v1 settings) → `--primary/--secondary/--bg1/--bg2`
  - submit → `POST /api/method/login` with `usr`/`pwd`, **X-Frappe-CSRF-Token** from `csrf_token` cookie, `credentials: "include"` → redirect to `data.home_page` or `/app`
  - remember username in localStorage; `play_sound('submit')` → `play_sound` API
  - Ctrl+Enter quick submit
- History: git commit `4bfc52a` "Fix login authentication flow" reworked this file (CSRF handling).

## Backend

| Concern | Location |
|---------|----------|
| Login endpoint | Frappe core `/api/method/login` |
| Prefs for login page | `api/boot.py::get_effective_prefs` (whitelisted, guest-safe) |
| v1 theme config | `swift_theme_settings.py::get_active_theme_config` |
| Sounds | `swift_theme_settings.py::play_sound` (⚠ sounds/ assets missing) |
| Favicon | `hooks.py website_context` → `icons/favicon.svg` |

## CSRF notes (v16)

- Login POST from a browser already holding a session cookie requires `X-Frappe-CSRF-Token` header (`login.js`).
- `credentials: "include"` preserves `sid`/`csrf_token` cookies after login.
