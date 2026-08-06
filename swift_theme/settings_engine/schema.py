"""Canonical settings schema for Swift Theme (GoldElite).

Single authoritative schema. Legacy (v1) fields are declared here as
deprecated with their mapping to canonical values. No subsystem should
read the DocType directly — use swift_theme.settings_engine.adapter.
"""

ACCENTS = ["indigo", "violet", "blue", "sky", "teal", "emerald", "amber", "rose", "pink", "slate"]
THEMES = ["", "emerald", "sapphire", "obsidian", "midnight", "aurora", "graphite", "carbon", "ivory", "porcelain", "rose-gold", "monochrome", "sandstone"]
MODES = ["Follow Frappe", "Force Light", "Force Dark", "Auto (time-based)"]
DENSITIES = ["Compact", "Comfortable", "Cozy"]
RADII = ["Sharp", "Rounded", "Pill"]
FONT_SCALES = ["S", "M", "L", "XL"]
FONT_FAMILIES = ["Inter", "Poppins", "Manrope", "Roboto", "System"]
NAVBAR_VARIANTS = ["Solid", "Glass", "Transparent"]
SIDEBAR_VARIANTS = ["Attached", "Floating", "Icon-only"]
LOGIN_LAYOUTS = ["Split", "Centered", "Minimal"]

ACCENT_LABELS = {
    "indigo": "Indigo", "violet": "Violet", "blue": "Blue", "sky": "Sky",
    "teal": "Teal", "emerald": "Emerald", "amber": "Amber", "rose": "Rose",
    "pink": "Pink", "slate": "Slate",
}

THEME_LABELS = {
    "": "None (use accent + Frappe mode)",
    "emerald": "Emerald", "sapphire": "Sapphire", "obsidian": "Obsidian",
    "midnight": "Midnight", "aurora": "Aurora", "graphite": "Graphite",
    "carbon": "Carbon", "ivory": "Ivory", "porcelain": "Porcelain",
    "rose-gold": "Rose Gold", "monochrome": "Monochrome", "sandstone": "Sandstone",
}

# Canonical schema version. Bumped when the field set or value domains change.
SCHEMA_VERSION = 2

#: Catalog payload exposed to clients (kept for backward compatibility with
#: swift-boot.js / swift-website.js which expect ``accents`` and ``themes``).
def accent_catalog():
    return [{"key": key, "label": ACCENT_LABELS[key]} for key in ACCENTS]


def theme_catalog():
    tags = {
        "emerald": "Dark · SaaS premium green",
        "sapphire": "Dark · Enterprise banking blue",
        "obsidian": "Dark · Developer luxury",
        "midnight": "Dark · Yacht-club navy",
        "aurora": "Dark · Glassy magic",
        "graphite": "Dark · Editorial charcoal",
        "carbon": "Dark · Terminal neon",
        "ivory": "Light · Museum-quality luxury",
        "porcelain": "Light · Warm editorial",
        "rose-gold": "Light · Fashion pearl",
        "monochrome": "Light · Zero color noise",
        "sandstone": "Light · Muji calm",
    }
    return [{"key": key, "label": THEME_LABELS[key], "tag": tags.get(key, "")} for key in THEMES]


# ---------------------------------------------------------------------------
# Canonical field registry
# ---------------------------------------------------------------------------
# Each spec:
#   type    - Frappe-style fieldtype used for validation (Select/Check/Int/
#             Data/Text/Color/Time)
#   options - list of allowed values for Select (may include "")
#   default - canonical default (used for fresh installs and fallback)
#   group   - logical grouping (theme/features/brand/login/auto_dark/
#             injection/print/system)
#   description - short human description

CANONICAL_FIELDS = {
    # --- theme ---
    "default_accent": {
        "type": "Select", "options": ACCENTS, "optional": True, "default": "indigo",
        "group": "theme", "label": "Default Accent", "description": "Default accent color for all users",
    },
    "default_theme": {
        "type": "Select", "options": THEMES, "optional": True, "default": "",
        "group": "theme", "label": "Default Full Theme", "description": "Default full theme (overrides accent)",
    },
    "default_density": {
        "type": "Select", "options": DENSITIES, "default": "Comfortable",
        "group": "theme", "label": "Default Density", "description": "Default UI density",
    },
    "default_radius": {
        "type": "Select", "options": RADII, "default": "Rounded",
        "group": "theme", "label": "Default Shape", "description": "Default corner radius",
    },
    "default_font_scale": {
        "type": "Select", "options": FONT_SCALES, "default": "M",
        "group": "theme", "label": "Default Font Scale", "description": "Default font scale",
    },
    "default_font_family": {
        "type": "Select", "options": FONT_FAMILIES, "default": "Inter",
        "group": "theme", "label": "Default Font Family", "description": "Default font family",
    },
    "navbar_variant": {
        "type": "Select", "options": NAVBAR_VARIANTS, "default": "Solid",
        "group": "theme", "label": "Navbar Variant", "description": "Navbar style",
    },
    "sidebar_variant": {
        "type": "Select", "options": SIDEBAR_VARIANTS, "default": "Attached",
        "group": "theme", "label": "Sidebar Variant", "description": "Sidebar style",
        # v1 stored "Minimal"; canonical domain uses "Icon-only".
        "legacy_value_map": {"Minimal": "Icon-only"},
    },
    "brand_hex_override": {
        "type": "Color", "optional": True, "default": "",
        "group": "theme", "label": "Brand Hex Override", "description": "Custom accent color (hex)",
    },

    # --- features ---
    "enable_switcher": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Switcher",
        "description": "Show the theme switcher",
    },
    "enable_command_palette": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Command Palette",
        "description": "Enable the command palette",
    },
    "enable_focus_mode": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Focus Mode",
        "description": "Enable focus/reading modes",
    },
    "enable_perf_mode": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Performance Mode",
        "description": "Enable performance optimizations",
    },
    "enable_styled_scrollbar": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Styled Scrollbar",
        "description": "Enable styled scrollbars",
    },
    "enable_toast_theming": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Toast Theming",
        "description": "Theme Frappe toasts",
    },
    "enable_print_theming": {
        "type": "Check", "default": 1, "group": "features", "label": "Enable Print Theming",
        "description": "Theme print formats",
    },

    # --- brand ---
    "brand_name": {
        "type": "Data", "default": "", "group": "brand", "label": "Brand Name",
        "description": "Overrides the Frappe product name",
    },
    "brand_logo": {
        "type": "Data", "default": "", "group": "brand", "label": "Brand Logo (light)",
        "description": "Logo used in light mode",
    },
    "brand_logo_dark": {
        "type": "Data", "default": "", "group": "brand", "label": "Brand Logo (dark)",
        "description": "Logo used in dark mode",
    },
    "brand_favicon": {
        "type": "Data", "default": "", "group": "brand", "label": "Brand Favicon",
        "description": "Favicon URL",
    },

    # --- login ---
    "login_layout": {
        "type": "Select", "options": LOGIN_LAYOUTS, "default": "Split",
        "group": "login", "label": "Login Layout", "description": "Login page layout",
    },
    "login_bg_image": {
        "type": "Data", "default": "", "group": "login", "label": "Login Background Image",
        "description": "Background image for the login page",
    },
    "login_tagline": {
        "type": "Data", "default": "", "group": "login", "label": "Login Tagline",
        "description": "Tagline shown on the login page",
    },
    "login_show_signup": {
        "type": "Check", "default": 0, "group": "login", "label": "Show Signup Link",
        "description": "Show the signup link on login",
    },

    # --- auto dark ---
    "enable_auto_dark": {
        "type": "Check", "default": 0, "group": "auto_dark", "label": "Enable Auto Dark",
        "description": "Switch Light/Dark by time of day",
    },
    "auto_dark_start": {
        "type": "Time", "default": "19:00:00", "group": "auto_dark", "label": "Auto Dark Start",
        "description": "Dark mode starts at",
    },
    "auto_dark_end": {
        "type": "Time", "default": "07:00:00", "group": "auto_dark", "label": "Auto Dark End",
        "description": "Dark mode ends at",
    },

    # --- injection ---
    "custom_css": {
        "type": "Text", "default": "", "group": "injection", "label": "Custom CSS",
        "description": "Injected into the desk on boot",
    },
    "custom_js": {
        "type": "Text", "default": "", "group": "injection", "label": "Custom JS",
        "description": "Injected into the desk on boot",
    },

    # --- print ---
    "print_font_family": {
        "type": "Select", "options": FONT_FAMILIES, "default": "Inter",
        "group": "print", "label": "Print Font Family", "description": "Font used in print formats",
    },

    # --- system ---
    "settings_schema_version": {
        "type": "Int", "default": SCHEMA_VERSION, "group": "system", "label": "Settings Schema Version",
        "description": "Canonical schema version of this document",
    },
}

# ---------------------------------------------------------------------------
# Legacy (v1) field registry
# ---------------------------------------------------------------------------
# v1 fields remain stored (never removed), but are no longer read by any
# canonical consumer. Each entry documents its mapping target.
#
# maps_to: canonical field receiving the legacy value (None = no mapping yet).
# value_map: optional literal legacy-value -> canonical-value translation.

LEGACY_FIELDS = {
    "color_mode": {
        "type": "Select", "options": ["Preset Themes", "Custom Gradient"],
        "label": "Color Mode", "maps_to": None,
        "description": "v1 color-mode selector; superseded by canonical theme settings",
    },
    "active_preset": {
        "type": "Select",
        "options": [
            "Swift Blue", "Midnight Pro", "Emerald Luxury", "Rose Gold",
            "Sapphire Elite", "Golden Hour", "Carbon Fiber", "Pearl White",
            "Royal Purple", "Ocean Depth", "Forest Mist", "Crimson Red",
        ],
        "label": "Active Preset", "maps_to": None, "value_map": None,
        "description": "v1 premium theme preset; mapped to canonical theme/accent",
    },
    "gradient_start": {
        "type": "Color", "label": "Gradient Start", "maps_to": "brand_hex_override",
        "description": "v1 custom gradient start; maps to brand hex override",
    },
    "gradient_end": {
        "type": "Color", "label": "Gradient End", "maps_to": None,
        "description": "v1 custom gradient end; no canonical target",
    },
    "enable_sounds": {
        "type": "Check", "label": "Enable Sounds", "maps_to": None,
        "description": "v1 sound toggle; no canonical target yet (S10 notify)",
    },
    "volume_level": {
        "type": "Int", "label": "Volume Level (%)", "maps_to": None,
        "description": "v1 sound volume; no canonical target yet",
    },
    "sound_events": {
        "type": "Table", "label": "Sound Events", "maps_to": None,
        "description": "v1 sound event table; no canonical target yet",
    },
    "pin_behavior": {
        "type": "Select", "options": ["Click to Pin", "Hover to Expand", "Always Expanded"],
        "label": "Pin Behavior", "maps_to": None,
        "description": "v1 sidebar pin behavior; no canonical target yet",
    },
}

# Best-effort mapping of v1 premium presets to canonical theme/accent values.
# Migration applies this only when the canonical target is unset.
PRESET_MAP = {
    "Swift Blue": {"default_theme": "", "default_accent": "blue"},
    "Midnight Pro": {"default_theme": "midnight", "default_accent": "indigo"},
    "Emerald Luxury": {"default_theme": "emerald", "default_accent": "emerald"},
    "Rose Gold": {"default_theme": "rose-gold", "default_accent": "rose"},
    "Sapphire Elite": {"default_theme": "sapphire", "default_accent": "blue"},
    "Golden Hour": {"default_theme": "", "default_accent": "amber"},
    "Carbon Fiber": {"default_theme": "carbon", "default_accent": "slate"},
    "Pearl White": {"default_theme": "ivory", "default_accent": "slate"},
    "Royal Purple": {"default_theme": "", "default_accent": "violet"},
    "Ocean Depth": {"default_theme": "", "default_accent": "sky"},
    "Forest Mist": {"default_theme": "", "default_accent": "emerald"},
    "Crimson Red": {"default_theme": "", "default_accent": "rose"},
}

# ---------------------------------------------------------------------------
# User preference fields (per-user overrides, stored as User custom fields)
# ---------------------------------------------------------------------------
USER_FIELDS = [
    ("swift_follow_frappe", "Check", "Follow Frappe's Theme Mode", None, "1"),
    ("swift_mode", "Select", "Swift Mode Override", "\n".join(MODES), "Follow Frappe"),
    ("swift_accent", "Select", "Swift Accent", "\n".join([""] + ACCENTS), ""),
    ("swift_theme", "Select", "Swift Full Theme (overrides accent)", "\n".join(THEMES), ""),
    ("swift_density", "Select", "Swift Density", "\n".join([""] + DENSITIES), ""),
    ("swift_radius", "Select", "Swift Shape", "\n".join([""] + RADII), ""),
    ("swift_font_scale", "Select", "Swift Font Scale", "\n".join([""] + FONT_SCALES), ""),
    ("swift_font_family", "Select", "Swift Font Family", "\n".join([""] + FONT_FAMILIES), ""),
]

# Reuse canonical specs for validating/sanitizing user overrides.
USER_FIELD_SPECS = {
    "swift_follow_frappe": {"type": "Check", "default": 1},
    "swift_mode": {"type": "Select", "options": MODES, "default": "Follow Frappe"},
    "swift_accent": {"type": "Select", "options": ACCENTS, "optional": True, "default": ""},
    "swift_theme": {"type": "Select", "options": THEMES, "optional": True, "default": ""},
    "swift_density": {"type": "Select", "options": DENSITIES, "optional": True, "default": ""},
    "swift_radius": {"type": "Select", "options": RADII, "optional": True, "default": ""},
    "swift_font_scale": {"type": "Select", "options": FONT_SCALES, "optional": True, "default": ""},
    "swift_font_family": {"type": "Select", "options": FONT_FAMILIES, "optional": True, "default": ""},
}

# Per-user legacy field written by the v1 ``apply_theme`` endpoint.
LEGACY_USER_FIELD = "swift_selected_theme"
LEGACY_USER_FIELD_TARGET = "swift_theme"

_ALL = {}
_ALL.update(CANONICAL_FIELDS)
_ALL.update(LEGACY_FIELDS)


def get(name):
    """Return the spec for a field, or None if unknown."""
    return _ALL.get(name)


def canonical_specs():
    return dict(CANONICAL_FIELDS)


def legacy_specs():
    return dict(LEGACY_FIELDS)


def is_canonical(name):
    return name in CANONICAL_FIELDS


def is_deprecated(name):
    return name in LEGACY_FIELDS


def defaults():
    """Canonical defaults for every canonical field (fill-if-empty target)."""
    return {name: spec.get("default") for name, spec in CANONICAL_FIELDS.items()}


def options_of(spec):
    """Allowed values for a Select spec (empty string allowed when optional)."""
    options = list(spec.get("options") or [])
    if spec.get("optional") and "" not in options:
        options.insert(0, "")
    return options
