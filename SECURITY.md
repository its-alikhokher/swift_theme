# Security Policy

## Supported versions

| Version | Branch | Supported |
|---|---|---|
| 2.x | `version-16` | Yes |
| 1.x | — | No |

Swift Theme targets Frappe v16. Security fixes land on `version-16`.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub's
[security advisory form](https://github.com/its-alikhokher/swift_theme/security/advisories/new),
or by email to **iamaliraza777@gmail.com**.

Include what you can: the version or commit, the Frappe version, what an
attacker can do with it, and the steps to reproduce. A proof of concept is
welcome but not required.

You can expect an acknowledgement within a few days. I will tell you whether it
is being fixed, and let you know when the fix ships so you can confirm it. If
you would like credit in the release notes, say so and I will include it.

## Scope

This app is a theming layer. The parts worth looking at hardest:

- The whitelisted endpoints in `swift_theme/api/boot.py` and
  `swift_theme/swift_theme/doctype/swift_theme_settings/swift_theme_settings.py`.
  Three allow guest access, because the login page renders before a session
  exists — those return only presentation values and are the ones most worth
  checking for leakage.
- Changing the theme is restricted to Administrator and System Manager, and
  that is enforced on the server rather than only hidden in the UI. Any path
  that writes a theme preference without going through that check is a bug —
  one such bypass has already been found and fixed.
- The login page posts to Frappe's own `/api/method/login` and sanitises the
  redirect target. Anything that lets an attacker choose where a login sends
  the user is in scope.

Findings in Frappe itself belong with the
[Frappe security team](https://github.com/frappe/frappe/security/policy).
