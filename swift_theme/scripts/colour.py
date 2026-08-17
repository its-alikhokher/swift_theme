"""Colour maths shared by the theme generator and the runtime.

Kept in one place so a preset stylesheet built at development time and a custom
palette derived in the browser cannot drift apart.
"""


def rgb(value):
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(channels):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in channels)


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
