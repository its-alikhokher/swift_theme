"""Colour maths shared by the theme generator and the runtime.

Kept in one place so a preset stylesheet built at development time and a custom
palette derived in the browser cannot drift apart.
"""

import math


def rgb(value):
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(channels):
    # floor(x + 0.5), not round(). Python's round() is banker's rounding, so
    # round(14.5) is 14 while JavaScript's Math.round(14.5) is 15. The same
    # maths runs in swift-boot.js, and that half-unit disagreement showed up as
    # a one-step colour difference on roughly one blend in a hundred.
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, int(math.floor(c + 0.5)))) for c in channels
    )


def mix(base, tint, amount):
    """Blend `amount` of `tint` into `base`. amount 0 = base, 1 = tint."""
    a, b = rgb(base), rgb(tint)
    return to_hex(tuple(a[i] * (1 - amount) + b[i] * amount for i in range(3)))


def alpha(value, a):
    r, g, b = rgb(value)
    return f"rgba({r}, {g}, {b}, {a})"


def luminance(value):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb(value)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


INK = "#0b0d12"
PAPER = "#ffffff"


def readable_on(value):
    """Black or white, whichever actually contrasts better on `value`.

    A luminance threshold is not good enough for mid-tone colours: gold
    (#e0a422) sits at 0.43, so a 0.45 cut-off picked white — which reads at
    2.2:1 and is unreadable. Comparing the two contrast ratios picks dark
    there instead, at 8.7:1.

    Mirrored in swift-boot.js for custom colours; keep the two in step.
    """
    return INK if contrast(value, INK) >= contrast(value, PAPER) else PAPER


# Custom Colors hands us two hexes and nothing else. A full palette needs the
# same eleven roles a preset defines, and two things a hex cannot tell us:
#
#   mode      light or dark desk — hardcoded to dark before this existed
#   strength  Subtle, colour lives in the accents; Bold, cards take the tone
#
# Mirrored in swift-boot.js so the Settings preview can react without a round
# trip. A test runs both and compares, so the two cannot drift.
NEAR_BLACK = "#070910"
NEAR_WHITE = "#ffffff"


def ensure_readable(value, target=4.5, steps=24):
    """Nudge `value` until black or white clears `target` against it.

    A user may pick any colour, and some mid-tones reach neither: #6366f1 tops
    out at 4.47:1 with white, just under AA. Rather than refuse the colour or
    ship unreadable button text, it is darkened (or lightened, if already dark)
    in small steps until it clears. The shift needed is a percent or two, so
    the result is indistinguishable from what was chosen.
    """
    if contrast(value, readable_on(value)) >= target:
        return value

    toward = "#000000" if luminance(value) > 0.18 else "#ffffff"
    candidate = value
    for step in range(1, steps + 1):
        candidate = mix(value, toward, step / 100.0)
        if contrast(candidate, readable_on(candidate)) >= target:
            return candidate
    return candidate


def derive_roles(primary, secondary, mode="Dark", strength="Subtle"):
    dark = (mode or "Dark") == "Dark"
    bold = (strength or "Subtle") == "Bold"
    secondary = secondary or primary

    # Buttons, badges and number cards put text on the accent, so it has to be
    # legible whatever the admin picked.
    primary = ensure_readable(primary)

    if dark:
        canvas = mix(NEAR_BLACK, primary, 0.06)
        # Elevation in a dark UI comes from light: the card sits above the page.
        lifted = mix(canvas, NEAR_WHITE, 0.07)
        surface = ensure_readable(mix(primary, "#0a0c12", 0.55)) if bold else lifted
        surface_alt = mix(canvas, NEAR_WHITE, 0.11)
        ink = mix("#f2f5fa", primary, 0.07)
        border = alpha(ink, 0.14)
    else:
        canvas = mix(NEAR_WHITE, primary, 0.035)
        surface = primary if bold else NEAR_WHITE
        surface_alt = mix(NEAR_WHITE, primary, 0.07)
        ink = mix("#12151a", primary, 0.10)
        border = alpha(ink, 0.13)

    return {
        "canvas": canvas,
        "surface": surface,
        "surface_alt": surface_alt,
        "on_canvas": ink,
        # Per surface, not one global value — a bold card can invert the text.
        "on_surface": readable_on(surface),
        "muted": mix(ink, canvas, 0.45),
        "border": border,
        "primary": primary,
        "secondary": secondary,
        "tint": secondary,
        "on_primary": readable_on(primary),
    }
