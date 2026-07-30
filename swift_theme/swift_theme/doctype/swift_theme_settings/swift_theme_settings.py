import json
import frappe
from frappe.model.document import Document

PRESETS = {
    "Linear":     {"default_accent": "violet",  "default_theme": "obsidian",   "default_density": "Compact",     "default_radius": "Rounded", "default_font_family": "Inter",   "default_font_scale": "M", "navbar_variant": "Glass",       "sidebar_variant": "Attached"},
    "Vercel":     {"default_accent": "slate",   "default_theme": "monochrome", "default_density": "Comfortable", "default_radius": "Rounded", "default_font_family": "Inter",   "default_font_scale": "M", "navbar_variant": "Solid",       "sidebar_variant": "Attached"},
    "Stripe":     {"default_accent": "indigo",  "default_theme": "porcelain",  "default_density": "Comfortable", "default_radius": "Rounded", "default_font_family": "Inter",   "default_font_scale": "M", "navbar_variant": "Glass",       "sidebar_variant": "Attached"},
    "Raycast":    {"default_accent": "violet",  "default_theme": "aurora",     "default_density": "Comfortable", "default_radius": "Rounded", "default_font_family": "Inter",   "default_font_scale": "M", "navbar_variant": "Glass",       "sidebar_variant": "Floating"},
    "Superhuman": {"default_accent": "teal",    "default_theme": "midnight",   "default_density": "Compact",     "default_radius": "Rounded", "default_font_family": "Inter",   "default_font_scale": "M", "navbar_variant": "Glass",       "sidebar_variant": "Icon-only"},
    "Notion":     {"default_accent": "slate",   "default_theme": "sandstone",  "default_density": "Cozy",        "default_radius": "Rounded", "default_font_family": "Manrope", "default_font_scale": "M", "navbar_variant": "Solid",       "sidebar_variant": "Attached"},
    "Terminal":   {"default_accent": "emerald", "default_theme": "carbon",     "default_density": "Compact",     "default_radius": "Sharp",   "default_font_family": "System",  "default_font_scale": "S", "navbar_variant": "Solid",       "sidebar_variant": "Attached"},
    "Editorial":  {"default_accent": "amber",   "default_theme": "graphite",   "default_density": "Cozy",        "default_radius": "Rounded", "default_font_family": "Manrope", "default_font_scale": "L", "navbar_variant": "Solid",       "sidebar_variant": "Floating"},
}

PREMIUM_THEMES = [
    {
        "name": "Swift Blue",
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
    {
        "name": "Midnight Pro",
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
    {
        "name": "Emerald Luxury",
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
    {
        "name": "Rose Gold",
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
    {
        "name": "Sapphire Elite",
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
    {
        "name": "Golden Hour",
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
    {
        "name": "Carbon Fiber",
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
    {
        "name": "Pearl White",
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
    {
        "name": "Royal Purple",
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
    {
        "name": "Ocean Depth",
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
    {
        "name": "Forest Mist",
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
    {
        "name": "Crimson Red",
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
]


class SwiftThemeSettings(Document):
    def validate(self):
        # Apply preset if user selected one (then clear the trigger field)
        if self.active_preset and self.active_preset in PRESETS:
            for k, v in PRESETS[self.active_preset].items():
                self.set(k, v)
            self.active_preset = ""

        # Apply imported JSON
        if self.import_preset_json:
            try:
                data = json.loads(self.import_preset_json)
                allowed = self._exportable_fields()
                for k, v in data.items():
                    if k in allowed:
                        self.set(k, v)
                self.import_preset_json = ""
            except Exception as e:
                frappe.throw(f"Invalid preset JSON: {e}")

        # Refresh exported JSON snapshot
        self.export_preset_json = json.dumps(self._export_dict(), indent=2)

    def on_update(self):
        frappe.clear_cache()
        frappe.publish_realtime("swift_theme_updated", {}, after_commit=True)

    def _exportable_fields(self):
        return {
            "default_accent", "default_theme", "default_density", "default_radius",
            "default_font_family", "default_font_scale",
            "navbar_variant", "sidebar_variant",
            "enable_switcher", "enable_command_palette", "enable_focus_mode",
            "enable_perf_mode", "enable_styled_scrollbar", "enable_toast_theming",
            "enable_print_theming", "print_font_family",
            "brand_name", "brand_hex_override",
            "login_layout", "login_tagline", "login_show_signup",
            "enable_auto_dark", "auto_dark_start", "auto_dark_end",
        }

    def _export_dict(self):
        d = {}
        for k in self._exportable_fields():
            d[k] = self.get(k)
        return d


@frappe.whitelist()
def get_premium_themes():
    """Returns the catalog of luxury premium themes available in Swift Theme"""
    return {"themes": PREMIUM_THEMES}


@frappe.whitelist()
def apply_theme(theme_value):
    """Applies a specific premium theme for the current user session"""
    selected_theme = next((t for t in PREMIUM_THEMES if t["value"] == theme_value), None)
    
    if not selected_theme:
        frappe.throw("Theme not found")
    
    # Set user preference
    frappe.db.set_value("User", frappe.session.user, "swift_selected_theme", theme_value)
    
    # Auto-set Dark/Light Mode based on theme
    mode = selected_theme.get("mode", "light")
    frappe.db.set_value("User", frappe.session.user, "desk_theme", mode)
    
    frappe.clear_cache(user=frappe.session.user)
    
    return {
        "success": True,
        "theme": selected_theme,
        "mode": mode
    }
