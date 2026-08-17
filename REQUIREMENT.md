# Swift Theme — Requirements

What the app must do. This is the spec, not a changelog and not a description
of the current code. Where a rule exists because something actually broke, the
reason is given — those lines are requirements, not history.

Status keys: **MUST** required · **SHOULD** wanted, not blocking · **OPEN** undecided

---

## 1. Colour Mode

The site picks **one** of two ways to be coloured. Nothing else.

| Mode | What the admin sets |
|---|---|
| **Theme Preset** | one preset from a named list |
| **Custom Colors** | a primary and a secondary colour |

- **MUST** Settings offers exactly these two modes.
- **MUST** No third colour control anywhere. A single accent, a separate full-theme
  picker and a brand-hex override all existed at once and overlapped; that is
  what this section replaces.

---

## 2. A theme is a palette, not a tint

The core requirement. A theme **MUST NOT** derive every surface from one colour —
that makes the whole screen read as a single wash.

Each theme **MUST** define these roles independently:

| Role | Meaning |
|---|---|
| `canvas` | the page behind everything |
| `surface` | cards, panels |
| `surface_alt` | secondary surfaces, sidebar, table headers |
| `on_canvas` | text on the page |
| `on_surface` | text on a card — computed **per surface**, never one global value |
| `muted` | secondary text |
| `border` | hairlines |
| `primary` / `secondary` | the brand pair |
| `on_primary` | text on an accent fill |

### 2.1 Light and dark follow different rules

**MUST** — the same formula cannot serve both.

| Role | Light | Dark |
|---|---|---|
| canvas | near-white | the deepest tone |
| surface | white, **or** the saturated brand tone | **lighter than the canvas** — in a dark UI elevation comes from light, not shadow |
| text | dark on page; light on a saturated card | light, chosen per surface |
| border | dark at low alpha | light at low alpha |

- **MUST** `on_surface` is computed from the contrast of its own surface. A green
  card takes dark text; a deep red card takes light text.
- **MUST** In dark themes `surface` is lighter than `canvas`. A darker card sinks
  instead of lifting.

### 2.2 Presets

- **MUST** 12 presets, each hand-tuned, not generated from one hue.
- **MUST** Each preset ships its own stylesheet; only the selected one is loaded.
- **MUST** Renaming presets ships a patch mapping old names to new on both
  `Swift Theme Settings.active_preset` and `User.swift_preset`. Without it every
  existing install silently falls back to the default.
- **MUST** Presets are named after Marvel characters, and each palette is drawn
  from that character rather than being a generic hue with a name attached.
  The names are trademarks of Marvel/Disney; the owner has accepted that, which
  only becomes relevant if the app is ever distributed publicly.

  Six light, six dark, chosen so no two share a hue:

  | Preset | Mode | Pair |
  |---|---|---|
  | Iron Man | light | crimson + gold |
  | Captain America | light | navy + red |
  | Doctor Strange | light | crimson + teal |
  | Star-Lord | light | maroon + teal |
  | Vision | light | gold + magenta |
  | Scarlet Witch | light | rose + crimson |
  | Black Panther | dark | violet on near-black |
  | Loki | dark | green + gold |
  | Hulk | dark | green + purple |
  | Thanos | dark | purple + gold |
  | Venom | dark | monochrome |
  | Winter Soldier | dark | steel + gunmetal |

- **MUST** In light presets only the **lead** card carries the brand tone;
  secondary cards stay neutral. A screen where every card is saturated is
  tiring to work in all day, and it leaves nothing to draw the eye.

### 2.3 Custom Colors

- **MUST** Two colours produce a **complete** palette — canvas, surface, per-surface
  text, muted, borders, accent states, backdrop. Not just an accent swap.
- **MUST** The admin also chooses:
  - **mode** — Light or Dark. It cannot be read off a hex code, and is currently
    hardcoded to dark.
  - **strength** — *Subtle* (surfaces neutral, colour in accents) or *Bold*
    (cards take the brand tone).
- **MUST** The login page and the desk resolve colour the same way. Today the
  login page uses a hardcoded navy while the desk uses Frappe's defaults, so the
  two disagree.
- **MUST** Default is **Dark · Subtle**. Custom Colors is dark today, so this is
  the one default that does not change how existing installs look the moment
  they upgrade. The admin can move to Light or Bold whenever they want.

---

## 3. Backdrops

The desk background **SHOULD** be more than a flat fill.

- **MUST** Built from the theme's own primary/secondary. No hardcoded hue, so a
  backdrop works with every preset and with custom colours.
- **MUST** Options: Aurora, Mesh, Grain, Facets, Silk, None.
- **MUST** Each preset carries a default; a Settings field overrides it.
- **MUST** No binary assets. CSS plus inline SVG only — nothing extra to ship, no
  requests.
- **MUST** Animation is transform/opacity only, and stops under performance mode,
  the animation switch, or `prefers-reduced-motion`.

---   

## 4. Applying a theme

- **MUST** Saving Swift Theme Settings applies immediately, in every open desk
  session, with no reload.
- **MUST** A colour change stands down per-user overrides, otherwise anyone who
  once used the switcher never sees an admin's change and has no way to know why.
- **MUST** Switching preset **retargets one** `<link>`. Stylesheets must never
  stack, or the previous palette lingers underneath.
- **MUST** Preferences persist so the next page load paints correctly with no flash.

---

## 5. Theme switcher

- **MUST** Lives inside Frappe's own **Switch Theme** dialog, drawn with the same
  preview cards as Light/Dark/Automatic — one place to change theme, not two.
- **MUST** Custom Colors is a card like any other; its two pickers appear only
  after that card is chosen.
- **MUST** A way back to the site default.
- **MUST** Restricted to **Administrator** and **System Manager**, enforced on the
  server as well as hidden in the UI — the endpoint is reachable directly.

---

## 6. Desk must follow the theme

**MUST** — all of it, in both light and dark:

navbar · sidebar (hover, selected) · list view · report view (datatable) ·
kanban · dashboards (widgets, number cards, charts) · forms · modals ·
child tables · toasts · buttons and links

- **MUST** No CSS may read a variable that no theme and no Frappe stylesheet
  defines. Undefined variables fall back to a hardcoded colour, which is why the
  desk stayed blue whatever theme was picked.
- **MUST** Gradients use **both** colours of the pair. A user who picks two
  colours must see both.
- **MUST** frappe-charts' own variables are repointed at the theme, or the chart
  stays a white slab with near-black labels on every dark theme.

---

## 7. Do not break Frappe

Hard constraints, each from a real failure.

- **MUST NOT** create a stacking context around the desk. Frappe opens a
  child-table row as `position: fixed` at z-index 1021 above a 1020 backdrop;
  `position: relative; z-index: n` on `.layout-main` traps it underneath and the
  row opens invisible.
- **MUST NOT** apply `content-visibility` or `contain: paint/strict/content` to
  any desk container. Paint containment makes that element the containing block
  for `position: fixed` descendants and clips them — the same editor ended up
  mispositioned, capped and clipped, so it could not be typed into.
- **MUST NOT** re-declare Frappe's `position` / `z-index` / `opacity` /
  `pointer-events` / `overflow` on its components. Colour them; leave the
  mechanics alone, or every Frappe upgrade is a fight.
- **MUST** Every element the theme's JS injects has CSS. Pin buttons, the sidebar
  restore button and the whole switcher palette each shipped unstyled.

---

## 8. Login page

- **MUST NOT** ship credentials, autofilled values, or any real account data.
- **MUST** Authenticate against `/api/method/login` with CSRF, real error
  messages, and a sanitised redirect. It previously faked a timeout and showed an
  alert, and because the page overrides `/login`, nobody could sign in.
- **MUST** Endpoints the page calls before login allow guests; guests receive
  presentation values only, never custom CSS/JS.
- **MUST** Themed from the active palette, server-rendered so it paints correctly
  on first load.
- **MUST** Responsive, and legible on light presets.

---

## 9. Sounds

- **MUST** Fire on real desk events (save, submit, cancel, error, success,
  notification), not only where a page happens to call them.
- **MUST** Silent when no file is attached. Never request a file that isn't
  shipped.
- **MUST** A fault in the sound layer can never block the action that triggered
  it — saving a document comes first.
- **MUST** The Settings form says so when sounds are on but nothing is configured.

---

## 10. Quality bar

- **MUST** Behaviour is proved, not asserted. A test that passes against the
  broken code is worse than no test — new guards are mutation-checked by
  reintroducing the defect and confirming the test fails.
- **MUST** Browser behaviour has browser-level coverage. A Python suite cannot
  see "the server publishes an event and nothing listens", which is exactly the
  bug this app had.
- **MUST** Settings options and CSS agree. An option with no rule behind it does
  nothing and looks like a bug.
- **MUST** The installed schema matches the shipped JSON, so a DocType that
  failed to sync is caught rather than silently tested in its stale state.
- **MUST** `bench migrate` needs redis running, or it does nothing and says
  nothing. Treat a silent migrate as a failure.

---

## 11. Out of scope

- No binary assets of any kind — no images, no audio shipped.
- No external requests from the desk or the login page.
- Frappe's own Light/Dark/Automatic switcher stays as it is; the theme adds to
  that dialog, it does not replace it.

---

## Decisions taken

Recorded so they are not re-litigated. Each is cheap to change — a preset name
is one string, the card rule is one CSS rule, the default is one field value.

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | Preset names | Marvel characters, 6 light / 6 dark (§2.2) | Owner's choice; palettes drawn from each character so the names mean something |
| 2 | Light presets: how many cards branded | Lead card only | All-saturated is tiring over a working day and flattens the visual hierarchy |
| 3 | Custom Colors default | Dark · Subtle | Matches how Custom Colors behaves today, so upgrading changes nothing until asked |
