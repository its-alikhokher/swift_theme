# Swift Theme → GoldElite — Performance Guide

Performance architecture (S15). Blueprint: ARCHITECTURE.md §1-S15.

## Budgets (targets)

| Metric | Target |
|---|---|
| GoldElite core JS (`ge.bundle.js`) | < 80 KB gz |
| Per-system chunk (`ge-<system>`) | < 30 KB gz |
| GoldElite CSS above-the-fold | < 20 KB gz |
| Extra DOM nodes added to Frappe views | < 5% overhead |
| Observers active (total) | ≤ 4 concurrent |
| Main-thread long tasks (dev perf layer on) | < 200 ms |

Budgets are soft (warn in CI), never hard-fail.

## Boot impact

- Core = boot + S7 + S12 + S14 only.
- Every other system: `import()` dynamic chunk + CSS chunk injected by `GE.flags` asset gate.
- Anti-FOUC: minimal inline critical CSS (tokens only) injected before first paint; all else deferred.
- Boot does NOT block Frappe's own boot; GoldElite initializes on `page_change` idle.

## Asset delivery (S14 gate)

- Server (`extend_bootinfo`) sends only enabled flags → client gate requests only those
  chunks. Disabled feature = zero bytes.
- `replace-chrome` / `window-management` etc. never load unless enabled.

## DOM discipline

- One MutationObserver per concern (theme, sidebar active-state), torn down on `page_change` (R6).
- Decorators run in a single pass; no per-row observers (event delegation).
- CSS containment: `content-visibility:auto` on `.list-row`, widget cards, timeline items
  (moved from `swift-perf.css` into S15 + S3 skins).

## Rendering

- Transitions on `transform`/`opacity` only (S6 tokens); GPU-friendly, no layout thrash.
- No forced reflow in animation driver; rAF batching.
- Charts/table rendering delegated to Frappe (unchanged).

## Metrics & developer mode

- `GE.perf.metrics()`: boot time, interactive, CLS, long-task count, observer count, DOM delta.
- `developer-mode` flag exposes a GE perf panel (S12).
- CI: Lighthouse-style budgets on representative pages (list + form + home).

## Anti-patterns (forbidden)

- jQuery-heavy selectors in hot paths; `:has()` overuse; per-row React/Vue; infinite observers.
- Loading full systems when flags are off; hardcoded asset lists (must go through gate).
