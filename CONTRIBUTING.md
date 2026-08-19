# Contributing

Thanks for taking an interest. This is a theming layer for Frappe v16, so most
changes are CSS — and CSS in someone else's desk has a few rules worth knowing
before you start.

## Getting set up

You need a working [Frappe bench](https://docs.frappe.io/framework/user/en/installation)
on v16 and a site you do not mind breaking.

```bash
bench get-app https://github.com/its-alikhokher/swift_theme
bench --site your-site install-app swift_theme
bench --site your-site migrate
bench build --app swift_theme
```

`bench migrate` needs redis running. Without it, it exits without doing the work
and without saying so — treat a silent migrate as a failure.

## Branches

- `main` — development
- `version-16` — the release branch for Frappe v16, and what the marketplace
  installs from

Open pull requests against `main`.

## Running the tests

```bash
bench --site your-site set-config allow_tests true
bench --site your-site run-tests --app swift_theme
```

Browser behaviour has its own harness, because a Python suite cannot see "the
server publishes an event and nothing listens" — a bug this app actually had:

```bash
node swift_theme/tests/boot_js_contract.js
```

The upgrade path is rehearsed separately, on a scratch site. `rewind` is
destructive, so keep it off anything real:

```bash
bench --site scratch.local execute swift_theme.scripts.verify_upgrade.rewind
bench --site scratch.local migrate
bench --site scratch.local execute swift_theme.scripts.verify_upgrade.verify
```

## What the tests are for

A theme fails quietly. An undefined CSS variable falls back to a hardcoded blue,
a selector that matches nothing simply does nothing, an event fires with no
listener — none of it raises, and none of it looks broken until you happen to
look at the right screen. Most of the suite exists to make those failures loud.

So when you fix something, add the guard that would have caught it, then break
the fix on purpose and confirm the test fails. A test that passes against the
bug it was written for is worse than no test.

## House rules for the CSS

These are not style preferences — each one is here because breaking it broke
something real. [REQUIREMENT.md](REQUIREMENT.md) has the full list with the
failure each came from.

- **Never `transform`, `filter` or `backdrop-filter` on a desk container.** Each
  makes the element a containing block and a stacking context for its
  descendants. A hover lift on a sidebar row once trapped the notifications
  panel inside it; the same thing on a widget traps the dropdown in its header.
  Use shadow and border for depth.
- **No `content-visibility` or `contain` on desk containers**, for the same
  reason — paint containment clipped the child-table editor until it could not
  be typed into.
- **No hardcoded hues inside a themed rule.** Read `--swift-primary` /
  `--swift-secondary` and the role variables. A literal colour ignores whichever
  preset is active, which defeats the point.
- **Colour Frappe's components; leave their mechanics alone.** Do not re-declare
  its `position`, `z-index`, `overflow` or `pointer-events`.
- **Anything the JS injects needs CSS.** Pin buttons and the sidebar restore
  button both shipped unstyled at some point.

## Adding or changing a preset

The palette in
`swift_theme/swift_theme/doctype/swift_theme_settings/swift_theme_settings.py`
is the single source of truth. After editing it, regenerate the stylesheets:

```bash
python3 swift_theme/scripts/generate_theme_css.py
```

`public/css/themes/*.css` is generated — editing one by hand will be
overwritten, and a test catches a stale file. The generator refuses to write a
palette that fails the 4.5:1 contrast floor, or a dark palette whose cards do
not lift above the canvas.

The colour maths exists in both Python and JavaScript, since the Settings
preview reacts without a round trip. A test runs both over eighty palettes and
compares them value for value, so the two cannot drift apart.

## Pull requests

Say what broke and how you know it is fixed. Screenshots help for anything
visual — there is no way to review a colour change from a diff.
