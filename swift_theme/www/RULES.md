# Swift Theme → GoldElite — Engineering Rules

Applies to all implementation phases. Architecture in ARCHITECTURE.md.

## Core rules

| # | Rule |
|---|------|
| R1 | NEVER modify files in `apps/frappe` or `apps/erpnext`. Any need to = design bug → use a hook/adapter instead |
| R2 | All Frappe interaction through `services/frappe/*` adapters; no other file touches `frappe.*` globals |
| R3 | Every capability behind a feature flag (S14) with a safe default (Frappe behavior) |
| R4 | CSS-first: tokens (`--ge-*`), `@layer goldelite`, attributes `data-ge-*`, classes `.ge-*`. No `!important` except a documented compat block |
| R5 | Public API `GE.*` frozen at 1.0; changes only via major version; deprecate → remove, never break |
| R6 | Lifecycle hygiene: every system `init()→mount()→destroy()`; remove all listeners/observers on `page_change` |
| R7 | Contract-first: every Frappe API used has a boot-time shape check; failure disables the feature gracefully (no error cascade) |
| R8 | Hide, never remove: Frappe DOM elements are hidden (display), not deleted — preserves Frappe JS assumptions |
| R9 | Lazy-load everything except core (S7+S12+S14); dynamic import per system; CSS chunks by enabled flags |
| R10 | Observer budget: one MutationObserver per concern; no polling loops; rAF for animation |

## Code conventions

- Namespace: `GE`; internal modules `systems/<name>/`; components `GE.ui.component(name)`.
- No new npm dependencies without architect review; no external animation/CSS frameworks.
- Strings/descriptions for every flag + shortcut (shown in help/settings).
- Accessibility: honor `prefers-reduced-motion`; keyboard parity for all owned components; AA contrast on accents.
- No emojis in UI text or code.

## Safety gates

| Gate | Check |
|---|---|
| Boot | contract checks pass or features disabled (log-only) |
| Flag change | applies live, never requires manual asset reload except `replace-chrome` |
| Migrations | transactional; v1 settings shim reads legacy keys one release, then removed |
| Dist | `bench build --app swift_theme` must succeed; committed dist in sync with sources |
| Tests | unit + contract + a11y + visual per system; perf budgets warn-only |

## Documentation rules

- Append-only to `www/*.md`; never create new `.md` files; never rewrite whole docs.
- Every phase: update CHANGELOG.md + MEMORY.md.
- No duplicate content across docs — reference (ARCHITECTURE/RULES/PHASES) rather than repeat.
