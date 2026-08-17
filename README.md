# Swift Theme

A theming layer for Frappe v16. It colours the whole desk — navbar, sidebar,
list, report, kanban, dashboards, forms, child tables, modals and the login
page — from one palette, and stays out of Frappe's way while doing it.

## Colour Mode

The site is coloured one of two ways. There is no third control.

### Theme Preset

Twelve presets, six light and six dark, each a hand-tuned palette rather than
one hue tinting everything:

| Light | Dark |
|---|---|
| Iron Man · crimson + gold | Black Panther · violet |
| Captain America · navy + red | Loki · emerald + gold |
| Doctor Strange · teal + crimson | Hulk · lime + purple |
| Star-Lord · burnt orange + teal | Thanos · gold + purple |
| Vision · gold + magenta | Venom · monochrome |
| Scarlet Witch · rose + deep red | Winter Soldier · steel blue |

Each ships its own stylesheet under `public/css/themes/`, and only the selected
one is ever loaded.

### Custom Colors

Give it a primary and a secondary colour and it works out the rest — canvas,
cards, the text for each surface, muted text, borders, accent states and the
backdrop. Two more choices it cannot read off a hex code:

- **Custom Mode** — Light or Dark
- **Colour Strength** — *Subtle* keeps cards neutral and puts the colour in the
  accents; *Bold* gives the cards the brand tone

If you pick a colour where neither black nor white is quite legible on it, it is
nudged a percent or two until one is.

## How a palette is built

A theme is a set of roles, not a colour with shades derived from it:

| Role | |
|---|---|
| `canvas` | the page |
| `surface` / `surface_alt` | cards, sidebar, table headers |
| `on_canvas` / `on_surface` | text, chosen per surface |
| `muted`, `border` | secondary text, hairlines |
| `primary` / `secondary` / `on_primary` | the brand pair and text on it |

Light and dark follow different rules, because one formula cannot serve both.
In dark, `surface` must be **lighter** than `canvas` — elevation there comes
from light, not shadow. Every palette is checked against that and against a
4.5:1 contrast floor when the stylesheets are built; the generator refuses to
write a file that fails either.

## Backdrops

The desk background can carry one of five treatments — **Aurora**, **Mesh**,
**Grain**, **Facets**, **Silk** — or **None**. Each is built from the active
theme's own two colours, so it works with every preset and with custom colours.
Each preset ships a default; the Backdrop field in Settings overrides it.

No image is shipped for any of this: it is CSS plus one inline SVG for the
grain, so there is nothing extra to download.

## Switching theme

Presets appear inside Frappe's own **Switch Theme** dialog, drawn as the same
preview cards as Light / Dark / Automatic. Custom Colors is a card there too;
its two pickers appear once it is chosen. Restricted to **Administrator** and
**System Manager**, enforced on the server as well as hidden in the UI.

Saving Swift Theme Settings applies immediately in every open desk session.

## Also included

- **Sounds** on desk events, configurable per event. No audio ships, so events
  with no file attached stay silent.
- **Login page** in three layouts (Split, Centered, Minimal), themed from the
  active palette and rendered server-side so it paints correctly on first load.
- **Density, shape, font scale and family**, per user.
- **Focus / reading mode**, a command palette, and sidebar pinning.

## Install

```bash
bench get-app https://github.com/its-alikhokher/swift_theme
bench --site your-site install-app swift_theme
bench --site your-site migrate
bench build --app swift_theme
```

`bench migrate` needs redis running. Without it, it exits without doing the
work and without saying so — treat a silent migrate as a failure.

## Working on it

The palette in
`swift_theme/doctype/swift_theme_settings/swift_theme_settings.py` is the single
source of truth. After editing it, rebuild the stylesheets:

```bash
python3 swift_theme/scripts/generate_theme_css.py
```

`themes/*.css` is generated — editing one by hand will be overwritten, and a
test catches a stale file.

### Tests

```bash
bench --site your-site set-config allow_tests true
bench --site your-site run-tests --app swift_theme
```

Browser behaviour has its own coverage, because a Python suite cannot see
"the server publishes an event and nothing listens" — which is a bug this app
actually had:

```bash
node swift_theme/tests/boot_js_contract.js
```

The colour maths exists in both Python and JavaScript, since the Settings
preview has to react without a round trip. A test runs both over eighty
palettes and compares them value for value, so the two cannot drift.

See [REQUIREMENT.md](REQUIREMENT.md) for what the app is meant to do, including
the constraints that exist because something broke.

## Licence

MIT
