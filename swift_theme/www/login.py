import frappe
from frappe.utils.html_utils import get_html_content_type
from frappe.website.utils import is_cache_enabled

def get_context(context):
    """Override default login context for Swift Theme"""
    from frappe.www.login import get_context as default_get_context
    
    # Call the default context function
    default_get_context(context)
    
    # Add Swift Theme specific settings
    context.swift_login_layout = frappe.db.get_single_value("Swift Theme Settings", "login_layout") or "Centered"
    context.brand_logo = frappe.db.get_single_value("Swift Theme Settings", "brand_logo") or "/assets/swift_theme/icons/favicon.svg"
    context.tagline = frappe.db.get_single_value("Swift Theme Settings", "login_tagline") or "Welcome back! Please sign in to continue."
    
    return context
