import os

import frappe
from frappe.model.document import Document

from swift_theme.scripts.colour import derive_roles


# Each preset is a set of roles, not one colour with shades derived from it.
# A single hue applied to every surface is what made every theme read as one
# flat tint. Light and dark follow different rules — see REQUIREMENT.md §2.1:
# in dark, `surface` must be lighter than `canvas`, because elevation there
# comes from light rather than shadow.
#
# Six light and six dark, no two sharing a hue. In the light presets the cards
# stay neutral and the character shows through headers, number cards and the
# sidebar — a screen of saturated cards is tiring to work in all day.
#
# Regenerate the stylesheets after editing:
#     python3 swift_theme/scripts/generate_theme_css.py
PREMIUM_THEMES = {
    "Iron Man": {
        "slug": "iron-man",
        "mode": "light",
        "backdrop": "iron-man",
        "roles": {
            "canvas": "#f7f3f1",
            "surface": "#ffffff",
            "surface_alt": "#fbf4f4",
            "on_canvas": "#241413",
            "on_surface": "#241413",
            "muted": "#837877",
            "border": "rgba(36, 20, 19, 0.13)",
            "primary": "#b3232a",
            "secondary": "#d99a2b",
            "tint": "#e04b52",
            "on_primary": "#ffffff",
        },
    },
    "Captain America": {
        "slug": "captain-america",
        "mode": "light",
        "backdrop": "captain-america",
        "roles": {
            "canvas": "#f2f5fa",
            "surface": "#ffffff",
            "surface_alt": "#f4f6fd",
            "on_canvas": "#0f1b2e",
            "on_surface": "#0f1b2e",
            "muted": "#757d8a",
            "border": "rgba(15, 27, 46, 0.13)",
            "primary": "#1d4ed8",
            "secondary": "#c0392b",
            "tint": "#60a5fa",
            "on_primary": "#ffffff",
        },
    },
    "Doctor Strange": {
        "slug": "doctor-strange",
        "mode": "light",
        "backdrop": "doctor-strange",
        "roles": {
            "canvas": "#f0f6f5",
            "surface": "#ffffff",
            "surface_alt": "#f3f8f8",
            "on_canvas": "#0c211f",
            "on_surface": "#0c211f",
            "muted": "#73817f",
            "border": "rgba(12, 33, 31, 0.13)",
            "primary": "#0f766e",
            "secondary": "#b91c1c",
            "tint": "#2dd4bf",
            "on_primary": "#ffffff",
        },
    },
    "Star-Lord": {
        "slug": "star-lord",
        "mode": "light",
        "backdrop": "star-lord",
        "roles": {
            "canvas": "#faf5ef",
            "surface": "#ffffff",
            "surface_alt": "#fcf6f3",
            "on_canvas": "#26160c",
            "on_surface": "#26160c",
            "muted": "#857a72",
            "border": "rgba(38, 22, 12, 0.13)",
            "primary": "#c2410c",
            "secondary": "#0d9488",
            "tint": "#fb923c",
            "on_primary": "#ffffff",
        },
    },
    "Vision": {
        "slug": "vision",
        "mode": "light",
        "backdrop": "vision",
        "roles": {
            "canvas": "#fbf7ee",
            "surface": "#ffffff",
            "surface_alt": "#faf7f3",
            "on_canvas": "#231a09",
            "on_surface": "#231a09",
            "muted": "#847d70",
            "border": "rgba(35, 26, 9, 0.13)",
            "primary": "#a16207",
            "secondary": "#be185d",
            "tint": "#facc15",
            "on_primary": "#ffffff",
        },
    },
    "Scarlet Witch": {
        "slug": "scarlet-witch",
        "mode": "light",
        "backdrop": "scarlet-witch",
        "roles": {
            "canvas": "#fdf3f5",
            "surface": "#ffffff",
            "surface_alt": "#fcf3f5",
            "on_canvas": "#251016",
            "on_surface": "#251016",
            "muted": "#86767a",
            "border": "rgba(37, 16, 22, 0.13)",
            "primary": "#be123c",
            "secondary": "#7f1d1d",
            "tint": "#fb7185",
            "on_primary": "#ffffff",
        },
    },
    "Black Panther": {
        "slug": "black-panther",
        "mode": "dark",
        "backdrop": "black-panther",
        "roles": {
            "canvas": "#0a0a10",
            "surface": "#1b1b21",
            "surface_alt": "#27272d",
            "on_canvas": "#ecebf5",
            "on_surface": "#ecebf5",
            "muted": "#8d8c95",
            "border": "rgba(236, 235, 245, 0.14)",
            "primary": "#8b5cf6",
            "secondary": "#c4b5fd",
            "tint": "#a78bfa",
            "on_primary": "#0b0d12",
        },
    },
    "Loki": {
        "slug": "loki",
        "mode": "dark",
        "backdrop": "loki",
        "roles": {
            "canvas": "#07130f",
            "surface": "#182420",
            "surface_alt": "#252f2c",
            "on_canvas": "#e6f4ee",
            "on_surface": "#e6f4ee",
            "muted": "#889690",
            "border": "rgba(230, 244, 238, 0.14)",
            "primary": "#10b981",
            "secondary": "#d4af37",
            "tint": "#34d399",
            "on_primary": "#0b0d12",
        },
    },
    "Hulk": {
        "slug": "hulk",
        "mode": "dark",
        "backdrop": "hulk",
        "roles": {
            "canvas": "#0b1206",
            "surface": "#1c2317",
            "surface_alt": "#282e24",
            "on_canvas": "#eef6e4",
            "on_surface": "#eef6e4",
            "muted": "#8f9687",
            "border": "rgba(238, 246, 228, 0.14)",
            "primary": "#65a30d",
            "secondary": "#7c3aed",
            "tint": "#a3e635",
            "on_primary": "#0b0d12",
        },
    },
    "Thanos": {
        "slug": "thanos",
        "mode": "dark",
        "backdrop": "thanos",
        "roles": {
            "canvas": "#120c17",
            "surface": "#231d27",
            "surface_alt": "#2e2933",
            "on_canvas": "#f4eefa",
            "on_surface": "#f4eefa",
            "muted": "#958f9b",
            "border": "rgba(244, 238, 250, 0.14)",
            "primary": "#d4a017",
            "secondary": "#9333ea",
            "tint": "#facc15",
            "on_primary": "#0b0d12",
        },
    },
    "Venom": {
        "slug": "venom",
        "mode": "dark",
        "backdrop": "venom",
        "roles": {
            "canvas": "#08080a",
            "surface": "#19191b",
            "surface_alt": "#262627",
            "on_canvas": "#e8e9ec",
            "on_surface": "#e8e9ec",
            "muted": "#8a8b8d",
            "border": "rgba(232, 233, 236, 0.14)",
            "primary": "#d1d5db",
            "secondary": "#6b7280",
            "tint": "#f3f4f6",
            "on_primary": "#0b0d12",
        },
    },
    "Winter Soldier": {
        "slug": "winter-soldier",
        "mode": "dark",
        "backdrop": "winter-soldier",
        "roles": {
            "canvas": "#0b0f14",
            "surface": "#1c2024",
            "surface_alt": "#282c30",
            "on_canvas": "#e6edf5",
            "on_surface": "#e6edf5",
            "muted": "#8a9097",
            "border": "rgba(230, 237, 245, 0.14)",
            "primary": "#3b82f6",
            "secondary": "#94a3b8",
            "tint": "#7dd3fc",
            "on_primary": "#0b0d12",
        },
    },
}

PRESET_SLUGS = {name: data["slug"] for name, data in PREMIUM_THEMES.items()}
DEFAULT_PRESET = "Iron Man"


def roles_to_colors(r):
    """The flat colour shape the login page and its template consume.

    Roles are the source of truth; this is only a view over them, so a preset
    and a derived custom palette reach the client in one shape.
    """
    return {
        "primary": r["primary"],
        "secondary": r["secondary"],
        "accent": r["tint"],
        "bg_body": r["canvas"],
        "bg_card": r["surface"],
        "text_main": r["on_surface"],
        "text_muted": r["muted"],
        "bg1": r["canvas"],
        "bg2": r["surface"],
    }


def theme_colors(name):
    data = PREMIUM_THEMES.get(name) or PREMIUM_THEMES[DEFAULT_PRESET]
    return roles_to_colors(data["roles"])


def preset_stylesheet(slug):
    """URL of the stylesheet for one preset, or None if it isn't shipped."""
    if not slug:
        return None
    if not os.path.exists(frappe.get_app_path("swift_theme", "public", "css", "themes", f"{slug}.css")):
        return None
    return f"/assets/swift_theme/css/themes/{slug}.css"


class SwiftThemeSettings(Document):
    def validate(self):
        if self.color_mode == "Custom Colors":
            if not self.primary_color or not self.secondary_color:
                frappe.throw(
                    frappe._(
                        "Both Primary Color and Secondary Color are required "
                        "when using Custom Colors."
                    )
                )
        elif not self.active_preset:
            self.active_preset = DEFAULT_PRESET

        self._validate_volume()
        self._validate_sound_events()
        self._guard_custom_code()

    def _validate_volume(self):
        if self.volume_level is None:
            return
        if not 0 <= int(self.volume_level) <= 100:
            frappe.throw(frappe._("Volume Level must be between 0 and 100."))

    def _validate_sound_events(self):
        """Duplicate keys silently shadow each other — the first row wins."""
        seen = set()
        for row in self.sound_events or []:
            if not row.event_key:
                continue
            if row.event_key in seen:
                frappe.throw(
                    frappe._("Duplicate sound event {0} in row {1}.").format(
                        frappe.bold(row.event_key), row.idx
                    )
                )
            seen.add(row.event_key)

    def _guard_custom_code(self):
        """Custom JS runs on every desk page for every user.

        That is effectively a site-wide script injection point, so restrict
        edits to Administrator rather than any System Manager.
        """
        if self.is_new() or frappe.session.user == "Administrator":
            return
        if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
            return

        before = self.get_doc_before_save()
        if before is None:
            return

        for field in ("custom_js", "custom_css"):
            if (before.get(field) or "") != (self.get(field) or ""):
                frappe.throw(
                    frappe._("Only Administrator can change {0}.").format(
                        frappe.bold(self.meta.get_label(field))
                    ),
                    frappe.PermissionError,
                )

    COLOR_FIELDS = ("color_mode", "active_preset", "primary_color", "secondary_color")

    def on_update(self):
        self._release_user_overrides()

        # Document.save() already invalidates this doc's own cached copy. What
        # still needs clearing is every user's cached bootinfo, since these
        # preferences are embedded in it — but only that. The previous
        # frappe.clear_cache() flushed the entire site cache (roles, defaults,
        # permissions, metadata) on every theme save.
        frappe.clear_cache(doctype=self.doctype)
        frappe.cache.delete_key("bootinfo")
        frappe.publish_realtime("swift_theme_updated", {}, after_commit=True)

    def _release_user_overrides(self):
        """Make a changed site colour actually take effect for everyone.

        Picking a theme from the navbar switcher stores swift_preset on the
        User. That override outranks this doctype, so once someone had used the
        switcher, changing the colour here did nothing for them and there was
        nothing on screen explaining why. When the site colour actually changes,
        stand those overrides down so the new choice applies; users are free to
        pick their own again afterwards.
        """
        if self.is_new():
            return
        if not any(self.has_value_changed(f) for f in self.COLOR_FIELDS):
            return

        overridden = set()
        for field in ("swift_preset", "swift_primary", "swift_secondary"):
            overridden.update(
                frappe.get_all("User", filters={field: ["is", "set"]}, pluck="name")
            )
        if not overridden:
            return

        for user in overridden:
            frappe.db.set_value(
                "User",
                user,
                {"swift_preset": None, "swift_primary": None, "swift_secondary": None},
                update_modified=False,
            )
            frappe.clear_cache(user=user)

        frappe.msgprint(
            frappe._("Applied to {0} user(s) who had picked their own theme.").format(
                len(overridden)
            ),
            alert=True,
            indicator="green",
        )


@frappe.whitelist(allow_guest=True)
def get_active_theme_config():
    """Returns JSON with colors/mode based on current settings selection.

    Guest-accessible because the login page renders before a session exists.
    Only presentation values are exposed here — never settings that could leak
    configuration to anonymous visitors.
    """
    settings = frappe.get_cached_doc("Swift Theme Settings")

    config = {
        "color_mode": settings.color_mode,
        "sidebar_variant": settings.sidebar_variant,
        "pin_behavior": settings.pin_behavior,
        "enable_sounds": int(settings.enable_sounds or 0),
        "volume_level": settings.volume_level or 50,
        "custom_login_text": settings.login_tagline or "",
    }

    if settings.color_mode == "Custom Colors":
        # The same derivation the desk uses. This used to pair the brand pair
        # with a hardcoded navy canvas, so the login page and the desk showed
        # two different themes for one setting.
        mode = settings.custom_mode or "Dark"
        roles = derive_roles(
            settings.primary_color or "#0b84f3",
            settings.secondary_color or "#0056b3",
            mode,
            settings.custom_strength or "Subtle",
        )
        colors = roles_to_colors(roles)
        config["preset"] = None
        config["preset_name"] = None
        config["theme_css"] = None
        config["mode"] = mode.lower()
        config["colors"] = colors
        config["is_dark_mode"] = mode == "Dark"
    else:
        preset_name = settings.active_preset or DEFAULT_PRESET
        theme_data = PREMIUM_THEMES.get(preset_name, PREMIUM_THEMES[DEFAULT_PRESET])
        colors = theme_colors(preset_name)
        config["preset"] = theme_data["slug"]
        config["preset_name"] = preset_name
        config["theme_css"] = preset_stylesheet(theme_data["slug"])
        config["theme"] = theme_data
        config["mode"] = theme_data["mode"]
        config["colors"] = colors
        config["is_dark_mode"] = theme_data["mode"] == "dark"

    # Flattened aliases so clients can read colours without digging into
    # config.colors — the login page relies on these.
    config.update(colors)

    return config


DEFAULT_SOUNDS = {
    "save": "save.mp3",
    "submit": "submit.mp3",
    "cancel": "cancel.mp3",
    "error": "error.mp3",
    "success": "success.mp3",
    "delete": "delete.mp3",
    "notification": "notification.mp3",
    "click": "click.mp3",
    "login": "login.mp3",
}


def _bundled_sound(event_name):
    """Path to a bundled sound, but only if the file is actually shipped.

    The app ships no audio by default, so returning a path unconditionally
    would make every client request a 404. Resolving against disk means these
    light up automatically if sound files are later added to public/sounds/.
    """
    filename = DEFAULT_SOUNDS.get(event_name)
    if not filename:
        return None
    if not os.path.exists(frappe.get_app_path("swift_theme", "public", "sounds", filename)):
        return None
    return f"/assets/swift_theme/sounds/{filename}"


@frappe.whitelist(allow_guest=True)
def play_sound(event_name):
    """Returns the sound file and volume configured for the given event.

    Returns sound_file=None when nothing is configured for the event; the
    client then stays silent rather than requesting a file that isn't there.
    """
    settings = frappe.get_cached_doc("Swift Theme Settings")

    if not settings.enable_sounds:
        return {"enabled": False, "sound_file": None, "volume": 0, "event": event_name}

    # Clamp so a stray value in Settings can't produce an invalid HTML volume.
    volume = min(max(int(settings.volume_level or 50), 0), 100) / 100.0

    # An uploaded file for this event wins over the bundled default.
    sound_file = None
    for event in settings.sound_events or []:
        if event.event_key == event_name and event.sound_file:
            sound_file = event.sound_file
            break

    if not sound_file:
        sound_file = _bundled_sound(event_name)

    return {
        "enabled": True,
        "sound_file": sound_file,
        "volume": volume,
        "event": event_name,
    }


@frappe.whitelist()
def get_premium_themes():
    """Returns the catalog of luxury premium themes available in Swift Theme"""
    themes_list = []
    for name, data in PREMIUM_THEMES.items():
        themes_list.append({
            "name": name,
            "value": data["slug"],
            "mode": data["mode"],
            "colors": theme_colors(name),
        })
    return {"themes": themes_list}


@frappe.whitelist()
def apply_theme(theme_name):
    """Applies a specific premium theme for the current user session"""
    if theme_name not in PREMIUM_THEMES:
        frappe.throw(frappe._("Theme not found"))

    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw(frappe._("Login required"), frappe.PermissionError)

    selected_theme = PREMIUM_THEMES[theme_name]
    mode = selected_theme.get("mode", "light")

    frappe.db.set_value(
        "User",
        user,
        {
            # swift_preset stores the premium preset name; both this and
            # desk_theme are created/validated by install._ensure_user_fields.
            "swift_preset": theme_name,
            # desk_theme is a core Select — its options are capitalised.
            "desk_theme": mode.capitalize(),
        },
    )

    frappe.clear_cache(user=user)

    return {
        "success": True,
        "theme": selected_theme,
        "mode": mode,
    }
