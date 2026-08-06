# Swift Theme — List Reference

Phase 1. Frappe v16 list/view rendering. All under `frappe/public/js/frappe/`.

## List view

| Item | Source |
|------|--------|
| Route | `/app/List/<doctype>` → `frappe.views.ListFactory` (`list/list_factory.js`) → `frappe.views.ListView` (`list/list_view.js`) extends `BaseList` (`list/base_list.js`) |
| Rows | `.list-row-container` → `.list-row` (`.list-row--head`, `.list-row--col`); count badge, checkboxes |
| Sidebar | `list/list_sidebar_group_by.js`, `list/list_sidebar_stat.html`, `.list-sidebar` (filters/tags/group-by) |
| Filter control | `list/list_filter.js` + `ui/filters/`; `list/list_settings.js` (column settings dialog) |
| Select/bulk | `list/list_view_select.js`, `list/bulk_operations.js` (bulk update/delete/print) |
| Templates | `list/base_list.js` uses `ui/listing.html` + `views/container` layout |

CSS: `desk/list.scss`, `desk/list_sidebar.scss`, `desk/filters.scss`, `desk/tags.scss`.

## Alternate views (route suffix on List)

| View | Route | Factory/Class | CSS |
|------|-------|---------------|-----|
| Report | `/List/<dt>/report` | `frappe.views.ReportFactory` → `ReportView` | `desk/report.scss`, `frappe_datatable.scss` |
| Kanban | `/List/<dt>/kanban` | `views/kanban/kanban_view.js` (`KanbanView`, `KanbanBoard`) | `desk/kanban.scss` |
| Calendar | `/List/<dt>/calendar` | `views/calendar/calendar.js` (`CalendarView`) | `desk/calendar.scss` |
| Tree | `/app/Tree/<dt>` | `views/treeview.js` (`TreeView`) + `ui/tree.js` | `desk/tree.scss` |
| Gantt | `/List/<dt>/gantt` | `views/gantt/` (frappe-gantt lib) | `desk/frappe_gantt.scss` |
| Image | `/List/<dt>/image` | `views/image/image_view.js` | `desk/image_view.scss` |
| File | `/app/File/...` | `views/file/file_view.js` | `desk/file_view.scss` |
| Dashboard | workspace widgets | `views/dashboard/dashboard_view.js` (extends ListView) | `desk/dashboard_view.scss` |
| Map | `/List/<dt>/map` | `views/map/` (leaflet) | — |

## List querying

- Server: `frappe/core/doctype/report/...`? No — list data via `frappe.client.get_list` / `frappe.call("frappe.client.get_list")` through `db.js`/`request.js`.
- `list_view.js` calls `frappe.call("frappe.core.doctype.doctype_list...")`? (not UI-relevant).

## Override strategy

- Swift already targets `.list-row`, `.list-row-container`, `.indicator-pill`, `.filter-section` (swift-desk.css) + content-visibility perf (swift-perf.css).
- Grouped view selectors are stable across v16; style via tokens. Avoid JS patching of list internals (risk 4); prefer `frappe.ui.form`/`listview` event hooks for any behavior.
