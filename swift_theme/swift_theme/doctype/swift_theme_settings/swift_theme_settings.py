import json
import frappe
from frappe.model.document import Document

from swift_theme.settings_engine import adapter, schema, validation


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
        # Canonical settings validation (centralized in settings_engine).
        errors = validation.validate_doc(self)
        if errors:
            frappe.throw("Invalid settings: " + "; ".join(errors))

        # Legacy (v1) validation retained for the deprecated fields.
        if self.color_mode == "Custom Gradient":
            if not self.gradient_start or not self.gradient_end:
                frappe.throw(
                    "Both Gradient Start and Gradient End colors are required when using Custom Gradient mode."
                )

    def on_update(self):
        frappe.clear_cache()
        frappe.publish_realtime("swift_theme_updated", {}, after_commit=True)


@frappe.whitelist()
def get_active_theme_config():
    """DEPRECATED (v1). Returns JSON with colors/mode based on v1 settings."""
    adapter.warn_deprecated("get_active_theme_config", usage="call")
    settings = frappe.get_single("Swift Theme Settings")
    
    config = {
        "color_mode": settings.color_mode,
        "sidebar_variant": settings.sidebar_variant,
        "pin_behavior": settings.pin_behavior,
        "enable_sounds": settings.enable_sounds,
        "volume_level": settings.volume_level or 50,
    }
    
    if settings.color_mode == "Preset Themes":
        preset_name = settings.active_preset or "Swift Blue"
        theme_data = PREMIUM_THEMES.get(preset_name, PREMIUM_THEMES["Swift Blue"])
        config["theme"] = theme_data
        config["mode"] = theme_data["mode"]
        config["colors"] = theme_data["colors"]
        config["gradient_start"] = None
        config["gradient_end"] = None
    elif settings.color_mode == "Custom Gradient":
        config["gradient_start"] = settings.gradient_start
        config["gradient_end"] = settings.gradient_end
        config["mode"] = "custom"
        config["colors"] = {
            "primary": settings.gradient_start or "#0b84f3",
            "secondary": settings.gradient_end or "#0056b3",
            "bg1": settings.gradient_start or "#0f172a",
            "bg2": settings.gradient_end or "#1e293b",
        }
    
    return config


@frappe.whitelist()
def play_sound(event_name):
    """DEPRECATED (v1). Checks v1 settings and returns a sound for an event."""
    adapter.warn_deprecated("play_sound", usage="call")
    settings = frappe.get_single("Swift Theme Settings")
    
    if not settings.enable_sounds:
        return {"enabled": False, "sound": None, "volume": 0}
    
    volume = (settings.volume_level or 50) / 100.0
    
    # Look for custom sound in sound_events table
    sound_file = None
    if settings.sound_events:
        for event in settings.sound_events:
            if event.event_key == event_name:
                sound_file = event.sound_file
                break
    
    # Default sounds mapping if no custom sound found
    default_sounds = {
        "save": "/assets/swift_theme/sounds/save.mp3",
        "submit": "/assets/swift_theme/sounds/submit.mp3",
        "error": "/assets/swift_theme/sounds/error.mp3",
        "success": "/assets/swift_theme/sounds/success.mp3",
        "delete": "/assets/swift_theme/sounds/delete.mp3",
        "click": "/assets/swift_theme/sounds/click.mp3",
    }
    
    if not sound_file:
        sound_file = default_sounds.get(event_name, default_sounds.get("click"))
    
    return {
        "enabled": True,
        "sound": sound_file,
        "volume": volume,
        "event": event_name
    }


@frappe.whitelist()
def get_premium_themes():
    """DEPRECATED (v1). Returns the catalog of v1 premium themes."""
    adapter.warn_deprecated("get_premium_themes", usage="call")
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
    """DEPRECATED (v1). Applies a v1 premium theme for the current user.

    Legacy ``swift_selected_theme`` is still written (backward compat); the
    canonical ``swift_theme`` override is written too when a mapping exists.
    """
    adapter.warn_deprecated("apply_theme", usage="call")
    if theme_name not in PREMIUM_THEMES:
        frappe.throw("Theme not found")

    selected_theme = PREMIUM_THEMES[theme_name]

    # Set user preference (legacy + canonical when mapped)
    frappe.db.set_value("User", frappe.session.user, "swift_selected_theme", theme_name)
    preset_map = schema.PRESET_MAP.get(theme_name)
    if preset_map:
        canonical_theme = preset_map.get("default_theme")
        if canonical_theme:
            frappe.db.set_value("User", frappe.session.user, "swift_theme", canonical_theme)

    # Auto-set Dark/Light Mode based on theme
    mode = selected_theme.get("mode", "light")
    frappe.db.set_value("User", frappe.session.user, "desk_theme", mode)

    frappe.clear_cache(user=frappe.session.user)

    return {
        "success": True,
        "theme": selected_theme,
        "mode": mode
    }
