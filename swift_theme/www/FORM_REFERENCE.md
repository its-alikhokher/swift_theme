# Swift Theme — Form Reference

Phase 1. Frappe v16 form rendering pipeline. All under `frappe/public/js/frappe/`.

## View factory & controller

| Item | Source |
|------|--------|
| Route | `/app/Form/<doctype>/<name>` → `frappe.views.FormFactory` (`views/formview.js`) |
| Controller | `frappe.ui.form.Form` (`form/form.js`), built via `FormLayout` (`form/layout.js`) |
| Sections | `form/section.js`, `form/column.js`, `form/tab.js` (`.form-section`, `.form-column`, `.form-tabs`) |
| Template helpers | `templates/form_macros.html` (frappe) |

## Toolbar

- `form/toolbar.js` — buttons: Primary action, Save, actions dropdown, menu, toggle sidebar, minimize.
- Rendered into `page.html` `.standard-actions` (`.actions-btn-group`, `.primary-action`).
- Custom buttons: `frm.add_custom_button` → `.custom-actions` area.
- CSS: `desk/form.scss`, `desk/page.scss`.

## Timeline / comments / activity

- `form/footer/form_timeline.js` (`FormTimeline`) + `base_timeline.js`; shared `Communication` views (`views/communication.js`).
- Template: `templates/includes/comments/*` + `templates/form_grid/`? no — comments in `public/js/frappe/form/footer/`.
- CSS: `desk/timeline.scss`, `desk/version.scss` (version/audit rows).

## Form sidebar (right column)

| File | Purpose |
|------|---------|
| `form/sidebar/form_sidebar.js` | container `.form-sidebar` |
| `form/sidebar/assign_to.js` | assignments |
| `form/sidebar/attachments.js` | attachments (also `file_uploader/`) |
| `form/sidebar/share.js` | sharing |
| `form/sidebar/document_follow.js` | follow |
| `form/sidebar/user_image.js` | user avatar row |
- CSS: `desk/form_sidebar.scss`.

## Grids (child tables)

| File | Purpose |
|------|---------|
| `form/grid.js` | `frappe.ui.form.Grid` (`.frappe-control[data-fieldtype="Table"]`) |
| `form/grid_row.js`, `form/grid_row_form.js`, `form/grid_pagination.js` | rows, inline edit, pagination |
| `templates/form_grid/*.html` | row templates; ERPNext overrides via `form_grid_template` (item_grid.html, stock_entry_grid.html, material_request_grid.html, bank_reconciliation_grid.html) |
- CSS: `common/grid.scss`, `desk/form.scss`.

## Quick Entry

- `form/quick_entry.js` — `frappe.ui.form.make_quick_entry(doctype, ...)`; per-doctype overrides `frappe.ui.form[Doctype]QuickEntryForm`.
- Hook: `quick_entry_doctypes` (ERPNext uses `utils/customer_quick_entry.js`, `supplier_quick_entry.js`, `contact_address_quick_entry.js`, `item_quick_entry` template).

## Save / workflow

- `form/save.js`, `form/workflow.js`, `form/undo_manager.js`, `form/success_action.js` (custom success dialogs), `form/script_manager.js` (client scripts).
- Dialogs from form: `multi_select_dialog.js`, `link_selector.js`, `linked_with.js`.

## Override strategy for Swift Theme

- CSS-only: target tokenized vars; never restructure `.form-section`/`.form-grid`.
- Swift already themes `.form-section`, `.layout-main-section`, `.form-control`, `.grid-row` via `swift-themes.css` / `swift-base.css`.
- New premium chrome (e.g. richer timeline, carded sections) → add new layers in `swift-desk.css` scoped by `html[data-swift-theme]:not([data-swift-theme=""])` or `html[data-swift-accent]`.
- Do NOT touch `form/form.js` or grid internals (risk 5).
