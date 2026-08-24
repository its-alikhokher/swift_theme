import frappe
from frappe import _
from frappe.apps import get_default_path
from frappe.utils import cint, now_datetime
from frappe.website.utils import get_home_page
from frappe.www.login import sanitize_redirect

from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    get_active_theme_config,
)

no_cache = True


def get_context(context):
    # frappe.local.request is absent when the page is rendered outside a web
    # request (tests, cache warming), so don't assume it exists.
    request = getattr(frappe.local, "request", None)
    redirect_to = sanitize_redirect(request.args.get("redirect-to") if request else None)

    # Already signed in — don't show them a login form.
    if frappe.session.user != "Guest":
        if not redirect_to:
            if frappe.session.data.user_type == "Website User":
                redirect_to = get_default_path() or get_home_page()
            else:
                redirect_to = get_default_path() or "/app"

        if redirect_to != "login":
            frappe.local.flags.redirect_location = redirect_to
            raise frappe.Redirect

    context.no_header = True
    context.no_cache = 1
    context["title"] = _("Login")
    context["hide_login"] = True
    context["redirect_to"] = redirect_to or ""

    # Issued so the login POST carries a valid token once the Guest session has
    # one; without it that request is rejected as an Invalid Request. Needs a
    # live session object, which isn't there outside a web request.
    try:
        context["csrf_token"] = frappe.sessions.get_csrf_token()
    except AttributeError:
        context["csrf_token"] = ""

    context["disable_signup"] = cint(frappe.get_website_settings("disable_signup"))

    # Rendered server-side so the themed page paints correctly on first load
    # instead of flashing default colours while an API call resolves.
    theme = get_active_theme_config()
    colors = theme.get("colors") or {}
    context["theme"] = theme
    context["colors"] = colors
    context["is_dark_mode"] = bool(theme.get("is_dark_mode"))
    context["custom_login_text"] = theme.get("custom_login_text") or _(
        "Secure login powered by Swift Theme Enterprise"
    )

    settings = frappe.get_cached_doc("Swift Theme Settings")
    context["brand_name"] = settings.brand_name or frappe.get_website_settings("app_name") or ""
    context["brand_logo"] = settings.brand_logo or ""
    context["login_tagline"] = settings.login_tagline or ""
    context["login_layout"] = settings.login_layout or "Split"
    context["login_bg_image"] = settings.login_bg_image or ""
    context["show_signup"] = bool(settings.login_show_signup) and not context["disable_signup"]

    # Everything printed on the brand panel comes from Settings. It used to be
    # written into the template, so the one thing a site most wants to change
    # about its login page was the one thing it could not.
    #
    # Falling back to the DocType's own default rather than to a literal here:
    # a site that clears a field wants it empty, and a site that has never
    # touched it gets what the field ships with, from one place.
    def setting(fieldname):
        value = settings.get(fieldname)
        return value if value is not None else ""

    def lines(fieldname):
        return [line.strip() for line in (setting(fieldname) or "").splitlines()
                if line.strip()]

    context["login_show_brand_panel"] = bool(settings.login_show_brand_panel)
    context["login_heading_lines"] = lines("login_heading")
    context["login_description"] = setting("login_description")
    context["login_points"] = lines("login_points")
    context["login_stat_value"] = setting("login_stat_value")
    context["login_stat_label"] = setting("login_stat_label")

    # Computed here rather than in the template — the Jinja sandbox does not
    # reliably expose frappe.utils.
    context["current_year"] = now_datetime().year

    return context
