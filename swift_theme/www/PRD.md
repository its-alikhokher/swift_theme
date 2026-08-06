# Swift Theme → GoldElite — PRD

Product: **GoldElite** — a Desktop Experience Layer for ERPNext v16 (built from Swift Theme).
Architecture blueprint in ARCHITECTURE.md.

## Vision

Replace nearly every visible part of ERPNext — chrome, navigation, home, search,
notifications, forms, lists — with a cohesive, premium desktop experience, without
modifying a single line of Frappe/ERPNext core.

## Positioning

- **Not** a CSS theme. A productized experience layer.
- 100% upgrade-safe: every capability is a replaceable, toggleable unit that falls back
  to a Frappe default when disabled or incompatible.

## Core principles (non-negotiable)

1. Modular — one system per concern (S1–S15).
2. Replaceable — any system can be swapped for a Frappe default via a flag.
3. Upgrade-safe — no core edits; adapter + contract-check pattern.
4. Optional — every feature off-by-default unless it is safe and desired.
5. CSS-first with thin JS decorators.

## Personas

| Persona | Need |
|---|---|
| System Admin | configure GoldElite centrally, per-tenant defaults, feature gating, audit |
| End User | fast daily workflow, own accent/density/light-dark, search + shortcuts |
| Developer | plugin API, documented contracts, debug tools |

## Feature scope (product-level)

| Area | Systems | Product value |
|---|---|---|
| Identity & look | S1 Theme, S6 Animation | accents, density, radius, fonts, glass, motion |
| Workspace | S2 Layout, S4 Navigation, S5 Workspace | dock/sidebar, home dashboard, module workspace |
| Power tools | S8 Shortcuts, S9 Search | command palette, global search |
| Attention | S10 Notifications | toast centre, sounds, unread |
| Desktop | S11 Windows | detach/dock views (optional, flagged) |
| Platform | S7 Settings, S12 APIs, S13 Plugins, S14 Flags, S15 Perf | config, extensibility, perf |

## Non-goals (explicit)

- No ERP business logic or data-model changes (beyond GoldElite's own settings DocType).
- No rewrite of POS (styled only).
- No modification of Frappe/ERPNext source.
- No backend for third-party plugins beyond declared hooks.

## Success criteria

- Boot overhead of GoldElite core < 80 KB gz; all systems lazy.
- Every feature independently toggleable (S14) with safe defaults.
- Zero edits to `apps/frappe` / `apps/erpnext`.
- Survives a Frappe minor + ERPNext minor upgrade via contract checks + fallback (matrix in TESTING_GUIDE).
- Full public API frozen at v1.0.

## Out of scope for v1 (see ROADMAP)

Window management/detachable views, third-party plugin marketplace, multi-monitor layouts.
