# Copyright (c) 2025, its-alikhokher
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
import json


class UserThemePreference(Document):
    pass


@frappe.whitelist()
def get_active_theme(user=None):
    """Get active theme for user"""
    if not user:
        user = frappe.session.user
    
    # Check user preference first
    try:
        pref = frappe.get_doc("User Theme Preference", {"user": user})
        if pref.active_theme:
            theme = frappe.get_doc("Theme Definition", pref.active_theme)
            return theme.as_dict()
    except frappe.DoesNotExistError:
        pass
    
    # Return default theme
    default_theme = frappe.db.get_value("Theme Definition", {"is_default": 1}, "name")
    if default_theme:
        return frappe.get_doc("Theme Definition", default_theme).as_dict()
    
    return None


@frappe.whitelist()
def set_active_theme(theme_key, user=None):
    """Set active theme for user"""
    if not user:
        user = frappe.session.user
    
    if user == "Guest":
        frappe.throw(_("Guest users cannot set theme preferences"))
    
    # Validate theme exists
    if not frappe.db.exists("Theme Definition", theme_key):
        frappe.throw(_("Theme {0} does not exist").format(theme_key))
    
    try:
        pref = frappe.get_doc("User Theme Preference", {"user": user})
        pref.active_theme = theme_key
        pref.save(ignore_permissions=True)
    except frappe.DoesNotExistError:
        pref = frappe.get_doc({
            "doctype": "User Theme Preference",
            "user": user,
            "active_theme": theme_key,
            "enabled": 1
        })
        pref.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    # Clear cache
    frappe.clear_cache(user=user)
    
    return {"success": True, "theme": theme_key}


@frappe.whitelist()
def get_all_themes():
    """Get all available themes"""
    themes = frappe.get_all("Theme Definition", 
                           fields=["name", "theme_name", "theme_key", "is_dark", "is_default", "accent"],
                           order_by="is_default desc, theme_name asc")
    return themes


@frappe.whitelist()
def create_custom_theme(theme_data):
    """Create a custom theme from data"""
    if isinstance(theme_data, str):
        theme_data = json.loads(theme_data)
    
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Guest users cannot create themes"))
    
    theme = frappe.get_doc({
        "doctype": "Theme Definition",
        "theme_name": theme_data.get("theme_name"),
        "theme_key": theme_data.get("theme_key"),
        "is_dark": cint(theme_data.get("is_dark", 0)),
        "owner_user": user,
        "is_public": cint(theme_data.get("is_public", 0)),
        "bg_primary": theme_data.get("bg_primary"),
        "bg_surface": theme_data.get("bg_surface"),
        "accent": theme_data.get("accent"),
        "text_primary": theme_data.get("text_primary"),
        "text_muted": theme_data.get("text_muted"),
    })
    
    theme.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return theme.name

