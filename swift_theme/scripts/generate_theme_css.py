"""Generate one stylesheet per preset from its roles.

Run after editing PREMIUM_THEMES:

    python3 swift_theme/scripts/generate_theme_css.py

The palette in swift_theme_settings.py is the single source of truth; these
files are derived, so editing a themes/*.css by hand will be overwritten.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from colour import alpha, contrast, mix, readable_on  # noqa: E402

OUT_DIR = os.path.join(APP, "public", "css", "themes")
SETTINGS = os.path.join(
    APP, "swift_theme", "doctype", "swift_theme_settings", "swift_theme_settings.py"
)


def load_presets():
    """Read the palette without importing frappe."""
    src = open(SETTINGS).read()
    block = src[src.index("PREMIUM_THEMES = {"):src.index("\nPRESET_SLUGS")]
    namespace = {}
    exec(block, namespace)
    return namespace["PREMIUM_THEMES"]


def build(name, data):
    r = data["roles"]
    dark = data["mode"] == "dark"
    slug = data["slug"]

    primary, secondary = r["primary"], r["secondary"]
    hover = mix(primary, "#ffffff" if dark else "#000000", 0.15)
    control = mix(r["surface"], primary, 0.04)

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

        with open(os.path.join(OUT_DIR, f"{data['slug']}.css"), "w") as f:
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
