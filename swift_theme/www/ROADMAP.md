# Swift Theme → GoldElite — Roadmap

Milestones with rough effort. Blueprint: ARCHITECTURE.md. Sequencing: PHASES.md.

| Milestone | Phase | Estimate | Deliverable |
|---|---|---|---|
| M1 Foundation | P0 | 1 wk | GE core boot, settings v1→v2 migration, flags, build scaffold |
| M2 Identity | P1 | 1–2 wk | theme engine, tokens, dark/auto parity |
| M3 Shell | P2 | 2–3 wk | layout + navigation, replace-chrome, sidebar tree, pins |
| M4 Surfaces | P3 | 2–3 wk | component kit, home dashboard, workspace pages |
| M5 Power tools | P4 | 2 wk | palette, global search, shortcut registry, toast centre |
| M6 Desktop | P5 | 3–4 wk | window management (flagged, optional) |
| M7 Hardening | P6 | 1–2 wk | motion, perf budgets, plugin system, upgrade matrix, docs |

Total: ~12–16 wk sequential (fewer with parallel theme/component tracks after M2).

## Dependencies & critical path

M1 → M2 → M3 → M4 → M5 → M6(optional) → M7.
M3 and M4 can parallelize after M2 (components independent of shell).
M6 is a stretch; ship only if M7 budget allows — flagged OFF protects users regardless.

## Gate reviews

| Gate | Criteria |
|---|---|
| Post-M1 | boot < 80 KB gz core; flags toggle live; zero frappe edits |
| Post-M3 | replace-chrome on/off byte-identical behavior outside GoldElite surfaces |
| Post-M5 | palette + shortcuts shown in Frappe help; no double alerts |
| Post-M7 | upgrade matrix green (frappe minor × erpnext minor); perf budgets met |

## Risks on roadmap

- M6 (windows) may slip → does not block v1 (flagged off).
- Frappe v17 during development → contract checks localize impact; upgrade matrix updated.
- Settings migration (M1) blocks everything → do first, keep v1 read shim one release.
