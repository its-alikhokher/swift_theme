import os

import frappe
from frappe.model.document import Document


PREMIUM_THEMES = {
    "Swift Blue": {
        "value": "swift-blue",
        "mode": "light",
        "colors": {
            "primary": "#0b84f3",
            "secondary": "#0056b3",
            "accent": "#3b82f6",
            "bg_body": "#f5f7fa",
            "bg_card": "#ffffff",
            "text_main": "#1e293b",
            "text_muted": "#64748b"
        }
    },
    "Midnight Pro": {
        "value": "midnight-pro",
        "mode": "dark",
        "colors": {
            "primary": "#6366f1",
            "secondary": "#4f46e5",
            "accent": "#818cf8",
            "bg_body": "#0f172a",
            "bg_card": "#1e293b",
            "text_main": "#f1f5f9",
            "text_muted": "#94a3b8"
        }
    },
    "Emerald Luxury": {
        "value": "emerald-luxury",
        "mode": "dark",
        "colors": {
            "primary": "#10b981",
            "secondary": "#059669",
            "accent": "#34d399",
            "bg_body": "#022c22",
            "bg_card": "#064e3b",
            "text_main": "#ecfdf5",
            "text_muted": "#6ee7b7"
        }
    },
    "Rose Gold": {
        "value": "rose-gold",
        "mode": "light",
        "colors": {
            "primary": "#fb7185",
            "secondary": "#e11d48",
            "accent": "#fda4af",
            "bg_body": "#fff1f2",
            "bg_card": "#ffffff",
            "text_main": "#881337",
            "text_muted": "#be123c"
        }
    },
    "Sapphire Elite": {
        "value": "sapphire-elite",
        "mode": "dark",
        "colors": {
            "primary": "#3b82f6",
            "secondary": "#2563eb",
            "accent": "#60a5fa",
            "bg_body": "#172554",
            "bg_card": "#1e3a8a",
            "text_main": "#dbeafe",
            "text_muted": "#93c5fd"
        }
    },
    "Golden Hour": {
        "value": "golden-hour",
        "mode": "light",
        "colors": {
            "primary": "#f59e0b",
            "secondary": "#d97706",
            "accent": "#fbbf24",
            "bg_body": "#fffbeb",
            "bg_card": "#ffffff",
            "text_main": "#78350f",
            "text_muted": "#b45309"
        }
    },
    "Carbon Fiber": {
        "value": "carbon-fiber",
        "mode": "dark",
        "colors": {
            "primary": "#9ca3af",
            "secondary": "#6b7280",
            "accent": "#d1d5db",
            "bg_body": "#111827",
            "bg_card": "#1f2937",
            "text_main": "#f9fafb",
            "text_muted": "#9ca3af"
        }
    },
    "Pearl White": {
        "value": "pearl-white",
        "mode": "light",
        "colors": {
            "primary": "#64748b",
            "secondary": "#475569",
            "accent": "#94a3b8",
            "bg_body": "#f8fafc",
            "bg_card": "#ffffff",
            "text_main": "#0f172a",
            "text_muted": "#64748b"
        }
    },
    "Royal Purple": {
        "value": "royal-purple",
        "mode": "dark",
        "colors": {
            "primary": "#a855f7",
            "secondary": "#9333ea",
            "accent": "#c084fc",
            "bg_body": "#2e1065",
            "bg_card": "#4c1d95",
            "text_main": "#f5f3ff",
            "text_muted": "#d8b4fe"
        }
    },
    "Ocean Depth": {
        "value": "ocean-depth",
        "mode": "dark",
        "colors": {
            "primary": "#06b6d4",
            "secondary": "#0891b2",
            "accent": "#22d3ee",
            "bg_body": "#164e63",
            "bg_card": "#155e75",
            "text_main": "#ecfeff",
            "text_muted": "#67e8f9"
        }
    },
    "Forest Mist": {
        "value": "forest-mist",
        "mode": "light",
        "colors": {
            "primary": "#84cc16",
            "secondary": "#65a30d",
            "accent": "#a3e635",
            "bg_body": "#f7fee7",
            "bg_card": "#ffffff",
            "text_main": "#365314",
            "text_muted": "#84cc16"
        }
    },
    "Crimson Red": {
        "value": "crimson-red",
        "mode": "dark",
        "colors": {
            "primary": "#ef4444",
            "secondary": "#dc2626",
            "accent": "#f87171",
            "bg_body": "#450a0a",
            "bg_card": "#7f1d1d",
            "text_main": "#fef2f2",
            "text_muted": "#fca5a5"
        }
    }
}


class SwiftThemeSettings(Document):
    def validate(self):
        # Validate Custom Gradient mode requires both colors
        if self.color_mode == "Custom Gradient":
            if not self.gradient_start or not self.gradient_end:
                frappe.throw(
                    "Both Gradient Start and Gradient End colors are required when using Custom Gradient mode."
                )

    def on_update(self):
        frappe.clear_cache()
        frappe.publish_realtime("swift_theme_updated", {}, after_commit=True)


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

    if settings.color_mode == "Custom Gradient":
        colors = {
            "primary": settings.gradient_start or "#0b84f3",
            "secondary": settings.gradient_end or "#0056b3",
            "bg1": settings.gradient_start or "#0f172a",
            "bg2": settings.gradient_end or "#1e293b",
        }
        config["gradient_start"] = settings.gradient_start
        config["gradient_end"] = settings.gradient_end
        config["mode"] = "custom"
        config["colors"] = colors
        # A custom gradient has no inherent brightness; keep the page's default.
        config["is_dark_mode"] = None
    else:
        preset_name = settings.active_preset or "Swift Blue"
        theme_data = PREMIUM_THEMES.get(preset_name, PREMIUM_THEMES["Swift Blue"])
        colors = dict(theme_data["colors"])
        colors.setdefault("bg1", colors.get("bg_body"))
        colors.setdefault("bg2", colors.get("bg_card"))
        config["theme"] = theme_data
        config["mode"] = theme_data["mode"]
        config["colors"] = colors
        config["gradient_start"] = None
        config["gradient_end"] = None
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
            "value": data["value"],
            "mode": data["mode"],
            "colors": data["colors"]
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
