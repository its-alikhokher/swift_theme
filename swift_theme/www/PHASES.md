# Swift Theme → GoldElite — Phases

Sequenced implementation plan. Blueprint: ARCHITECTURE.md. Rules: RULES.md.

| Phase | Scope | Systems | Exit criteria | Depends on |
|---|---|---|---|---|
| P0 Foundation | GE namespace, core store, event bus, lifecycle, feature flags, settings engine (v1→v2 migration), boot payload, build/code-split scaffold | S7, S12, S14, S15 (scaffold) | `ge.bundle.js` boots; settings schema migrated; flags gate assets; zero frappe edits | — |
| P1 Theme Engine | tokens, accent/mode/density/radius, fonts, glass, dark, containment | S1, S6 (tokens) | `data-ge-*` drive look; light/dark/auto match Frappe | P0 |
| P2 Layout + Navigation | shell, sidebar tree, navbar, status bar, pins, floating sidebar, responsive | S2, S4 | `replace-chrome` flag renders GoldElite shell; nav tree from boot data | P1 |
| P3 Components + Workspace | UI kit, home dashboard, widget registry, workspace pages | S3, S5 | home + module surfaces rendered by GE widgets; fallback to Frappe via flags | P2 |
| P4 Search + Shortcuts + Notifications | palette, command providers, shortcut registry, toast centre, sounds | S8, S9, S10 | palette searches docs+commands; keys in Ctrl+F1; toast centre live | P3 |
| P5 Windows (flagged) | window frames, detach/dock, geometry persistence | S11 | detach opens 2nd instance in window; OFF default; mini-view fallback | P3 |
| P6 Polish + Perf + Plugins | motion polish, metrics budgets, plugin system finalize, upgrade matrix, docs | S6, S13, S15 | all flags togggable live; perf budgets met; upgrade matrix green; CHANGELOG/MEMORY updated | all |

## Sequencing rationale

- Settings + flags (P0) first because every system reads them.
- Theme (P1) before chrome (P2) so the shell renders correctly on first frame.
- Components (P3) gate workspace; palette/search (P4) reuse S3.
- Windows (P5) is intentionally last + flagged (highest risk, see DECISIONS).
- Plugins (P6) finalize the public API surface after all systems exist.

## Per-phase deliverables

Each phase ships: code under `swift_theme/swift_theme/{public/goldelite,settings_engine,feature_flags}`,
SCSS chunks, contract checks, tests (unit + contract), flags registered in S14, and
CHANGELOG.md + MEMORY.md updates. No phase modifies frappe/erpnext.
