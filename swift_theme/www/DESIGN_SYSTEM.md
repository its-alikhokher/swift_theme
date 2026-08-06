# Swift Theme — Design System

Phase 1. Frappe v16 design tokens + Swift's theme layer mapping.

## Frappe core tokens

| Token group | Source SCSS | Examples |
|-------------|-------------|----------|
| CSS variables (root) | `public/scss/common/css_variables.scss` | `--navbar-height: 48px`, `--page-max-width: 900px`, `--bg-*` pairs, `--text-*`, spacing `--margin-*`, `--radius-*` |
| Light palette | `common/css_variables.scss` | `--bg-gray-100..900`, `--border-color`, `--text-color` |
| Dark palette | `desk/dark.scss` (overrides under `[data-theme="dark"]`) | dark `--bg-*`, `--control-bg` |
| Component vars | component scss files | `--btn-primary-bg`? (buttons.scss), `--form-control-bg` (controls.scss) |

Notes: Frappe v16 is Bootstrap 5 + CSS custom properties. `[data-theme-mode]` (user pref:
light/dark/automatic) vs `[data-theme]` (resolved light/dark). `desk.html` sets both server-side;
`theme_switcher.js` updates on switch; auto mode uses `prefers-color-scheme`.

## Swift theme layer

| Layer | File | Applies |
|-------|------|---------|
| Base | `swift-base.css` | tokens, resets, root `html[data-swift-accent]` accent/density/radius variables |
| Themes | `swift-themes.css` | per-accent color maps (`data-swift-accent="blue|violet|teal|rose"`) |
| Desk | `swift-desk.css` | `.navbar`, `.sidebar`, `.form-section`, `.grid-row`, `.list-row`, sidebar pins, command palette |
| Login | `swift-login.css` | `body.for-login` card/glass layout |
| Web | `swift-web.css` | website navbar/footer, homepage, portal order page |
| Toast | `swift-toast.css` | `.desk-alert` restyle + floating container |
| Perf | `swift-perf.css` | `content-visibility:auto` on `.list-row`, grid rows |

### Root variable overrides

```
html[data-swift-theme]:not([data-swift-theme=""]) {
  --navbar-height: 48px;            /* keep Frappe metric */
  --page-max-width: 1120px;         /* wider content */
  --container-padding-x: 24px;
  --radius-sm/md/lg: remap from data-swift-radius;
  --accent-*: set from data-swift-accent;
  --density: 0 (comfortable) | 1 (compact);
}
html[data-swift-theme][data-theme-mode="dark"] { /* auto-mode awareness */ }
```

## Icon system

- Frappe icons: `lucide` SVG sprite + `timeless`/`espresso` (hooks `app_include_icons`), rendered via `frappe.utils.get_icon_html`? / `frappe.render`; icons in `ui/icons.js` (`frappe.ui.icon()`? v16 `frappe.ui.get_icon`).
- Swift favicon/branding: `swift-logo.js` swaps brand via hook? — Swift provides logo in `public/` and Website Settings; desk brand = `frappe.boot.`? (desktop page).

## Spacing / layout metrics (from `css_variables.scss`)

`--page-max-width: 900px`, `--container-padding-x`, `--navbar-height: 48px`,
`--sidebar-width: 240px`, `--form-section-padding` etc. — Swift overrides via same names.

## Density

- Frappe has no official density API; Swift uses `html[data-swift-density="compact"]` to reduce `--control-sm` paddings, row min-heights, section margins. Must keep Bootstrap `form-control` heights for a11y.

## Risk notes

- Frappe hardcodes some hex colors outside tokens (charts palette in `ui/chart.js`, some `desk/*.scss`) — those need per-file SCSS override, not variables.
- `dark.scss` uses `[data-theme="dark"]`; Swift's dark variants must select `html[data-swift-theme][data-theme-mode="dark"]` to stay compatible with auto mode.
