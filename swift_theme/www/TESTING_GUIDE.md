# Swift Theme → GoldElite — Testing Guide

Test strategy for the GoldElite layer. Blueprint: ARCHITECTURE.md.

## Test pyramid

| Layer | Scope | Tooling (framework-agnostic) |
|---|---|---|
| Unit | stores, registries, token math, fuzzy, adapters (pure fns) | js test runner |
| Contract | every Frappe API used — assert presence + shape at boot; failure → feature disabled | boot-time asserts + stubs |
| Integration | systems wired against stubbed Frappe; flag toggles; settings migrate | js integration |
| E2E | real bench: login → home → list → form → save → palette → toast | browser automation |
| A11y | keyboard nav, reduced-motion, contrast on all accents/modes | axe + manual |
| Visual | per accent × mode × density screenshots (login, home, list, form, portal) | screenshot diff |
| Perf | budgets from PERFORMANCE_GUIDE on representative pages | Lighthouse-style |
| Upgrade matrix | frappe minor × erpnext minor combos run contract + E2E | CI matrix |

## Key test cases per area

- **Settings (P0):** v1 data migrates to v2; unknown keys rejected; tenant flag not user-overridable; guest receives no payload.
- **Theme (P1):** `data-theme-mode="dark"` + auto via `prefers-color-scheme` parity; accent contrast AA; density does not shrink controls below a11y minimum.
- **Shell (P2):** replace-chrome on vs off render equivalence outside GE surfaces; nav tree from `workspace_sidebar_item`; fallback to Frappe sidebar on malformed data.
- **Workspace (P3):** widget registry; home fallback to Frappe when `workspace-home` off.
- **Search/Shortcuts (P4):** palette doc+command results; shortcuts appear in Frappe Ctrl+F1; no double alerts (dedupe).
- **Windows (P5):** detach opens 2nd instance; dirty-doc mini-view fallback; geometry persistence round-trip.

## CI gates

| Gate | Fails on |
|---|---|
| Unit + contract | any break |
| Upgrade matrix | contract failure on any supported combo |
| Visual diff | unauthorized change per accent/mode (review-diff, not hard-fail) |
| Perf | hard exceed only (soft warn otherwise) |
| Dist | `bench build --app swift_theme` output out of sync with sources |

## Regression discipline

- Every flag-off path is a first-class test (default behavior must match Frappe).
- Screenshot baselines updated only via reviewed PR.
- Contract stubs kept in `goldelite/tests/` and versioned with the adapter they test.
