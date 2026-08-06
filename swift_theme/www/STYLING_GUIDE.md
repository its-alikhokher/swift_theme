# Swift Theme — Styling Guide

Phase 1. How Swift applies styling on top of Frappe v16. Rules for future implementation.

## Principles

1. **CSS-first.** Never rewrite Frappe JS; never patch `frappe.ui.*` or `frappe.views.*` classes. All visual changes via CSS variables + scoped selectors.
2. **Token-based.** Override Frappe tokens (DESIGN_SYSTEM.md) at `html` level, driven by `data-swift-*` attributes. Never duplicate palette values in component rules.
3. **Attribute-driven.** Swift switches are `data-swift-theme`, `data-swift-accent`, `data-swift-radius`, `data-swift-density`, `data-swift-sidebar`, `data-swift-nav-mode`, `data-swift-toast`. Frappe owns `data-theme` / `data-theme-mode`.
4. **No !important** except a documented compat block at the end of `swift-base.css`.
5. **CSS layers** ordered: `@layer swift-base, swift-themes, swift-components, swift-overrides;` appended to `swift-desk.css`.

## Selector scoping (current Swift patterns)

| Context | Selector |
|---------|----------|
| Desk whole app | `html[data-swift-theme]:not([data-swift-theme=""])` |
| Dark | `html[data-swift-theme][data-theme-mode="dark"]` (auto-aware) |
| Sidebar | `#body .sidebar` (legacy) vs `html[data-swift-sidebar] .layout-side-section` (v2) — **mismatch risk, see DECISIONS.md** |
| Navbar chip | `header .navbar-nav` (injected `.swift-chip`) |
| Command palette | `.swift-palette` (custom) |
| Login | `body.for-login` |
| Website | `body[data-path="/"]` homepage, `.swift-web` components |
| Toast | `.desk-alert`, `.swift-toast-wrap` |

## Accent maps

Defined in `swift-themes.css` for `data-swift-accent` = blue (default), violet, teal, rose.
Each map sets `--swift-accent-h`, `--swift-accent-s`, `--swift-accent-l` (and -2/-1/+1/+2 ladder),
`--swift-accent-rgb`. Derived colors computed via `hsl()` from hue/saturation — single source of truth.

## Density & radius

- `data-swift-radius` → `--swift-radius` used by `--radius-sm/md/lg`.
- `data-swift-density` → `--swift-density` consumed by row/section `min-height`/`padding` rules in `swift-desk.css`.

## File responsibilities (current)

| File | Responsibility |
|------|----------------|
| `swift-base.css` | reset, `data-swift-*` variable definitions, compat block |
| `swift-themes.css` | accent maps, per-accent overrides |
| `swift-desk.css` | navbar/sidebar/forms/lists/grid/kanban, pins, palette, mode badge |
| `swift-login.css` | login card, glass layout, gradients |
| `swift-web.css` | website navbar/footer/home/portal |
| `swift-toast.css` | toast restyle |
| `swift-perf.css` | content-visibility, scrollbar, transitions |

## Verification

- Manual: v16 desk, dark mode via `data-theme-mode="dark"`, sidebar pin, command palette open,
  login page, portal order page, print view — contrast on accents.
- Keep DevTools "Emulate prefers-color-scheme" test for auto mode.
- No regression to Frappe's own `desk.bundle.css` — Swift never edits `public/` in frappe repo.
