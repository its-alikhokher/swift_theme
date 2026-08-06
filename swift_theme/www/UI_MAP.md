# Swift Theme — UI Map (Frappe v16 + ERPNext)

Phase 1. Reverse-engineered from bench at `/home/hassan/bench-16/apps/`.
Master index. Detail lives in PAGES_REFERENCE, FORM_REFERENCE, LIST_REFERENCE,
REPORT_REFERENCE, COMPONENT_LIBRARY, WEBSITE_REFERENCE, PORTAL_REFERENCE, BUILD_SYSTEM.

Legend: **S**=created by, **R**=rendered by, **JS**=controller, **CSS**=stylesheet, **Hook**=frappe hook,
**Ov**=can Swift Theme override?, **Risk**=1 low → 5 high.

## 1. Login

| Element | S | R | JS | CSS | Hook | Ov | Strategy / Risk |
|---------|---|---|-----|-----|------|----|-----------------|
| Login page (`/login`) | `frappe/www/login.py` + `frappe/www/login.html` (extends `templates/web.html`) | server Jinja → `web.html` layout | `templates/includes/login/login.js` (inlined) | `login.bundle.scss` + `web_include_css` (swift-login.css) | `web_include_css/js`, `website_context` (favicon/logo) | ✅ | Theme via `web_include_*` + `body.for-login` selectors (Swift already does). Risk 2 |
| Auth POST | core `login` whitelisted method (`frappe/auth.py`) | — | login.js `login.call` → `/api/method/login` | — | `on_login` (unused by Swift) | ⚠ | Do NOT override core login method; wrap via `on_login` if needed. Risk 5 |
| Forgot password | same login.html, `section.for-forgot` | hash-route `#forgot` | login.js `.form-forgot` → `frappe.core.doctype.user.user.reset_password` | login.bundle + swift-login | — | ✅ CSS | Style `.for-forgot`. Risk 2 |
| Reset password | `frappe/www/update_password.py` + template | server | `update_password` JS in template | login.bundle | — | ✅ CSS | Style page card. Risk 2 |
| Signup | same login.html, `section.for-signup` | hash-route `#signup` | login.js → `user.sign_up` | login.bundle | Website Settings `disable_signup` | ✅ | Swift hides signup via `login_show_signup`. Risk 1 |

## 2. Desk shell

| Element | S | R | JS | CSS | Hook | Ov | Strategy / Risk |
|---------|---|---|-----|-----|------|----|-----------------|
| Desk HTML shell | `frappe/www/desk.py` + `desk.html` | server | `desk.bundle.js` chain | `desk.bundle.scss` | `app_include_css/js`, `app_include_icons`, `sounds` | ⚠ | Never replace shell; inject via `app_include_*`. Risk 5 |
| Boot data | `frappe/sessions.py get_boot_info` | server JSON in `frappe.boot` | boot bundle | — | `boot_session`, `extend_bootinfo` | ✅ | Swift adds `bootinfo.swift_theme` via both. Risk 2 |
| Boot init | `desk.js` (`new frappe.views.Container`, `Toolbar`, `Sidebar`, Router) | `frappe/boot.js` → `frappe.app.start` | `desk.js` | `desk/main.scss` | — | ✅ | Swift's own boot runs alongside. Risk 3 |
| Router | `public/js/frappe/router.js` (`FrappeRouter`) | hash + history | maps route[0] → `<Title>Factory` | — | `router_route_rules` (unused) | ⚠ | Don't touch; register views via `frappe.views`. Risk 5 |
| Navbar | `ui/toolbar/toolbar.js` + `navbar.html` | `frappe.ui.toolbar.Toolbar` | toolbar.js | `desk/navbar.scss` | `app_include_js` (Swift chip injects here) | ✅ | Swift injects `.swift-chip` into `.navbar-nav`. Risk 2 |
| Sidebar (desk) | `ui/sidebar/sidebar.js` (+header/editor/card) | `frappe.ui.Sidebar` | sidebar.js, sidebar_item.js | `desk/sidebar.scss`, `list_sidebar.scss` | `workspace_sidebar` JSON data | ✅ | Swift decorates items, pin/unpin, hide mode. Risk 3 |
| Workspace | `views/workspace/workspace.js` + `blocks/*` | `frappe.views.Workspace` | workspace.js, widget_group.js | `desk/desktop.scss`, `module.scss` | `config/desktop.py` + `workspace/*.json` | ✅ | Style via `.widget`, `.workspace-title`. Risk 2 |
| Page container | `ui/page.js` + `page.html` | `frappe.ui.Page`/`make_app_page` | page.js | `desk/page.scss`, `main.scss` | — | ✅ | Style `.page-head`, `.page-title`, `.page-container`. Risk 2 |
| Breadcrumbs | `views/breadcrumbs.js` | `frappe.breadcrumbs` | breadcrumbs.js | `desk/breadcrumb.scss` | — | ✅ | Style `.page-breadcrumbs`. Risk 1 |
| Search (awesomebar) | `ui/toolbar/awesome_bar.js`, `search.js` + `search.html` | `frappe.search.SearchDialog` | search.js | `desk/global_search.scss` | `extend_awesome_bar_shortcuts` | ✅ | Theme focus ring; Swift themes `.awesomebar-input-row`. Risk 2 |
| Notifications | `ui/notifications/notifications.js` | popover | notifications.js | `desk/notification.scss` | `notification_config` | ✅ | Style `.dropdown-notifications`. Risk 2 |
| User menu | toolbar.js `set_dropdown_menu` + `navbar.html` | dropdown | toolbar.js | navbar.scss | `set_user_menu_items` | ✅ | Style `.dropdown-navbar-user`. Risk 1 |
| Theme switcher (L/D/A) | `ui/theme_switcher.js` | dialog | `frappe.ui.set_theme()` (sets `[data-theme]` on `<html>`) | `desk/theme_switcher.scss` | — | ✅ (coexists) | Swift layers `data-swift-*`; never writes `[data-theme]`. Risk 3 |
| Splash screen | `templates/includes/splash_screen.html` | desk.html include | desk.js removes | `splash_screen` scss | — | ✅ | Swift's `.swift-splash` used on website. Risk 1 |

## 3. Forms

| Element | S | R | JS | CSS | Hook | Ov | Strategy / Risk |
|---------|---|---|-----|-----|------|----|-----------------|
| Form view | `views/formview.js` (FormFactory) + `form/form.js` | `frappe.ui.form.Form` | form.js, layout.js, section.js, tab.js, column.js | `desk/form.scss` | `form_sidebar` config | ✅ | Style classes; don't re-render. Risk 3 |
| Form toolbar | `form/toolbar.js` | toolbar buttons | toolbar.js | form.scss | — | ✅ | CSS only. Risk 1 |
| Form tabs | `form/tab.js` | `.form-tabs` | tab.js | form.scss | — | ✅ | CSS. Risk 1 |
| Timeline / comments | `form/footer/form_timeline.js` + `base_timeline.js`, `templates/includes/comments` | footer | form_timeline.js | `desk/timeline.scss` | — | ✅ | CSS + custom blocks. Risk 2 |
| Assignments/Attachments/Share | `form/sidebar/assign_to.js`, `attachments.js`, `share.js` + `form_sidebar.js` | form sidebar | form/sidebar/* | `desk/form_sidebar.scss` | — | ✅ | CSS. Risk 2 |
| Child tables (grid) | `form/grid.js`, `grid_row.js`, `grid_row_form.js` | grid | grid.js | `common/grid.scss`, `form.scss` | `form_grid_template` (ERPNext overrides) | ✅ | CSS; ERPNext grids theme via `.grid-row`. Risk 2 |
| Quick Entry | `form/quick_entry.js` | dialog | make_quick_entry | form.scss | `quick_entry_doctypes` | ✅ | CSS only. Risk 1 |
| Form sidebar | `form/sidebar/form_sidebar.js` | `.form-sidebar` | form_sidebar.js | `desk/form_sidebar.scss` | — | ✅ | CSS. Risk 2 |

## 4. Lists / views

| Element | S | R | JS | CSS | Hook | Ov | Strategy / Risk |
|---------|---|---|-----|-----|------|----|-----------------|
| List view | `list/list_view.js` + `list_factory.js` + `list/base_list.js` | `frappe.views.ListView` | list_view.js | `desk/list.scss`, `list_sidebar.scss` | `list_view` view config | ✅ | Swift styles `.list-row`, rows already. Risk 2 |
| List sidebar/filters | `list/list_filter.js`, `list_sidebar_group_by.js`, `list_settings.js` | list view | — | `list_sidebar.scss` | — | ✅ | CSS. Risk 2 |
| Report view (datatable) | `views/reports/report_view.js` + datatable (frappe_datatable) | `frappe.views.ReportView` | report_view.js | `desk/frappe_datatable.scss`, `report.scss` | — | ✅ | Style `.dt-*` (Swift already). Risk 2 |
| Query report | `views/reports/query_report.js`, `report_factory.js` | `frappe.views.QueryReport` | query_report.js | report.bundle.scss | `web_include_css` report.bundle | ✅ | CSS. Risk 2 |
| Kanban | `views/kanban/kanban_view.js` (+ board/card/column) | `frappe.views.KanbanView` | kanban_view.js | `desk/kanban.scss` | — | ✅ | Swift styles kanban. Risk 2 |
| Calendar | `views/calendar/calendar.js` | `frappe.views.CalendarView` | calendar.js | `desk/calendar.scss` | — | ✅ | CSS. Risk 2 |
| Tree | `views/treeview.js` + `ui/tree.js` | `frappe.views.TreeView` | treeview.js | `desk/tree.scss` | — | ✅ | CSS. Risk 2 |
| Gantt | `views/gantt/` (frappe-gantt) | `frappe.views.GanttView` | gantt bundle | `desk/frappe_gantt.scss` | — | ⚠ | CSS + theme lib vars. Risk 3 |
| Image view | `views/image/` | `frappe.views.ImageView` | image view | `desk/image_view.scss` | — | ✅ | CSS. Risk 1 |
| File view | `views/file/` | `frappe.views.FileView` | file view | `desk/file_view.scss` | — | ✅ | CSS. Risk 1 |

## 5. Reports / dashboards

| Element | S | R | JS | CSS | Ov | Strategy / Risk |
|---------|---|---|-----|-----|----|-----------------|
| Dashboard (dashboard view) | `views/dashboard/dashboard_view.js` | extends ListView | `desk/dashboard_view.scss` | ✅ | Style `.widget`. Risk 2 |
| Number cards / charts widgets | `widgets/number_card_widget.js`, `chart_widget.js`, `widget_group.js` | widget group | `desk/dashboard_view.scss` | ✅ | Swift's theme gradient numbers. Risk 2 |
| Report summary cards | `views/reports/report_utils.js` | report view | report.scss | ✅ | CSS. Risk 1 |

## 6. Dialogs & feedback

| Element | S | R | JS | CSS | Ov | Strategy / Risk |
|---------|---|---|-----|-----|----|-----------------|
| Modal (Dialog) | `ui/dialog.js` (`frappe.ui.Dialog extends FieldGroup`) | modal | dialog.js | `common/modal.scss` | ✅ | CSS only. Risk 2 |
| Confirm | `ui/dialog.js` (Dialog subclass) | modal | `frappe.confirm` | modal.scss | ✅ | CSS. Risk 1 |
| Prompt | `ui/dialog.js` | modal | `frappe.prompt` | modal.scss | ✅ | CSS. Risk 1 |
| Toast/Alert | `ui/messages.js` (`frappe.show_alert`, `frappe.msgprint`) | toast | messages.js | `common/alert.scss`, `desk/toast.scss` | ✅ | Swift `swift-toast.css` targets `.desk-alert`. Risk 1 |
| Progress bar | `ui/progress.js` (v16? via `frappe.utils.make_progress_bar`) | inline | — | — | ✅ | CSS. Risk 1 |
| Tooltip | `ui/tooltip.js` (popper) | — | — | — | ✅ | CSS. Risk 1 |

## 7. Website / Portal

| Element | S | R | JS | CSS | Ov | Strategy / Risk |
|---------|---|---|-----|-----|----|-----------------|
| Website base | `templates/base.html` + `templates/web.html` | server | `frappe-web.bundle.js` + `website_script.js` | `website.bundle.scss` | `web_include_*` | ⚠ | Inject via web hooks. Risk 4 |
| Web navbar/footer | `templates/includes/navbar/*`, `footer/*` + `Website Settings` templates | web_block render | website_script.js | `website/navbar.scss`, `footer.scss` | `website_context` | ✅ | Swift themes `.website-navbar`. Risk 2 |
| Web Forms | `frappe/website/doctype/web_form` + `public/js/frappe/web_form/*.js` | `WebForm` page | web_form.js, web_form_list.js | `web_form.bundle.scss` | `web_form` doctype config | ✅ | CSS. Risk 2 |
| Error pages | `frappe/www/error.py`, `404.py`, `message.py` | server | — | `website/error-state.scss` | — | ✅ | Style `.error-page`. Risk 1 |
| Website Theme | `website/doctype/website_theme/website_theme.py` | SCSS compile into website theme | — | user `custom_scss` compiled | — | ✅ | Add `@import "erpnext/public/scss/website"` pattern. Risk 2 |

## 8. ERPNext UI surface

| Element | S | R | JS | CSS | Hook | Ov | Strategy / Risk |
|---------|---|---|-----|-----|------|----|-----------------|
| ERPNext desk bundle | `erpnext/public/js/erpnext.bundle.js` (POS, call popup, item selector, quick entries, telephony…) | app_include_js | many | `erpnext.bundle.scss` + `public/scss/*.scss` | `app_include_js/css` | ✅ | CSS layer covers. Risk 2 |
| POS | `public/js/point-of-sale.bundle.js` + `point-of-sale.scss` | POS app route | pos.js | `point-of-sale.scss` | `pos_app` | ⚠ | Separate UI; theme carefully. Risk 4 |
| Portal (orders/invoices) | `erpnext/templates/pages/order.html` + `website_route_rules` (`/orders`, `/invoices`…) | server + `www/portal.py` | `erpnext/public/js/conf.js`, `utils/party.js` | `order-page.scss` (via `website.scss`) | `website_route_rules`, `boot_session` | ✅ | Style `order-page.scss` classes. Risk 2 |
| Workspaces | `erpnext/**/workspace/*.json` + `workspace_sidebar/*.json` | Workspace view | workspace.js | desktop.scss | — | ✅ | Data; theme via CSS. Risk 1 |
| Sounds | `erpnext/public/sounds/*.mp3` | desk.html `<audio>` via `sounds` hook | — | — | `sounds` | ✅ | Add/replace via hook. Risk 1 |

## Cross-cutting conclusions

- **Rendering model:** Desk = JS SPA (server shells only). Website = server-rendered Jinja + small JS. Swift's CSS-first approach matches both.
- **Frappe's own theme system:** `[data-theme="light|dark"]` + `[data-theme-mode]` set server-side (desk.html) and by `theme_switcher.js`. Swift must keep layering `data-swift-*`, never overwrite.
- **Highest-risk override targets:** router, core login method, desk shell, POS. **Safest:** CSS variable/layer injection + `app_include_*` + `web_include_*` hooks.
- **Main extension surface for theming:** Frappe CSS tokens (see DESIGN_SYSTEM.md) → remap via `html[data-swift-*]` selectors; all frappe views already use token-based variables.
