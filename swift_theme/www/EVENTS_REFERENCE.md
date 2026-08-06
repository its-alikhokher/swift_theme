# Swift Theme — Events Reference

Phase 1. Frappe v16 DOM/app events Swift can hook.

## Frappe app events

| Event | Fired | Where |
|-------|-------|-------|
| `app_ready` | after `frappe.app.start` boot | `frappe/app.js` |
| `page_change` | on route change (also `frappe.views.pageview.show`) | `frappe/router.js`, `container.js` (`body[data-route]` set) |
| `page_show` | per-view show | `frappe/views/*` |
| `page_render` | after view render | views |
| `toolbar_setup` | after navbar built (`$(document).trigger("toolbar_setup")`) | `ui/toolbar/toolbar.js` |
| `boot` | broadcast after desk boot | `desk.js` |
| `refresh` / `after-refresh` | form refresh (Form) | `form/form.js` |
| `list_view.refresh` | list refresh | `list/list_view.js` |
| `report:refresh` | report refresh | `views/reports/query_report.js` |
| `frappe.ui.chart` events | chart rendered | `ui/chart.js` |
| `shown.bs.modal` | dialog shown | `ui/dialog.js` |

## DOM events

| Event | Element | Note |
|-------|---------|------|
| `data-theme-mode` change (MutationObserver) | `<html>` | frappe theme switch; Swift `swift-mode-observer.js` reacts + fires `swift:mode-changed` |
| `storage` | window | cross-tab pref sync (Swift uses localStorage) |
| `hashchange`/`popstate` | window | router (Swift CSS-only, no route logic) |
| `document:view` custom | document | Swift fires `swift:sidebar-changed`, `swift:accent-changed`, `swift:mode-changed` for JS companions |

## Server → client events (realtime)

| Channel | Meaning |
|---------|---------|
| `notification` | notifications bell (core `frappe.ui.Notifications`) |
| `refresh` | doc update → `frappe.ui.form.Form` refresh |
| `list_update` | list refresh |

## Swift events

`swift:mode-changed`, `swift:sidebar-changed`, `swift:accent-changed`, `swift:density-changed`,
`swift:command`, `swift:menu` — dispatched by `swift-switcher.js`/`swift-mode-observer.js`.

## Risks

- `page_change` fires on every route change; perf-sensitive Swift handlers must debounce/throttle.
- Frappe may move event names between versions; wrap in feature-detection (`frappe.views.pageview` check) before relying.
