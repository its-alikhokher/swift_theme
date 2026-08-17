import os

import frappe
from frappe.model.document import Document


# Each preset is a set of roles, not one colour with shades derived from it.
# A single hue applied to every surface is what made every theme read as one
# flat tint. Light and dark follow different rules — see REQUIREMENT.md §2.1:
# in dark, `surface` must be lighter than `canvas`, because elevation there
# comes from light rather than shadow.
#
# Regenerate the stylesheets after editing:
#     python3 swift_theme/scripts/generate_theme_css.py
PREMIUM_THEMES = {
    "Swift Blue": {
        "slug": "swift-blue",
        "mode": "light",
        "roles": {
            "canvas": "#f5f7fa",
            "surface": "#ffffff",
            "surface_alt": "#f0f8fe",
            "on_canvas": "#1e293b",
            "on_surface": "#1e293b",
            "muted": "#64748b",
            "border": "rgba(30, 41, 59, 0.12)",
            "primary": "#0b84f3",
            "secondary": "#0056b3",
            "tint": "#3b82f6",
            "on_primary": "#0b0d12",
        },
    },
    "Midnight Pro": {
        "slug": "midnight-pro",
        "mode": "dark",
        "roles": {
            "canvas": "#0f172a",
            "surface": "#1e293b",
            "surface_alt": "#222d46",
            "on_canvas": "#f1f5f9",
            "on_surface": "#f1f5f9",
            "muted": "#94a3b8",
            "border": "rgba(241, 245, 249, 0.16)",
            # Nudged from #6366f1, which put white button text at 4.47:1 —
            # just under WCAG AA. This clears it at 4.79:1.
            "primary": "#5f62e7",
            "secondary": "#4f46e5",
            "tint": "#818cf8",
            "on_primary": "#ffffff",
        },
    },
    "Emerald Luxury": {
        "slug": "emerald-luxury",
        "mode": "dark",
        "roles": {
            "canvas": "#022c22",
            "surface": "#064e3b",
            "surface_alt": "#07543f",
            "on_canvas": "#ecfdf5",
            "on_surface": "#ecfdf5",
            "muted": "#6ee7b7",
            "border": "rgba(236, 253, 245, 0.16)",
            "primary": "#10b981",
            "secondary": "#059669",
            "tint": "#34d399",
            "on_primary": "#0b0d12",
        },
    },
    "Rose Gold": {
        "slug": "rose-gold",
        "mode": "light",
        "roles": {
            "canvas": "#fff1f2",
            "surface": "#ffffff",
            "surface_alt": "#fff6f8",
            "on_canvas": "#881337",
            "on_surface": "#881337",
            "muted": "#be123c",
            "border": "rgba(136, 19, 55, 0.12)",
            "primary": "#fb7185",
            "secondary": "#e11d48",
            "tint": "#fda4af",
            "on_primary": "#0b0d12",
        },
    },
    "Sapphire Elite": {
        "slug": "sapphire-elite",
        "mode": "dark",
        "roles": {
            "canvas": "#172554",
            "surface": "#1e3a8a",
            "surface_alt": "#203e90",
            "on_canvas": "#dbeafe",
            "on_surface": "#dbeafe",
            "muted": "#93c5fd",
            "border": "rgba(219, 234, 254, 0.16)",
            "primary": "#3b82f6",
            "secondary": "#2563eb",
            "tint": "#60a5fa",
            "on_primary": "#0b0d12",
        },
    },
    "Golden Hour": {
        "slug": "golden-hour",
        "mode": "light",
        "roles": {
            "canvas": "#fffbeb",
            "surface": "#ffffff",
            "surface_alt": "#fef9f0",
            "on_canvas": "#78350f",
            "on_surface": "#78350f",
            "muted": "#b45309",
            "border": "rgba(120, 53, 15, 0.12)",
            "primary": "#f59e0b",
            "secondary": "#d97706",
            "tint": "#fbbf24",
            "on_primary": "#0b0d12",
        },
    },
    "Carbon Fiber": {
        "slug": "carbon-fiber",
        "mode": "dark",
        "roles": {
            "canvas": "#111827",
            "surface": "#1f2937",
            "surface_alt": "#26303e",
            "on_canvas": "#f9fafb",
            "on_surface": "#f9fafb",
            "muted": "#9ca3af",
            "border": "rgba(249, 250, 251, 0.16)",
            "primary": "#9ca3af",
            "secondary": "#6b7280",
            "tint": "#d1d5db",
            "on_primary": "#0b0d12",
        },
    },
    "Pearl White": {
        "slug": "pearl-white",
        "mode": "light",
        "roles": {
            "canvas": "#f8fafc",
            "surface": "#ffffff",
            "surface_alt": "#f6f7f8",
            "on_canvas": "#0f172a",
            "on_surface": "#0f172a",
            "muted": "#64748b",
            "border": "rgba(15, 23, 42, 0.12)",
            "primary": "#64748b",
            "secondary": "#475569",
            "tint": "#94a3b8",
            "on_primary": "#ffffff",
        },
    },
    "Royal Purple": {
        "slug": "royal-purple",
        "mode": "dark",
        "roles": {
            "canvas": "#2e1065",
            "surface": "#4c1d95",
            "surface_alt": "#52209b",
            "on_canvas": "#f5f3ff",
            "on_surface": "#f5f3ff",
            "muted": "#d8b4fe",
            "border": "rgba(245, 243, 255, 0.16)",
            "primary": "#a855f7",
            "secondary": "#9333ea",
            "tint": "#c084fc",
            "on_primary": "#0b0d12",
        },
    },
    "Ocean Depth": {
        "slug": "ocean-depth",
        "mode": "dark",
        "roles": {
            "canvas": "#164e63",
            "surface": "#155e75",
            "surface_alt": "#14637b",
            "on_canvas": "#ecfeff",
            "on_surface": "#ecfeff",
            "muted": "#67e8f9",
            "border": "rgba(236, 254, 255, 0.16)",
            "primary": "#06b6d4",
            "secondary": "#0891b2",
            "tint": "#22d3ee",
            "on_primary": "#0b0d12",
        },
    },
    "Forest Mist": {
        "slug": "forest-mist",
        "mode": "light",
        "roles": {
            "canvas": "#f7fee7",
            "surface": "#ffffff",
            "surface_alt": "#f8fcf1",
            "on_canvas": "#365314",
            "on_surface": "#365314",
            "muted": "#84cc16",
            "border": "rgba(54, 83, 20, 0.12)",
            "primary": "#84cc16",
            "secondary": "#65a30d",
            "tint": "#a3e635",
            "on_primary": "#0b0d12",
        },
    },
    "Crimson Red": {
        "slug": "crimson-red",
        "mode": "dark",
        "roles": {
            "canvas": "#450a0a",
            "surface": "#7f1d1d",
            "surface_alt": "#861f1f",
            "on_canvas": "#fef2f2",
            "on_surface": "#fef2f2",
            "muted": "#fca5a5",
            "border": "rgba(254, 242, 242, 0.16)",
            "primary": "#ef4444",
            "secondary": "#dc2626",
            "tint": "#f87171",
            "on_primary": "#0b0d12",
        },
    },
}

PRESET_SLUGS = {name: data["slug"] for name, data in PREMIUM_THEMES.items()}
DEFAULT_PRESET = "Swift Blue"


def theme_colors(name):
    """The flat colour shape the login page and its template consume.

    Roles are the source of truth; this is only a view over them, so the two
    can never disagree.
    """
    data = PREMIUM_THEMES.get(name) or PREMIUM_THEMES[DEFAULT_PRESET]
    r = data["roles"]
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
        primary = settings.primary_color or "#0b84f3"
        secondary = settings.secondary_color or "#0056b3"
        # Custom colours describe the brand, not the page surface, so pair them
        # with a neutral canvas rather than tinting the whole background.
        colors = {
            "primary": primary,
            "secondary": secondary,
            "accent": secondary,
            "bg_body": "#0f172a",
            "bg_card": "#1e293b",
            "text_main": "#f1f5f9",
            "text_muted": "#94a3b8",
            "bg1": "#0f172a",
            "bg2": "#1e293b",
        }
        config["preset"] = None
        config["preset_name"] = None
        config["theme_css"] = None
        config["mode"] = "dark"
        config["colors"] = colors
        config["is_dark_mode"] = True
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
