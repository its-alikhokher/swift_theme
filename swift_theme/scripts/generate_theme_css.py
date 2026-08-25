"""Generate one stylesheet per preset from its roles.

Run after editing PREMIUM_THEMES:

    python3 swift_theme/scripts/generate_theme_css.py

The palette in swift_theme_settings.py is the single source of truth; these
files are derived, so editing a themes/*.css by hand will be overwritten.
"""

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from colour import PAPER, alpha, contrast, mix, readable_on  # noqa: E402

OUT_DIR = os.path.join(APP, "public", "css", "themes")
SETTINGS = os.path.join(
    APP, "swift_theme", "doctype", "swift_theme_settings", "swift_theme_settings.py"
)


def load_presets():
    """Read the palette without importing frappe.

    The settings module imports frappe at the top, which is not available when
    this runs standalone — so the dict is read out of the source rather than
    imported. It is parsed and evaluated as a literal: PREMIUM_THEMES is pure
    data, so nothing here needs to *run* the file, and `exec` on a slice of
    source (what this used to do) would execute whatever happened to be inside
    it.
    """
    # SETTINGS is a constant built from __file__; no caller-supplied path
    # reaches it.
    with open(SETTINGS) as f:  # nosemgrep: frappe-security-file-traversal
        tree = ast.parse(f.read())

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(getattr(t, "id", None) == "PREMIUM_THEMES" for t in node.targets):
            return ast.literal_eval(node.value)

    raise SystemExit(f"PREMIUM_THEMES not found in {SETTINGS}")



SIDEBAR_DARKEN = 0.16       # how much the panel deepens from top to bottom
SIDEBAR_TARGET = 4.5        # WCAG AA for body text


def sidebar_fill(primary):
    """Panel colours for the brand sidebar, and the text colour to use on them.

    The panel is a gradient, so it is two colours and the text has to clear the
    contrast floor on both. Picking the text against the brand colour alone was
    not enough: on a mid-tone primary — the purple and the blue — neither black
    nor white cleared 4.5:1 across the whole panel, and those two sidebars
    shipped at 3.4:1 and 3.9:1. Legible but styled wrong beats styled right and
    unreadable, so the panel moves to fit the text rather than the reverse.

    White text wants a darker panel and dark text wants a lighter one, so the
    adjustment goes whichever way the chosen text colour needs, a step at a
    time, and stops as soon as both ends clear the floor.
    """
    ink = readable_on(primary)
    toward = "#000000" if ink == PAPER else "#ffffff"

    start = primary
    for _ in range(24):
        end = mix(start, "#000000", SIDEBAR_DARKEN)
        if min(contrast(ink, start), contrast(ink, end)) >= SIDEBAR_TARGET:
            return start, end, ink
        # Nudge the panel away from the text, 6% at a time. Small enough that
        # the brand colour is still recognisably itself when it stops.
        start = mix(start, toward, 0.06)

    return start, mix(start, "#000000", SIDEBAR_DARKEN), ink

def build(name, data):
    r = data["roles"]
    dark = data["mode"] == "dark"
    slug = data["slug"]

    primary, secondary = r["primary"], r["secondary"]
    hover = mix(primary, "#ffffff" if dark else "#000000", 0.15)
    control = mix(r["surface"], primary, 0.04)

    sidebar_start, sidebar_end, sidebar_fg = sidebar_fill(primary)

    return f"""/* Swift Theme — {name}
   Generated from PREMIUM_THEMES["{name}"] by scripts/generate_theme_css.py.
   Do not edit by hand; the palette is the source of truth.

   Loaded on its own — only the selected preset's stylesheet is ever added. */

html[data-swift-preset="{slug}"] {{
  color-scheme: {"dark" if dark else "light"};

  /* Brand pair */
  --swift-primary:      {primary};
  --swift-secondary:    {secondary};
  --swift-primary-soft: {alpha(primary, 0.14)};

  /* Accent aliases — the rest of the app reads these */
  --swift-accent:       {primary};
  --swift-accent-hover: {hover};
  --swift-accent-fg:    {r["on_primary"]};
  --swift-accent-soft:  {alpha(primary, 0.14)};
  --swift-accent-tint:  {r["tint"]};

  /* The brand sidebar paints a gradient from the primary down to a darkened
     version of it, so the panel is two different colours and the text has to
     be legible on both. on_primary is chosen against the primary alone, and on
     two presets that left the lower half at 3.4:1 and 3.9:1 — present, styled
     and unreadable. This is picked against the darker end and checked against
     both, which is why it is a token of its own rather than a reuse. */
  --swift-sidebar-fg:   {sidebar_fg};
  --swift-sidebar-fill-start: {sidebar_start};
  --swift-sidebar-fill-end: {sidebar_end};

  /* Roles */
  --swift-canvas:       {r["canvas"]};
  --swift-surface:      {r["surface"]};
  --swift-surface-alt:  {r["surface_alt"]};
  --swift-on-canvas:    {r["on_canvas"]};
  --swift-on-surface:   {r["on_surface"]};

  /* Mapped onto the variables Frappe itself paints with */
  --bg-color:            {r["canvas"]};
  --fg-color:            {r["surface"]};
  --card-bg:             {r["surface"]};
  --subtle-fg:           {r["surface_alt"]};
  --subtle-accent:       {control};
  --control-bg:          {control};
  --control-bg-on-gray:  {r["surface_alt"]};
  --border-color:        {r["border"]};
  --text-color:          {r["on_surface"]};
  --text-muted:          {r["muted"]};
  --text-light:          {r["muted"]};
  --heading-color:       {r["on_canvas"]};
  --sidebar-bg:          {r["surface_alt"]};
  --navbar-bg:           {alpha(r["surface"], 0.82)};

  /* Fallback wash for when no backdrop is selected */
  --swift-ambient:
    radial-gradient(1200px 600px at 8% -10%, {alpha(primary, 0.16)}, transparent 60%),
    radial-gradient(900px 500px at 100% 110%, {alpha(secondary, 0.12)}, transparent 60%);
}}
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    presets = load_presets()
    problems = []

    for name, data in presets.items():
        r, dark = data["roles"], data["mode"] == "dark"

        # The two rules from REQUIREMENT.md §2.1, checked at build time so a
        # bad palette never reaches a stylesheet.
        if dark and not _lighter(r["surface"], r["canvas"]):
            problems.append(f"{name}: dark preset has a card darker than the canvas")
        ratio = contrast(r["on_surface"], r["surface"])
        if ratio < 4.5:
            problems.append(f"{name}: text on card is {ratio:.1f}:1, below 4.5:1")
        if readable_on(r["primary"]) != r["on_primary"]:
            problems.append(
                f"{name}: on_primary is {r['on_primary']}, "
                f"but {readable_on(r['primary'])} contrasts better on {r['primary']}"
            )

        # OUT_DIR is a constant and the filename is the preset's own slug,
        # not user input.
        out = os.path.join(OUT_DIR, f"{data['slug']}.css")
        with open(out, "w") as f:  # nosemgrep: frappe-security-file-traversal
            f.write(build(name, data))

    if problems:
        print("PALETTE PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1

    print(f"wrote {len(presets)} stylesheets to {OUT_DIR}")
    return 0


def _lighter(a, b):
    from colour import luminance
    return luminance(a) > luminance(b)


if __name__ == "__main__":
    raise SystemExit(main())
