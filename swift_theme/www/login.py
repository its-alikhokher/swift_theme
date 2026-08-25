import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.www.login import get_context as frappe_login_context
from frappe.www.login import sanitize_redirect

from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    get_active_theme_config,
)

no_cache = True


def get_context(context):
    # Frappe's own login controller runs first, and everything it puts on the
    # context is kept. This page replaces Frappe's login page, so anything it
    # offers has to be offered here too: the social login providers, LDAP, the
    # email-link sign-in, the sign-up form, whether user/password login is
    # allowed at all, and what the identifier field should be called.
    #
    # Delegating rather than restating it also means a Frappe release that adds
    # a login option gets it here without this file changing. The version that
    # restated the list drifted immediately — it sent signed-in users to /app,
    # which is the v15 desk, and dropped every provider.
    #
    # It also performs the signed-in redirect, by raising frappe.Redirect.
    #
    # Guarded because it reads frappe.local.request without checking for it,
    # and this page is also rendered with no request behind it — website cache
    # warming and tests both do that. Letting the AttributeError through would
    # turn a warm-up into a build failure, so the offline path fills in the
    # same keys with the answers a request would have produced.
    request = getattr(frappe.local, "request", None)
    if request is not None:
        frappe_login_context(context)
    else:
        _context_without_a_request(context)

    redirect_to = sanitize_redirect(request.args.get("redirect-to") if request else None)

    context.no_cache = 1
    context["title"] = _("Login")
    context["redirect_to"] = redirect_to or ""

    # Issued so the login POST carries a valid token once the Guest session has
    # one; without it that request is rejected as an Invalid Request. Needs a
    # live session object, which isn't there outside a web request.
    try:
        context["csrf_token"] = frappe.sessions.get_csrf_token()
    except AttributeError:
        context["csrf_token"] = ""

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
    # Rendered onto <body> by templates/base.html rather than added by a script
    # afterwards. The layout decides the whole look, so a class applied after
    # first paint means the page visibly changes shape as it loads.
    # A site's own picture could be anything — including a pale one, or a logo
    # — so the page says which it is and the stylesheet treats them
    # differently: the shipped photograph is known to be dark and can be shown
    # vividly, an uploaded one gets a heavier scrim so the text stays readable
    # whatever arrived.
    classes = ["swift-login", "swift-login-{0}".format(context["login_layout"])]
    if settings.login_bg_image:
        classes.append("swift-login-custom-bg")
    context["body_class"] = " ".join(classes)
    context["login_bg_image"] = settings.login_bg_image or ""

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
    # The theme's own variables, written into the page.
    #
    # Without them every rule in the login stylesheet that reads
    # var(--swift-accent) — the button's fill, the borders, the surfaces — is
    # invalid at computed-value time and simply drops, which is why the page
    # looked unstyled however much CSS was aimed at it. They cannot come from
    # the preset stylesheet here: that file is keyed on an attribute of <html>,
    # and this page does not own the <html> tag. Rendered inline instead, so
    # they are there for the first paint rather than after a script runs.
    context["theme_variables"] = _theme_variables()

    context["current_year"] = now_datetime().year

    return context


def _context_without_a_request(context):
    """The login options, resolved without a live request.

    Only what the template reads. The social providers are deliberately left
    empty: building their authorise URLs needs the redirect target from the
    request, and a provider button pointing at the wrong place is worse than
    no button on a page nobody is looking at.
    """
    from frappe.utils import cint

    context.no_header = True
    context["hide_login"] = True
    context["provider_logins"] = []
    context["disable_signup"] = cint(frappe.get_website_settings("disable_signup"))
    context["show_footer_on_login"] = cint(
        frappe.get_website_settings("show_footer_on_login"))
    context["disable_user_pass_login"] = cint(
        frappe.get_system_settings("disable_user_pass_login"))
    context["login_with_email_link"] = frappe.get_system_settings("login_with_email_link")

    labels = [_("Email")]
    if cint(frappe.get_system_settings("allow_login_using_mobile_number")):
        labels.append(_("Mobile"))
    if cint(frappe.get_system_settings("allow_login_using_user_name")):
        labels.append(_("Username"))
    context["login_label"] = f" {_('or')} ".join(labels)


# Mirrors ROLE_VARS in public/js/swift-boot.js. The desk gets these from the
# preset stylesheet and the portal from that script; the login page is the one
# place neither reaches, so the mapping is needed on this side too. A test
# compares the two, so they cannot drift apart.
ROLE_VARS = {
    "canvas":      ["--swift-canvas", "--bg-color"],
    "surface":     ["--swift-surface", "--card-bg", "--fg-color"],
    "surface_alt": ["--swift-surface-alt", "--subtle-fg", "--sidebar-bg", "--control-bg"],
    "on_canvas":   ["--swift-on-canvas", "--heading-color"],
    "on_surface":  ["--swift-on-surface", "--text-color"],
    "muted":       ["--text-muted", "--text-light"],
    "border":      ["--border-color"],
    "primary":     ["--swift-primary", "--swift-accent"],
    "secondary":   ["--swift-secondary", "--swift-accent-hover"],
    "on_primary":  ["--swift-accent-fg"],
}


def _theme_variables():
    """The resolved palette as CSS custom property declarations."""
    from swift_theme.api.boot import get_effective_prefs

    roles = (get_effective_prefs() or {}).get("roles") or {}
    lines = []
    for role, names in ROLE_VARS.items():
        value = roles.get(role)
        if not value:
            continue
        for name in names:
            lines.append(f"{name}: {value};")

    # Two the role set does not carry but the stylesheet reads.
    tint = roles.get("tint")
    if tint:
        lines.append(f"--swift-accent-tint: {tint};")
    primary = roles.get("primary")
    if primary:
        lines.append(
            f"--swift-accent-soft: color-mix(in oklab, {primary} 14%, transparent);")

    return "\n            ".join(lines)
