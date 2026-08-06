# Swift Theme — Build System

Phase 1. Frappe v16 asset pipeline (`frappe/build.py`, `public/js/frappe/assets.js`).

## Pipeline

| Stage | Detail |
|-------|--------|
| SCSS/JS entry | `*.bundle.scss` / `*.bundle.js` in each app `public/` |
| Config | `frappe/build.py::bundle()` (line 222) reads per-app `assets.json`? — reads apps' `public/` bundle files, builds with esbuild? (v16 uses esbuild via `frappe/build`) |
| Output | `sites/assets/<app>/dist/*.{css,js}` |
| Serving | `/assets/<app>/...` via `frappe.utils.get_assets_json`? / `frappe.assets.bundled_asset()` |
| Rebuild | `bench build --app swift_theme` (or full `bench build`) |

## Frappe bundles (hooks `app_include_js`)

`libs.bundle.js`, `billing.bundle.js`, `desk.bundle.js`, `list.bundle.js`, `form.bundle.js`,
`controls.bundle.js`, `report.bundle.js`, `telemetry.bundle.js`
+ `app_include_css`: `desk.bundle.css`, `report.bundle.css`
+ `web_include_js`: `website_script.js`, `web_include_css`: website bundles.

## ERPNext bundles

`erpnext.bundle.js` (big: POS, call popup, item selector, telephony, financial statements,
trend filters — see UI_MAP), `erpnext.bundle.css`, `erpnext-web.bundle.css`,
`point-of-sale.bundle.js`+`point-of-sale.scss`, `website_theme.js` (injects
`@import "erpnext/public/scss/website"` into Website Theme SCSS).

## Swift bundles

`swift-theme.bundle.js` / `swift-theme.bundle.scss`? — Swift currently ships pre-built
`public/css/*.css` + `public/js/*.js` (dist committed). Hooks:
`app_include_css`/`app_include_js` (desk), `web_include_css`/`web_include_js` (website/login).

## Override points for Swift

| Need | Mechanism |
|------|-----------|
| Add desk CSS/JS | `app_include_css/js` hooks (Swift already) |
| Add website CSS/JS | `web_include_css/js` |
| Extend Website Theme SCSS | Website Theme custom_scss + `@import` pattern (ERPNext `website_theme.js` precedent) |
| Login-only | `swift-login.css` via `web_include_css` + `body.for-login` scope |

## Risks / notes

- `bench build` required after Swift scss changes; pre-built dist files must be committed for deploy parity.
- Frappe `assets.json`? bundle map: adding a new `*.bundle.*` requires rebuild + `assets.json` regeneration; prefer existing Swift flat files unless a bundle is needed.
- Never modify frappe/erpnext `public/` — changes lost on bench update and pollute repo diff.
