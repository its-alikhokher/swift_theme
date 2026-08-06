# Swift Theme — Pages Reference (Desk shell chrome)

Phase 1. Desk shell elements: boot, navbar, sidebar, workspace, page container,
breadcrumbs, search, notifications, user menu. See UI_MAP for the overview table.

## Boot & shell

| Item | Detail |
|------|--------|
| HTML shell | `frappe/www/desk.py` (context) → `frappe/www/desk.html`. Sets `<html data-theme-mode data-theme>` from `boot.desk_theme`, renders `app_include_css`, splash, `<header></header>`, `<div id="body"></div>`, `<footer></footer>`, `app_include_js`, `app_include_icons`, `sounds` audio tags |
| Main JS | `public/js/frappe/boot.js` (startup) → `desk.js` (`frappe.app`): `make_sidebar()`, `setup_theme()`, `make_page_container()` (`new frappe.views.Container`), `make_nav_bar()` (`new frappe.ui.toolbar.Toolbar`) |
| Bundles | `desk.bundle.js`, `list.bundle.js`, `form.bundle.js`, `controls.bundle.js`, `report.bundle.js`, `libs.bundle.js` (frappe hooks `app_include_js`) |
| Page creation | `router.js` → route[0] → `frappe.views.<Title>Factory` → `container.add_page()` (`.content.page-container`) → `frappe.make_page` → `ui/page.js::make_app_page` |
| Body attrs | `container.js` sets `body[data-route]`, `body[data-sidebar]` on `page-change` |

## Navbar

- Renderer: `ui/toolbar/toolbar.js` → `frappe.render_template("navbar")` → `ui/toolbar/navbar.html`.
- Layout: `.navbar` → `.navbar-right` → `.navbar-nav` (dropdown-help, awesomebar, user).
- Announcement widget: rendered if `navbar_settings.announcement_widget` present (dismissable, localStorage `dismissed_announcement_widget`).
- Menu items API: `set_help_icons`, `set_dropdown_menu`, `add_dropdown_item`, `add_user_indicator` — `$(document).trigger("toolbar_setup")` after make.
- Swift hook: `swift-switcher.js` injects `.swift-chip` nav-item at front of `.navbar-nav` (targets `header .navbar-nav`).
- CSS: `public/scss/desk/navbar.scss`.

## Desk sidebar (module/workspace navigator)

- Renderer: `ui/sidebar/sidebar.js` (`frappe.ui.Sidebar`, boot on `frappe.app.make_sidebar`), `sidebar_header.js`, `sidebar_editor.js`, `sidebar_card.js` + templates `sidebar.html`, `sidebar_item.html`, `sidebar_header.html`, `sidebar_card.html`.
- Data: `frappe.boot.workspace_sidebar_item` (built server-side from each app's `workspace_sidebar/*.json` + workspaces). ERPNext ships many (see UI_MAP).
- Features: edit mode, nested items, pins, promotional banners (CRM/Helpdesk), app logo subtitle.
- Swift hook: `swift-sidebar.js` pins (`★`), reorders pinned to top (`.swift-pinned-group`), hide-off mode `data-swift-sidebar="off"` + restore button, Alt+B.
- CSS: `desk/sidebar.scss`, `sidebar_header.scss`, `sidebar_card.scss`, `desk/sidebar_card.scss`, `list_sidebar.scss`.

## Workspace view

- Renderer: `views/workspace/workspace.js` (`frappe.views.Workspace`) + `widgets/*` (base_widget, chart_widget, number_card_widget, shortcut_widget, links_widget, quick_list_widget, custom_block_widget, onboarding_widget, widget_group) + `blocks/*` HTML.
- Data: `workspace/*.json` per app (ERPNext: 12 modules) + `config/desktop.py` module icons.
- CSS: `desk/desktop.scss`, `desk/module.scss`, `desk/dashboard_view.scss`, `sidebar_card.scss`.

## Page container (form/list/report chrome)

- Renderer: `ui/page.js` (`frappe.ui.Page`, `make_app_page`) + template `ui/page.html`.
- Structure: `.page-head` → `.page-title` (breadcrumbs `<ul class="navbar-breadcrumbs">` + title h1) + `.standard-items-section` (filters, custom-actions, standard-actions, actions menu, primary-action).
- `.page-body` → `.page-toolbar` (hidden) → `.page-wrapper` → `.page-content` → `body[data-route]` switches per-view content.
- Sidebar placement: `frappe.make_page(double_column, name, sidebar_position)`.
- CSS: `desk/page.scss`, `desk/main.scss` (`.layout-side-section` margins), `desk/breadcrumb.scss`.

## Breadcrumbs

- Renderer: `views/breadcrumbs.js` (`frappe.breadcrumbs`) — `update()` on page-change, `rename()` on doc rename, `add_parent` etc. from views.
- CSS: `desk/breadcrumb.scss` (`.page-breadcrumbs`, `.breadcrumb`).

## Search / Awesomebar

- Renderer: `ui/toolbar/awesome_bar.js` + `search.js` + template `search.html` (`.awesomebar-input-row`, global search dialog `frappe.search.SearchDialog`).
- Hook: `extend_awesome_bar_shortcuts` (available, unused).
- CSS: `desk/global_search.scss`, `desk/menu.scss`.

## Notifications

- Renderer: `ui/notifications/notifications.js` (`frappe.ui.Notifications`, popover `.dropdown-notifications`), driven by realtime `notification` events.
- Hook: `notification_config` (per-doctype, unused).
- CSS: `desk/notification.scss`.

## User menu

- In `toolbar.js::set_dropdown_menu`; template `navbar.html`; items via `frappe.ui.toolbar.Toolbar.add_user_indicator` + core user actions (My Settings, Logout).
- Hook: `set_user_menu_items` (available, unused).
- CSS: `navbar.scss`, `user_profile.scss`.

## Theme switching (Frappe native)

- `ui/theme_switcher.js`: dialog with Light/Dark/Auto. `frappe.ui.set_theme(theme)` sets `<html data-theme>`; `data-theme-mode` holds user pref ("light"/"dark"/"automatic"); auto mode listens `prefers-color-scheme`.
- `desk.js` MutationObserver re-syncs on `data-theme-mode` changes; Swift `swift-mode-observer.js` reacts and fires `swift:mode-changed`.
- CSS: `desk/theme_switcher.scss`, `dark.scss` (v16 dark palette).

## Splash

- `templates/includes/splash_screen.html` (`.splash` with logo spinner) shown in desk.html, removed by `make_page_container()`. Swift website splash is `.swift-splash` (separate).
