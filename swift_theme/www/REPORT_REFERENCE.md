# Swift Theme — Report Reference

Phase 1. Frappe v16 reports & dashboards. Under `frappe/public/js/frappe/views/reports/`.

## Query report

| Item | Source |
|------|--------|
| Route | `/app/query-report/<name>` → `frappe.views.QueryReport` (`query_report.js`) |
| Factory | `report_factory.js` (QueryReportFactory, ReportFactory) |
| Data table | `frappe_datatable` (`ui/datatable.js`), cells `.dt-*` |
| Chart | `ui/chart.js` (frappe-charts) |
| Filters | `report_utils.js` (report summary cards, chart options, export) |
| Print | `print_grid.html`, `print_tree.html` (template in views/reports) |

CSS: `desk/report.scss`, `desk/frappe_datatable.scss`, `report.bundle.scss` (frappe hook `app_include_css`).

## Script report / Custom Report

- `frappe.core.doctype.report` server-side (business logic — out of scope).
- `print_tree.html` for tree reports.

## Dashboards & number cards

| Item | Source |
|------|--------|
| Dashboard (doctype) | `frappe/desk/dashboard` + `views/dashboard/`? v16 dashboard built from workspace widgets + `Dashboard` doctype (`frappe/core/doctype/dashboard`) |
| Dashboard view | `views/dashboard/dashboard_view.js` (extends `ListView`) |
| Widgets | `widgets/number_card_widget.js`, `chart_widget.js`, `shortcut_widget.js`, `links_widget.js`, `quick_list_widget.js`, `widget_group.js` |
| CSS | `desk/dashboard_view.scss`, `desk/desktop.scss` |

## Override strategy

- Swift already themes `.dt-header`, `.dt-cell`, `.dt-row`, `.report-summary`, `.widget`, `.number-card` (swift-desk.css + swift-themes.css multi-color numbers).
- Datatable is token-based; remap `--dt-*`? (see frappe_datatable.scss) — safe to extend.
- Risk: chart canvas (SVG) colors come from `ui/chart.js` palette; theme via `frappe.ui.Chart` options, not CSS.
