# Swift Theme — Component Library

Phase 1. Reusable Frappe v16 UI components and their extension points.

## Modal & dialogs

| Component | Source | Class / API | CSS | Override |
|-----------|--------|-------------|-----|----------|
| Modal | `ui/dialog.js` | `frappe.ui.Dialog` (extends `FieldGroup`) | `common/modal.scss` | CSS only (`.modal`, `.modal-dialog`) |
| Confirm | `ui/dialog.js` | `frappe.confirm(msg, onyes, oncancel)` | modal.scss | CSS |
| Prompt | `ui/dialog.js` | `frappe.prompt(fields, callback)` | modal.scss | CSS |
| Field group | `form/field_group.js` + `form/controls/field.js` | `frappe.ui.FieldGroup` | `common/controls.scss` | CSS |
| Multi-select | `form/multi_select_dialog.js` | `frappe.ui.form.MultiSelectDialog` | controls.scss | CSS |

## Feedback

| Component | Source | API | CSS | Override |
|-----------|--------|-----|-----|----------|
| Toast/Alert | `ui/messages.js` | `frappe.show_alert(msg, type)` (`.desk-alert`), `frappe.toast` | `desk/toast.scss`, `common/alert.scss` | CSS (Swift `swift-toast.css`) |
| Message box | `ui/messages.js` | `frappe.msgprint(msg, title, minimize)` → modal | modal.scss | CSS |
| Progress | `ui/progress.js` | `frappe.utils.make_progress_bar` | `desk/form.scss` | CSS |
| Tooltip | `ui/tooltip.js` | popper-based, `frappe.tooltip` | — | CSS |

## Navigation

| Component | Source | API | CSS |
|-----------|--------|-----|-----|
| Awesomebar | `ui/toolbar/awesome_bar.js`, `search.js` + `search.html` | `frappe.search.SearchDialog` | `desk/global_search.scss` |
| Dropdown | `ui/dropdown.js`? — v16 uses `frappe.ui.CustomDropdown`/BS5 | `.dropdown` BS5 | `common/dropdown.scss`, `desk/menu.scss` |
| Menu (user) | `ui/toolbar/toolbar.js::set_dropdown_menu` | `frappe.ui.toolbar.Toolbar` | navbar.scss |
| Breadcrumbs | `views/breadcrumbs.js` | `frappe.breadcrumbs` | desk/breadcrumb.scss |
| Tabs | `form/tab.js` | BS5 tabs | form.scss |
| Accordion | — | BS5 | — |

## Tables & grids

| Component | Source | API | CSS |
|-----------|--------|-----|-----|
| DataTable | `ui/datatable.js` + `frappe_datatable` build | `frappe.DataTable` | `desk/frappe_datatable.scss` |
| Tree | `ui/tree.js` | `frappe.ui.Tree` | `desk/tree.scss` |
| Chart | `ui/chart.js` (frappe-charts) | `frappe.Chart` | — (SVG) |
| Grid (child table) | `form/grid.js` | `frm.grids[...]` | common/grid.scss |

## Filters / search

| Component | Source | API | CSS |
|-----------|--------|-----|-----|
| Filters control | `list/list_filter.js` + `ui/filters/filters.js` | `frappe.ui.Filters` | `desk/filters.scss` |
| Link/Select control | `form/controls/autocomplete.js`, `select.js`, `link.js` | field controls | common/controls.scss |
| Tags | `form/controls/tags.js` | field control | desk/tags.scss |

## Misc

| Component | Source | CSS |
|-----------|--------|-----|
| Spinner / loaders | `ui/loader.js` (`frappe.ui.loaders`) + `desk.html` `.spinner` | common/controls.scss |
| Modal splash | `templates/includes/splash_screen.html` | splash_screen scss |
| Indicator | `ui/badge.js`? — `frappe.utils.get_indicator` + templates | desk/list.scss |
| Banner / announcement | toolbar.js navbar widget | navbar.scss |
| Avatar | `ui/user_image.js` + `utils/utils.js` | desk/user_profile.scss |

## Extension pattern for Swift

- All components render into `#body .content .page-container .content` with stable `.page-content` wrappers → Swift themes by CSS layer + `html[data-swift-accent]`/`html[data-swift-density]` selectors.
- Behavioral customization: attach to Frappe events (see EVENTS_REFERENCE.md), do NOT subclass `frappe.ui.Dialog`/`FieldGroup` unless Frappe provides a hook (it does not) — risk 4.
