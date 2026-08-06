# Swift Theme → GoldElite — Security Guide

Security surface of the GoldElite layer. Blueprint: ARCHITECTURE.md.

## Backend

| Area | Control |
|---|---|
| Endpoints | whitelisted `goldelite.api.*` only; no `@frappe.whitelist(allow_guest)` except public assets |
| CSRF | Frappe's built-in CSRF for all POSTs (never disable) |
| Auth | guest users never receive settings payload (guard in `extend_bootinfo`) |
| Settings | role-checked (System Manager for tenant/global tiers); user tier self-write only |
| Validation | server-side schema validation in `settings_engine/validation.py`; unknown keys rejected |
| Audit | flag/setting changes logged (`feature_flags/audit.py`) — who/what/when |
| Secrets | never in boot payload or localStorage; tokens are presentation-only |

## Client

| Area | Control |
|---|---|
| Rendering | palette/widget/toast HTML escaped by default; only trusted plugin render output allowed |
| Storage | localStorage only as an ephemeral cache of server prefs; server is source of truth; sync + revalidate on boot |
| Sounds/assets | allowlist from `hooks.sounds`; no user-controlled URLs |
| Plugins | third-party plugins = trusted installs (documented trust model); manifest version + `ge` range checked; no code execution beyond the page's own origin |
| CSP | no inline eval; no dynamically generated script URLs; bundled assets only |
| XSS | all `GE.ui.component` rendering escapes text; plugin providers return data, GE renders |

## Feature-flag security

- `developer-mode` exposes perf/debug data — user-tier flag, no extra data exfiltration (metrics local only).
- Tenant/global flags are admin-controlled; user cannot override tenant-mandated flags.

## Test requirements (see TESTING_GUIDE.md)

- Guest payload leak check; CSRF on all endpoints; XSS fuzz on palette/search inputs;
  flag escalation (user overriding tenant flag) test; audit-log completeness test.
