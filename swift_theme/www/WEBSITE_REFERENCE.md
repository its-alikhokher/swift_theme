# Swift Theme — Website Reference

Phase 1. Frappe v16 public website + Web Forms. Under `frappe/frappe/`.

## Template stack

| File | Role |
|------|------|
| `templates/base.html` | Root: `window.frappe={}`, `frappe.ready()` queue, `body[frappe-session-status][data-path]`, blocks: meta_block, favicon, head, style, navbar, content, footer, script. `{%- block navbar -%}` renders website navbar (from Website Settings) |
| `templates/web.html` | Extends base; `main_content()` macro → `.page-content-wrapper` > `.page-breadcrumbs` (`includes/breadcrumbs.html`) > `page_container` `<main class="container">` > `.page-header-wrapper` > `.page-header` + `.page-header-actions-block` > `.page_content` > `.page-footer`; sidebar via `includes/web_sidebar.html`; container attrs `id="page-{{name or route}}" data-path="{{route}}"`
| `templates/includes/*` | navbar/, footer/, breadcrumbs.html, web_sidebar.html, head.html, splash_screen.html, login/ |

## Page types

| Page | Source |
|------|--------|
| Web Form | `frappe/website/doctype/web_form/` + `public/js/frappe/web_form/web_form.js` (+ list), `web_form.bundle.scss` |
| Website Theme | `website/doctype/website_theme/website_theme.py` (custom_scss → compiled SCSS) |
| Dynamic pages | `frappe/www/*.py` + `*.html` (see below) |

## Server-rendered pages

| Page | Source | Notes |
|------|--------|-------|
| `/` | `frappe/www/__init__.py` route → Website Settings home + `www/robots.txt` |
| Login | `www/login.py` + `www/login.html` (extends web.html) | `email_login_body()` macro; sections: `section.for-login`, `section.for-forgot`, `section.for-signup`; `templates/includes/login/login.js` handles submit/forgot/signup + redirect; 2FA |
| Password reset | `www/update_password.py` | `templates/update_password.html` |
| Error | `www/error.py` | `templates/error.html` |
| 404 | `www/404.py` + `templates/404.html` | `web_include_css` applies |
| Message | `www/message.py` | custom message pages |
| Me | `www/me.py` | profile redirect |
| List (web) | `www/list.py` + `www/list.html` | renders `templates/list/` rows |
| Print view | `www/printview.py` + `www/printview.html` | `.print-format` (see print bundle) |
| Portal | `www/portal.py` + `templates/portal_page.html`? | rows via `frappe.render_template(row_template)`; `templates/pages/*.html` per doctype |
| Website assets | `frappe/website/doctype/website_theme/` + `public/scss/website*.bundle.scss` |

## Navbar / Footer (website)

- `templates/includes/navbar/navbar.html` + `navbar_items.html`; `website_context` hook builds `navbar_items`/`footer_items` (core: Website Settings → Main Menu).
- Footer: `templates/includes/footer/footer.html` (+ `footer_items.html`).
- Logo/branding: Website Settings (brand_html, logo).
- CSS: `website/navbar.scss`, `website/footer.scss`.

## Web Forms

- Entry: `/app/web-form/<name>`? Actually web forms route via `Web Form` doctype `route` field, rendered by `frappe.www.web_form`? — v16: `frappe/website/doctype/web_form/web_form.py` `get_context`; JS `public/js/frappe/web_form/web_form.js`.
- Submissions: `Web Form` + `Web Form Field` doctypes (business config — out of scope).
- CSS: `web_form.bundle.scss` (`web_include_css` not set for it — it is a standalone bundle loaded via page asset), plus `.web-form` classes.

## Website theming surface for Swift

| Surface | Mechanism |
|---------|-----------|
| CSS | `web_include_css` hook (Swift: `swift-web.css`, `swift-base.css`, `swift-login.css`) |
| JS | `web_include_js` (Swift: `swift-web.js`, `swift-logo.js`) |
| Theme SCSS | Website Theme custom_scss + ERPNext `website_theme.js` `@import "erpnext/public/scss/website"` pattern — Swift can add `@import "swift_theme/public/scss/website"` similarly |
| Body classes | server sets `data-path`; Swift CSS scoped `body[data-path^="/"]` for homepage-only chrome |

## Key constraints / risk

- Website is server-rendered; Swift CSS/JS must survive before `frappe.ready` (Swift boots on `DOMContentLoaded`, not `frappe.ready`, to control splash timing).
- `web.html` page container changes (`page-{name}`) — Swift homepage detection uses `body[data-path="/"]` + `[data-sidebar]` guards.
- Risk 3: overriding Website Theme SCSS may conflict with ERPNext's `@import` injection.
