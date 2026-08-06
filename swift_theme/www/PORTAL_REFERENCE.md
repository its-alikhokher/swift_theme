# Swift Theme — Portal Reference

Phase 1. Frappe + ERPNext portal (customer-facing pages).

## Frappe portal core

| Item | Detail |
|------|--------|
| Route | `/portal` → `frappe/www/portal.py` → `templates/portal_page.html`; lists documents per `portal_menu_items` / Website Settings portal settings |
| Row rendering | `frappe.render_template(row_template, {...})` — each doctype provides a row template (`templates/pages/*.html` or `_row.html`) |
| Data | server `get_context()` builds `rows` from Portal Settings doctypes |
| Breadcrumbs | `templates/includes/breadcrumbs.html` (home / portal / entity) |

## ERPNext portal routes (`erpnext/hooks.py:121` `website_route_rules`)

| Rule | Target |
|------|--------|
| `/orders` | Sales Order list |
| `/orders/<path:name>` | Sales Order detail → `erpnext/templates/pages/order.html` |
| `/invoices` | Sales Invoice list |
| `/invoices/<path:name>` | Sales Invoice detail → `order.html` (shared template) |
| `/supplier-quotations` | Supplier Quotation list |
| `/supplier-quotations/<path:name>` | detail |
| also | `/purchase-order`, `/order-return`, `/order-return/<name>`, `/projects` etc. (see hooks.py) |

- Breadcrumb parents set in `get_context` (portal routes add `<path:name>` with parent list route).
- Conf JS: `erpnext/public/js/conf.js`, party utils `utils/party.js` (company/finance display).

## Portal templates (ERPNext)

`erpnext/templates/pages/order.html` + `order_home.html`, `rfq.html`, `task_info.html`,
`partners.html`, `help.html`, `projects.html`, `material_request_info.html`, `timelog_info.html`,
`_row.html` variants under `templates/includes/` (e.g. `order_row.html`).

## CSS surface

- ERPNext: `erpnext/public/scss/website.scss` (imports `order-page.scss`, POS?) + `erpnext-web.bundle.scss`.
- Swift: `swift-web.css` styles `.order-page`, `.order-status`, `.order-item-table`, `.print-format`.

## Risks / notes

- Portal detail pages render raw tables + print-like layouts; Swift's `.swift-web` layers must not break `print-format`/`web_print` classes.
- Custom row templates are Python config (`get_website_row_template`?) — Swift will not change server templates (discovery only); theme strictly via CSS.
