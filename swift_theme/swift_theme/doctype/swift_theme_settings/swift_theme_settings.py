import frappe
from frappe.model.document import Document


class SwiftThemeSettings(Document):
    def on_update(self):
        # Bust user cache so new prefs load immediately
        frappe.clear_cache()
