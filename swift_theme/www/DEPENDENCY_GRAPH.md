# Swift Theme — Dependency Graph

Phase 1. Cross-document index of Swift ↔ Frappe ↔ ERPNext relationships.

## Swift → Frappe (core) dependencies

| Swift surface | Frappe dependency |
|---------------|-------------------|
| Desk theming | `data-theme` / `data-theme-mode` (desk.html), `frappe.ui.theme_switcher`, `desk.bundle.css` tokens |
| Sidebar pins/toggle | `frappe.ui.Sidebar` DOM (`#body .layout-side-section`), `workspace_sidebar` boot data |
| Navbar chip | `frappe.ui.toolbar.Toolbar` DOM (`.navbar-nav`) |
| Command palette | `frappe.ui.keys.add_shortcut` + custom overlay |
| Login | `www/login.html` `section.for-login` + `templates/web.html` layout |
| Website | `web.html` `page-{name}` containers, Website Settings navbar/footer |
| Mode observer | MutationObserver on `<html data-theme-mode>` + `prefers-color-scheme` |

## Swift → ERPNext

| Swift surface | ERPNext dependency |
|---------------|--------------------|
| Portal theming | `erpnext/templates/pages/order.html`, `erpnext-web.bundle.css` |
| Website SCSS import | `public/js/website_theme.js` injects `@import "erpnext/public/scss/website"` |
| Sounds | `erpnext/public/sounds/*.mp3` via `sounds` hook |
| Workspaces | `erpnext/**/workspace/*.json` sidebar data |
| POS styling | `point-of-sale.scss` (risk area) |

## Frappe ↔ ERPNext (Swift must not break)

| Frappe | ERPNext |
|--------|---------|
| `app_include_js` chain | `erpnext.bundle.js` appended after frappe bundles (order matters) |
| `extend_bootinfo` / `boot_session` | erpnext `startup/boot.py` sets sysdefaults; Swift appends prefs |
| `website_route_rules` | portal routes registered by ERPNext |
| `sounds` hook | erpnext sounds; Swift adds its own |

## Load order (desk page)

`desk.html` → `app_include_css` (frappe desk.css → erpnext.css → swift css) →
`libs.bundle.js` → `desk.bundle.js` (`frappe.app` boot) → Swift `swift-theme.js`
(waits for `boot`/DOM) → `frappe.ui.Sidebar`/`Toolbar`/`Container` build DOM → Swift decorators run.

## Risks

- If erpnext bundle loads before Swift, Swift's `$(document).ready`/`frappe.ready` ordering matters; Swift uses DOMContentLoaded + `frappe.boot` presence check.
- Adding a Swift bundle to `app_include_js` before `desk.bundle.js` will break (needs `frappe.ui`); must append after.
