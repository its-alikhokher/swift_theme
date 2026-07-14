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
