"""Regression tests for Swift Theme.

Each test maps to a defect that shipped silently: the desk JS gated on Settings
fields that no longer existed, the login page called whitelisted methods as
Guest, and several CSS attribute values had no rule behind them. None of those
raised an exception — they quietly did nothing, which is exactly the class of
bug that needs a test rather than a manual check.

Two deliberate choices about *how* things are asserted:

* Guest access is checked against ``frappe.guest_methods`` rather than by
  calling the function. ``allow_guest`` is enforced by the HTTP layer only, so
  a direct Python call succeeds regardless and would prove nothing.
* Browser behaviour is asserted against the shipped JS source. These are
  contract checks, not a substitute for real JS tests — but the bug this app
  actually had was "Python publishes an event and nothing listens", which a
  Python-only suite cannot see.
"""

import json
import os
import re
from contextlib import contextmanager

import frappe
from frappe.tests import IntegrationTestCase

from swift_theme.api.boot import can_switch_theme, get_effective_prefs, set_user_pref
from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    PREMIUM_THEMES,
    theme_colors,
    apply_theme,
    get_active_theme_config,
    get_premium_themes,
    play_sound,
)

APP = "swift_theme"
CSS_DIR = frappe.get_app_path(APP, "public", "css")
JS_DIR = frappe.get_app_path(APP, "public", "js")
SETTINGS_JSON = frappe.get_app_path(
    APP, "swift_theme", "doctype", "swift_theme_settings", "swift_theme_settings.json"
)

# Every Settings field read by api/boot.py or the desk JS. If one goes missing
# again the features it gates fail silently, so assert the whole set.
REQUIRED_SETTINGS_FIELDS = [
    "color_mode", "active_preset",
    "primary_color", "secondary_color",
    "default_density", "default_radius",
    "default_font_scale", "default_font_family",
    "navbar_variant", "sidebar_variant",
    "enable_switcher", "enable_command_palette", "enable_focus_mode",
    "enable_perf_mode", "enable_styled_scrollbar", "enable_toast_theming",
    "enable_print_theming", "print_font_family",
    "brand_name", "brand_logo", "brand_logo_dark", "brand_favicon",
    "login_layout", "login_bg_image", "login_tagline",
    "enable_auto_dark", "auto_dark_start", "auto_dark_end",
    "enable_sounds", "volume_level", "sound_events",
]

COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)


def read_css(filename=None):
    """CSS with comments stripped, so a commented-out rule can't satisfy a test.

    Pass a filename to scope the check — concatenating every stylesheet lets a
    rule in login.css accidentally satisfy an assertion about the desk.
    """
    names = [filename] if filename else sorted(
        n for n in os.listdir(CSS_DIR) if n.endswith(".css")
    )
    blob = ""
    for name in names:
        with open(os.path.join(CSS_DIR, name)) as f:
            blob += COMMENT_RE.sub("", f.read())
    return blob


BUNDLES = {
    "app_include_css": "swift_theme.bundle.scss",
    "web_include_css": "swift_theme_web.bundle.scss",
    "app_include_js": "swift_theme.bundle.js",
    "web_include_js": "swift_theme_web.bundle.js",
}


def bundle_contents(bundle):
    """The files a bundle imports, in order."""
    folder = "css" if bundle.endswith(("css", "scss")) else "js"
    with open(frappe.get_app_path(APP, "public", folder, bundle)) as handle:
        body = handle.read()
    # "@import" contains "import", so the script pattern has to refuse the
    # sass one or every stylesheet is counted twice, once without its suffix.
    return [f"{m}.css" for m in re.findall(r'@import\s+"\./([^"]+)"', body)] + \
        re.findall(r'(?<!@)\bimport\s+"\./([^"]+)"', body)


def loaded_assets(hook):
    """The files a hook actually serves, in the order they are applied.

    The hooks name a bundle, not the individual files — Frappe only content
    hashes a path containing ".bundle.", and without a hash the browser kept
    serving the previous release. The order that used to live in the hook list
    now lives in the bundle's import list, and it is just as load-bearing, so
    resolve through to the real names rather than testing the bundle name.
    """
    # Frappe and any other installed app contribute to the same hook; only
    # this app's entries say anything about this app.
    entries = [e for e in (frappe.get_hooks(hook) or []) if "swift" in e.lower()]
    names = []
    for entry in entries:
        bundle = BUNDLES.get(hook)
        if bundle and entry.endswith(bundle.replace(".scss", ".css")):
            names += bundle_contents(bundle)
        else:
            names.append(entry.rsplit("/", 1)[-1])
    return names


RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def css_rules(filename):
    """Every innermost `selector { declarations }` pair in one stylesheet.

    Nested at-rules are handled by only matching brace-free chunks, so a rule
    inside @media is returned on its own.
    """
    for match in RULE_RE.finditer(read_css(filename)):
        selector = " ".join(match.group(1).split())
        if selector.startswith("@"):
            continue
        yield selector, match.group(2)


def selects_the_backdrop(selector):
    """Whether this selector reaches body::before / body::after.

    The universal form counts: `*::before` matches the backdrop just as surely
    as naming it, which is how perf mode came to flatten it by accident.
    """
    compact = selector.replace(" ", "")
    if ":not(body)::before" in compact or ":not(body)::after" in compact:
        return False
    return any(part in compact for part in
               ("body::before", "body::after", "*::before", "*::after"))


def read_js(filename):
    with open(os.path.join(JS_DIR, filename)) as f:
        return f.read()


def settings_json_options(fieldname):
    """Options straight from the DocType JSON.

    Reading frappe.get_meta() instead would mean a DocType that failed to sync
    (which has happened here) is tested in its stale state.
    """
    with open(SETTINGS_JSON) as f:
        schema = json.load(f)
    for field in schema["fields"]:
        if field["fieldname"] == fieldname:
            return [o for o in (field.get("options") or "").split("\n") if o]
    raise AssertionError(f"{fieldname} is not defined in swift_theme_settings.json")


@contextmanager
def settings_patched(**values):
    """Apply Settings values for a test, then put them back.

    The save happens inside the try so a validation error still restores state.
    """
    doc = frappe.get_single("Swift Theme Settings")
    previous = {k: doc.get(k) for k in values}
    try:
        for key, value in values.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        frappe.clear_cache()
        yield doc
    finally:
        doc = frappe.get_single("Swift Theme Settings")
        for key, value in previous.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        frappe.clear_cache()


@contextmanager
def stale_single_value(field, value):
    """Put a value in the row that the field would reject on save.

    This is the state a site is genuinely in part-way through an upgrade, and
    it cannot be reached through the ORM — which is the point, since the bugs
    it reproduces are ones only that state triggers.
    """
    previous = frappe.db.get_single_value("Swift Theme Settings", field)
    frappe.db.set_single_value("Swift Theme Settings", field, value)
    frappe.clear_cache()
    try:
        yield
    finally:
        frappe.db.set_single_value("Swift Theme Settings", field, previous)
        frappe.db.commit()
        frappe.clear_cache()


@contextmanager
def no_user_preset():
    """Clear the session user's preset so the site setting is what's measured."""
    user = frappe.session.user
    previous = frappe.db.get_value("User", user, "swift_preset")
    frappe.db.set_value("User", user, "swift_preset", None)
    try:
        yield
    finally:
        frappe.db.set_value("User", user, "swift_preset", previous)


def make_user(roles):
    """A throwaway user for permission checks."""
    slug = "-".join(roles).lower().replace(" ", "-") or "plain"
    email = f"swift-perm-{slug}@example.com"
    if not frappe.db.exists("User", email):
        doc = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Swift Perm Test",
            "send_welcome_email": 0,
            "roles": [{"role": r} for r in roles],
        })
        doc.insert(ignore_permissions=True)
    return email


@contextmanager
def as_guest():
    original = frappe.session.user
    frappe.set_user("Guest")
    try:
        yield
    finally:
        frappe.set_user(original)


class TestSwiftThemeSchema(IntegrationTestCase):
    def test_settings_has_every_field_the_code_reads(self):
        """The rewrite dropped ~25 fields while boot.py still read them."""
        meta = frappe.get_meta("Swift Theme Settings")
        missing = [f for f in REQUIRED_SETTINGS_FIELDS if not meta.has_field(f)]
        self.assertEqual(missing, [], f"Swift Theme Settings is missing: {missing}")

    def test_installed_schema_matches_the_json(self):
        """Catches a DocType that silently failed to sync during migrate."""
        for fieldname in ("sidebar_variant", "navbar_variant", "login_layout"):
            installed = frappe.get_meta("Swift Theme Settings").get_field(fieldname)
            self.assertEqual(
                [o for o in (installed.options or "").split("\n") if o],
                settings_json_options(fieldname),
                f"{fieldname} in the database does not match the shipped JSON — "
                "run bench migrate with redis running",
            )

    def test_sound_event_child_table_is_configured_as_a_child_table(self):
        meta = frappe.get_meta("Swift Theme Sound Event")
        self.assertTrue(meta.istable, "Swift Theme Sound Event must be a child table")
        # autoname/unique are meaningless on a child table, and the unique index
        # would have blocked the same event key across parents.
        self.assertFalse(meta.autoname, "child tables are hash-named")
        self.assertFalse(meta.get_field("event_key").unique)


class TestSwiftThemeAccessControl(IntegrationTestCase):
    """allow_guest lives in a registry the HTTP layer consults.

    Calling the function directly never checks it, so these assert the registry.
    """

    GUEST_ENDPOINTS = [get_active_theme_config, play_sound, get_effective_prefs]
    PRIVILEGED_ENDPOINTS = [set_user_pref, apply_theme, get_premium_themes]

    def test_login_page_endpoints_allow_guest(self):
        for fn in self.GUEST_ENDPOINTS:
            self.assertIn(
                fn,
                frappe.guest_methods,
                f"{fn.__name__} is called before login and must allow guests",
            )

    def test_privileged_endpoints_reject_guests(self):
        for fn in self.PRIVILEGED_ENDPOINTS:
            self.assertNotIn(
                fn,
                frappe.guest_methods,
                f"{fn.__name__} writes or exposes config and must not allow guests",
            )

    def test_guest_prefs_exclude_custom_code(self):
        """The login page needs prefs, but Guests must not receive custom JS/CSS."""
        with as_guest():
            prefs = get_effective_prefs()
        self.assertNotIn("custom_js", prefs)
        self.assertNotIn("custom_css", prefs)
        self.assertIn("login_layout", prefs, "login page still needs its layout")

    def test_set_user_pref_rejects_unknown_fields(self):
        with self.assertRaises(frappe.ValidationError):
            set_user_pref("desk_theme", "Dark")

    def test_set_user_pref_rejects_guests(self):
        with as_guest():
            with self.assertRaises(frappe.ValidationError):
                set_user_pref("swift_accent", "rose")

    def test_the_signup_switch_is_gone_from_the_schema_too(self):
        """Removing the code is not removing the field.

        The switch was taken out of the controller, the template and the
        payload, and a patch was written to clear what sites had stored — but
        it stayed in the DocType. So every migrate wrote it straight back from
        the meta, and the patch deleted a row that reappeared moments later.
        Nothing failed; the setting simply would not die.
        """
        self.assertFalse(
            frappe.get_meta("Swift Theme Settings").has_field("login_show_signup"),
            "login_show_signup is still a field, so a save writes it back "
            "however many times the patch deletes it")

        with open(SETTINGS_JSON) as handle:
            self.assertNotIn(
                "login_show_signup", handle.read(),
                "the field is still declared in the DocType JSON")

    def test_custom_code_injection_is_gone_completely(self):
        """Removed feature, removed remains.

        Custom CSS and JS let anyone who could reach this form run script on
        every desk page. A theming app has no business holding that, and Frappe
        already offers Client Scripts behind their own permissions. Half a
        removal is worse than none — a field left in the schema still stores
        what an upgrade would start executing again — so check every layer.
        """
        for fieldname in ("custom_css", "custom_js"):
            self.assertFalse(
                frappe.get_meta("Swift Theme Settings").has_field(fieldname),
                f"{fieldname} is still a field on the Settings form")
            self.assertFalse(
                frappe.db.exists(
                    "Singles", {"doctype": "Swift Theme Settings", "field": fieldname}),
                f"{fieldname} still has a stored value on this site")

        app = frappe.get_app_path(APP)
        offenders = []
        for root, _dirs, files in os.walk(app):
            if "__pycache__" in root or "/patches/" in root:
                continue        # the patch that removes them must name them
            for name in files:
                if not name.endswith((".py", ".js", ".json", ".html")):
                    continue
                # Nor can the code that proves the removal avoid naming it:
                # this test, and the script that plants the old state and then
                # checks the migrate cleared it.
                if name in (os.path.basename(__file__), "verify_upgrade.py"):
                    continue
                path = os.path.join(root, name)
                with open(path) as handle:
                    body = handle.read()
                if "custom_css" in body or "custom_js" in body:
                    offenders.append(os.path.relpath(path, app))
        self.assertEqual(
            offenders, [],
            f"these still reference the removed custom code fields: {offenders}")


class TestSwiftThemeSwitchPermission(IntegrationTestCase):
    """Only Administrator / System Manager may change the theme."""

    def test_administrator_may_switch(self):
        self.assertTrue(can_switch_theme())
        self.assertTrue(get_effective_prefs()["can_switch_theme"])

    def test_plain_user_may_not_switch(self):
        user = make_user([])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            self.assertFalse(can_switch_theme())
            self.assertFalse(get_effective_prefs()["can_switch_theme"])
        finally:
            frappe.set_user(original)

    def test_system_manager_may_switch(self):
        user = make_user(["System Manager"])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            self.assertTrue(can_switch_theme())
        finally:
            frappe.set_user(original)

    def test_endpoint_refuses_a_plain_user(self):
        """Hiding the UI is not a control — the endpoint is reachable directly."""
        user = make_user([])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            with self.assertRaises(frappe.PermissionError):
                set_user_pref("swift_preset", "Hulk")
            with self.assertRaises(frappe.PermissionError):
                set_user_pref("swift_primary", "#123456")
        finally:
            frappe.set_user(original)

    def test_apply_theme_endpoint_refuses_a_plain_user_too(self):
        """The other endpoint that writes swift_preset must gate it identically.

        set_user_pref guarded the field and apply_theme did not, so the same
        change refused through one whitelisted method went straight through the
        other — the permission check was effectively optional for anyone
        calling the API rather than using the switcher.
        """
        from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
            apply_theme,
        )

        user = make_user([])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            with self.assertRaises(frappe.PermissionError):
                apply_theme("Hulk")
            # A fresh user's swift_preset is "" (the Custom Field's default),
            # not None — so assert the write did not land rather than that the
            # field is empty in some particular way.
            self.assertNotEqual(
                frappe.db.get_value("User", user, "swift_preset"), "Hulk",
                "the preset was written despite the refusal")
        finally:
            frappe.set_user(original)

    def test_apply_theme_still_works_for_someone_allowed(self):
        """The guard must not lock out the people it is meant to admit."""
        from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
            apply_theme,
        )

        user = make_user(["System Manager"])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            apply_theme("Hulk")
            self.assertEqual(frappe.db.get_value("User", user, "swift_preset"), "Hulk")
        finally:
            frappe.set_user(original)

    def test_layout_prefs_stay_open_to_everyone(self):
        """Only colour is restricted; density and font are personal comfort."""
        user = make_user([])
        original = frappe.session.user
        frappe.set_user(user)
        try:
            set_user_pref("swift_density", "Compact")
            self.assertEqual(frappe.db.get_value("User", user, "swift_density"), "Compact")
        finally:
            frappe.set_user(original)


class TestSwiftThemePreferences(IntegrationTestCase):
    def test_feature_flags_are_integers_not_none(self):
        """JS does `if (!boot.enable_switcher) return;` — None disables it."""
        prefs = get_effective_prefs()
        for flag in (
            "enable_switcher", "enable_command_palette", "enable_focus_mode",
            "enable_perf_mode", "enable_styled_scrollbar", "enable_toast_theming",
            "enable_print_theming",
        ):
            self.assertIn(flag, prefs)
            self.assertIsInstance(prefs[flag], int, f"{flag} must be an int")

    def test_switcher_flag_follows_the_setting(self):
        with settings_patched(enable_switcher=1):
            self.assertEqual(get_effective_prefs()["enable_switcher"], 1)
        with settings_patched(enable_switcher=0):
            self.assertEqual(get_effective_prefs()["enable_switcher"], 0)

    def test_sounds_config_is_shipped_in_boot(self):
        prefs = get_effective_prefs()
        self.assertIn("sounds", prefs)
        self.assertIn("enabled", prefs["sounds"])
        self.assertIn("files", prefs["sounds"])

    def test_saved_value_is_visible_to_the_next_read(self):
        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki"):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["preset_name"], "Loki")
        self.assertEqual(prefs["preset"], "loki")
        self.assertEqual(prefs["theme_css"], "/assets/swift_theme/css/themes/loki.css")

    def test_saving_a_new_colour_clears_stale_user_overrides(self):
        """The exact bug: Save appeared to do nothing.

        A swift_preset stored on the User outranks this doctype, so once anyone
        had used the navbar switcher, changing the site colour silently did
        nothing for them.
        """
        user = frappe.session.user
        previous = frappe.db.get_value("User", user, "swift_preset")
        # The release is driven by the value actually changing, so pick a
        # preset that differs from whatever this site is currently on.
        current = frappe.db.get_single_value("Swift Theme Settings", "active_preset")
        target = next(n for n in PREMIUM_THEMES if n != current)
        try:
            frappe.db.set_value("User", user, "swift_preset", "Black Panther")

            with settings_patched(color_mode="Theme Preset", active_preset=target):
                self.assertIsNone(
                    frappe.db.get_value("User", user, "swift_preset"),
                    "changing the site colour must stand user overrides down",
                )
                self.assertEqual(get_effective_prefs()["preset_name"], target)
        finally:
            frappe.db.set_value("User", user, "swift_preset", previous)

    def test_unrelated_save_keeps_user_overrides(self):
        """Only a colour change releases them — not every save."""
        user = frappe.session.user
        previous = frappe.db.get_value("User", user, "swift_preset")
        try:
            frappe.db.set_value("User", user, "swift_preset", "Black Panther")
            with settings_patched(login_tagline="Unrelated change"):
                self.assertEqual(
                    frappe.db.get_value("User", user, "swift_preset"), "Black Panther"
                )
        finally:
            frappe.db.set_value("User", user, "swift_preset", previous)

    def test_user_can_set_their_own_colour_pair(self):
        """Picked from the navbar dialog; outranks both presets."""
        user = frappe.session.user
        before = frappe.db.get_value(
            "User", user, ["swift_preset", "swift_primary", "swift_secondary"], as_dict=True
        )
        try:
            frappe.db.set_value(
                "User", user, {"swift_primary": "#123456", "swift_secondary": "#654321"}
            )
            prefs = get_effective_prefs()
            self.assertEqual(prefs["primary"], "#123456")
            self.assertEqual(prefs["secondary"], "#654321")
            self.assertEqual(prefs["color_mode"], "Custom Colors")
            self.assertEqual(prefs["color_source"], "user")
            self.assertIsNone(prefs["preset"], "custom colours load no preset stylesheet")
        finally:
            frappe.db.set_value("User", user, dict(before))

    def test_user_colours_outrank_a_user_preset(self):
        user = frappe.session.user
        before = frappe.db.get_value(
            "User", user, ["swift_preset", "swift_primary", "swift_secondary"], as_dict=True
        )
        try:
            frappe.db.set_value(
                "User", user, {"swift_preset": "Hulk", "swift_primary": "#0abab5"}
            )
            self.assertEqual(get_effective_prefs()["primary"], "#0abab5")
        finally:
            frappe.db.set_value("User", user, dict(before))

    def test_site_colour_change_also_clears_user_colour_pairs(self):
        user = frappe.session.user
        before = frappe.db.get_value(
            "User", user, ["swift_preset", "swift_primary", "swift_secondary"], as_dict=True
        )
        current = frappe.db.get_single_value("Swift Theme Settings", "active_preset")
        target = next(n for n in PREMIUM_THEMES if n != current)
        try:
            frappe.db.set_value(
                "User", user, {"swift_primary": "#123456", "swift_secondary": "#654321"}
            )
            with settings_patched(color_mode="Theme Preset", active_preset=target):
                self.assertIsNone(frappe.db.get_value("User", user, "swift_primary"))
                self.assertEqual(get_effective_prefs()["preset_name"], target)
        finally:
            frappe.db.set_value("User", user, dict(before))

    def test_user_preset_overrides_the_site_preset(self):
        """A per-user choice must win, but only in Theme Preset mode."""
        user = frappe.session.user
        previous = frappe.db.get_value("User", user, "swift_preset")
        try:
            # Set the override *after* the site colour, so it isn't released.
            with settings_patched(color_mode="Theme Preset", active_preset="Loki"):
                frappe.db.set_value("User", user, "swift_preset", "Hulk")
                self.assertEqual(get_effective_prefs()["preset_name"], "Hulk")

            with settings_patched(
                color_mode="Custom Colors", primary_color="#123456", secondary_color="#654321"
            ):
                prefs = get_effective_prefs()
            self.assertEqual(prefs["primary"], "#123456")
            self.assertIsNone(prefs["preset"], "custom colours ignore the user preset")
        finally:
            frappe.db.set_value("User", user, "swift_preset", previous)

    def test_saving_settings_broadcasts_to_open_sessions(self):
        """Without this event the desk only updates on a hard refresh."""
        published = []
        original = frappe.publish_realtime

        def spy(event=None, message=None, **kwargs):
            published.append(event)
            return original(event, message, **kwargs)

        frappe.publish_realtime = spy
        try:
            with settings_patched(active_preset="Loki"):
                pass
        finally:
            frappe.publish_realtime = original

        self.assertIn("swift_theme_updated", published)

    def test_saving_settings_does_not_flush_the_whole_site_cache(self):
        """clear_cache() with no arguments drops roles, defaults and metadata."""
        calls = []
        original = frappe.clear_cache

        def spy(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)

        frappe.clear_cache = spy
        try:
            doc = frappe.get_single("Swift Theme Settings")
            doc.save(ignore_permissions=True)
        finally:
            frappe.clear_cache = original

        unscoped = [c for c in calls if not c[0] and not c[1]]
        self.assertEqual(unscoped, [], "on_update must scope its cache invalidation")


class TestSwiftThemeCustomColors(IntegrationTestCase):
    """Two hexes must produce a whole palette, not just an accent swap."""

    # A handful of cases missed a rounding disagreement between Python and JS
    # that only showed on about one blend in a hundred, so sweep the hue wheel
    # and both switches instead.
    HUES = [
        "#39e4a5", "#F21667", "#e0a422", "#0b84f3", "#8b5cf6", "#ef4444",
        "#14b8a6", "#84cc16", "#f97316", "#ec4899", "#64748b", "#ffffff",
        "#000000", "#6366f1", "#7c3aed", "#22d3ee", "#1d4ed8", "#be123c",
        "#d4a017", "#0f766e",
    ]
    CASES = [
        (hue, "#888888", mode, strength)
        for hue in HUES
        for mode in ("Dark", "Light")
        for strength in ("Subtle", "Bold")
    ]

    def test_derivation_produces_every_role(self):
        from swift_theme.scripts.colour import derive_roles

        roles = ("canvas", "surface", "surface_alt", "on_canvas", "on_surface",
                 "muted", "border", "primary", "secondary", "tint", "on_primary")
        for primary, secondary, mode, strength in self.CASES:
            r = derive_roles(primary, secondary, mode, strength)
            missing = [k for k in roles if not r.get(k)]
            self.assertEqual(missing, [], f"{primary} {mode}/{strength} missing {missing}")

    def test_derived_palettes_are_legible(self):
        """A user may pick any colour, including ones where neither black nor
        white clears 4.5:1 — the accent is nudged until one does."""
        from swift_theme.scripts.colour import contrast, derive_roles, luminance

        for primary, secondary, mode, strength in self.CASES:
            r = derive_roles(primary, secondary, mode, strength)
            for text, bg, label in ((r["on_surface"], r["surface"], "card"),
                                    (r["on_canvas"], r["canvas"], "page"),
                                    (r["on_primary"], r["primary"], "accent")):
                ratio = contrast(text, bg)
                self.assertGreaterEqual(
                    ratio, 4.5,
                    f"{primary} {mode}/{strength}: {label} is {ratio:.2f}:1")
            if mode == "Dark" and strength == "Subtle":
                self.assertGreater(
                    luminance(r["surface"]), luminance(r["canvas"]),
                    f"{primary} Dark/Subtle: card does not lift above the canvas")

    def test_python_and_javascript_derive_identically(self):
        """The maths exists twice — Python for the server, JS for the live
        preview. Duplicated logic drifts, so prove they agree hex for hex."""
        import json
        import shutil
        import subprocess

        from swift_theme.scripts.colour import derive_roles

        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")

        harness = frappe.get_app_path(APP, "tests", "derive_roles_parity.js")
        result = subprocess.run(
            [node, harness, json.dumps([list(c) for c in self.CASES])],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        from_js = json.loads(result.stdout)
        for case, js in zip(self.CASES, from_js):
            py = derive_roles(*case)
            for role in sorted(py):
                self.assertEqual(
                    str(js.get(role)).lower(), str(py[role]).lower(),
                    f"{case} role {role!r}: JS {js.get(role)} vs Python {py[role]}")

    def test_custom_mode_and_strength_are_configurable(self):
        """Both were impossible to express: custom colour was hardcoded dark
        and always subtle."""
        meta = frappe.get_meta("Swift Theme Settings")
        for field, options in (("custom_mode", {"Dark", "Light"}),
                               ("custom_strength", {"Subtle", "Bold"})):
            self.assertTrue(meta.has_field(field), f"{field} is missing")
            got = {o for o in meta.get_field(field).options.split("\n") if o}
            self.assertEqual(got, options)

    def test_preset_mode_also_reaches_the_client_as_roles(self):
        """A refresh must be able to paint the real colours with no network
        wait for the preset's own stylesheet.

        boot.js bridges with these roles inline the instant it runs, before
        that stylesheet has had a chance to arrive — without this key in the
        boot payload there is nothing to bridge with, and every refresh shows
        Frappe's own colours for as long as the stylesheet takes to load.
        """
        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki"):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["color_mode"], "Theme Preset")
        expected = PREMIUM_THEMES["Loki"]["roles"]
        self.assertEqual(prefs["roles"], expected,
                         "preset mode's roles must match the preset exactly, "
                         "since boot.js paints them verbatim before the "
                         "stylesheet is even requested")

    def test_boot_bridges_preset_roles_until_the_stylesheet_loads(self):
        """Source-level guard for the client half of the fix.

        A JS harness proves the bridge behaves correctly; this locks in the
        pieces it depends on existing at all, so a refactor cannot quietly
        drop one half of the mechanism without a Python test noticing too.
        """
        js = read_js("swift-boot.js")

        # Isolated to the bootstrap block specifically. frappe.boot.swift_theme
        # is read in several unrelated places further down the file (the
        # switcher, syncFromBoot), so a loose assertIn("frappe.boot...", js)
        # would still pass with this specific read removed — it did, the first
        # time this test was written, and caught nothing.
        bootstrap = js.split("var serverBoot", 1)
        self.assertEqual(
            len(bootstrap), 2,
            "the bootstrap call no longer reads frappe.boot.swift_theme at "
            "all, so a cold load has nothing to bridge with")
        self.assertIn(
            "frappe.boot && frappe.boot.swift_theme", bootstrap[1][:120],
            "serverBoot is no longer read from frappe.boot.swift_theme")

        self.assertIn('addEventListener("load"', js,
                      "nothing waits for the stylesheet to actually finish "
                      "loading before handing off from the bridge")
        self.assertIn('addEventListener("error"', js,
                      "a failed stylesheet fetch would leave the bridge "
                      "stuck forever with nothing to release it")

    def test_custom_colours_reach_the_client_as_roles(self):
        with settings_patched(color_mode="Custom Colors", primary_color="#39e4a5",
                              secondary_color="#F21667", custom_mode="Light",
                              custom_strength="Bold"):
            prefs = get_effective_prefs()
        self.assertEqual(prefs["color_mode"], "Custom Colors")
        self.assertTrue(prefs["roles"], "no roles sent; the desk would keep Frappe's surfaces")
        self.assertEqual(prefs["roles"]["surface"].lower(), "#39e4a5",
                         "Bold means the card takes the brand tone")
        self.assertEqual(prefs["is_dark"], 0, "Light mode was requested")

    def test_login_page_and_desk_agree_on_custom_colours(self):
        """The login page used a hardcoded navy while the desk used Frappe's
        defaults, so the two looked like different products."""
        with settings_patched(color_mode="Custom Colors", primary_color="#39e4a5",
                              secondary_color="#F21667", custom_mode="Dark",
                              custom_strength="Subtle"):
            prefs = get_effective_prefs()
            config = get_active_theme_config()
        self.assertEqual(config["primary"].lower(), prefs["primary"].lower())
        self.assertEqual(config["bg_body"].lower(), prefs["roles"]["canvas"].lower())
        self.assertEqual(config["bg_card"].lower(), prefs["roles"]["surface"].lower())


class TestSwiftThemeColors(IntegrationTestCase):
    def test_theme_config_flattens_colours(self):
        """login.js reads config.primary, not config.colors.primary."""
        with settings_patched(color_mode="Theme Preset", active_preset="Black Panther"):
            config = get_active_theme_config()

        expected = theme_colors("Black Panther")
        self.assertEqual(config["primary"], expected["primary"])
        self.assertEqual(config["secondary"], expected["secondary"])
        # bg1/bg2 are what the page's gradient variables bind to.
        self.assertEqual(config["bg1"], expected["bg_body"])
        self.assertEqual(config["bg2"], expected["bg_card"])

    def test_dark_preset_reports_dark_mode(self):
        with settings_patched(color_mode="Theme Preset", active_preset="Black Panther"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], True)
        with settings_patched(color_mode="Theme Preset", active_preset="Captain America"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], False)

    ROLES = ("canvas", "surface", "surface_alt", "on_canvas", "on_surface",
             "muted", "border", "primary", "secondary", "tint", "on_primary")

    def test_every_preset_defines_every_role(self):
        """A theme is a palette. One colour with shades derived from it is
        what made every preset read as a single flat tint."""
        for name, data in PREMIUM_THEMES.items():
            missing = [r for r in self.ROLES if r not in data["roles"]]
            self.assertEqual(missing, [], f"preset {name} is missing roles: {missing}")
            self.assertIn(data["mode"], ("light", "dark"), f"preset {name} has no valid mode")
            self.assertTrue(data.get("slug"), f"preset {name} has no slug")

    def test_dark_presets_lift_the_card_above_the_canvas(self):
        """In a dark UI elevation comes from light, not shadow. A card darker
        than the page sinks into it."""
        from swift_theme.scripts.colour import luminance

        for name, data in PREMIUM_THEMES.items():
            if data["mode"] != "dark":
                continue
            r = data["roles"]
            self.assertGreater(
                luminance(r["surface"]), luminance(r["canvas"]),
                f"{name}: card {r['surface']} is darker than canvas {r['canvas']}",
            )

    def test_text_is_legible_on_every_surface(self):
        """on_surface is computed per surface, not one global text colour."""
        from swift_theme.scripts.colour import contrast

        for name, data in PREMIUM_THEMES.items():
            r = data["roles"]
            for text, bg, label in ((r["on_surface"], r["surface"], "card"),
                                    (r["on_canvas"], r["canvas"], "page"),
                                    (r["on_primary"], r["primary"], "accent")):
                ratio = contrast(text, bg)
                self.assertGreaterEqual(
                    ratio, 4.5, f"{name}: text on {label} is {ratio:.1f}:1, below 4.5:1")

    def test_on_primary_picks_the_better_of_black_or_white(self):
        """A luminance cut-off put white on gold, at 2.2:1."""
        from swift_theme.scripts.colour import readable_on

        for name, data in PREMIUM_THEMES.items():
            r = data["roles"]
            self.assertEqual(
                r["on_primary"], readable_on(r["primary"]),
                f"{name}: on_primary does not contrast best on {r['primary']}")

    def test_every_shipped_stylesheet_belongs_to_a_preset(self):
        """Renaming presets leaves the old files behind unless they are removed,
        and an orphan stylesheet is dead weight that can still be requested."""
        shipped = {n[:-4] for n in os.listdir(os.path.join(CSS_DIR, "themes"))
                   if n.endswith(".css")}
        expected = {d["slug"] for d in PREMIUM_THEMES.values()}
        self.assertEqual(shipped, expected, f"orphans: {sorted(shipped - expected)}")

    def test_renamed_presets_are_carried_over(self):
        """active_preset stores the name. Without a mapping every site holding
        an old name silently drops to the default on upgrade."""
        from swift_theme.patches.v1_0.rename_presets_to_marvel import RENAMED

        # The module existing is not enough — an unregistered patch never runs.
        registered = frappe.get_file_items(frappe.get_app_path(APP, "patches.txt"))
        self.assertIn(
            "swift_theme.patches.v1_0.rename_presets_to_marvel", registered,
            "the rename patch is not listed in patches.txt, so it will never run")

        for old, new in RENAMED.items():
            self.assertNotIn(old, PREMIUM_THEMES, f"{old} is still a live preset")
            self.assertIn(new, PREMIUM_THEMES, f"{old} maps to {new}, which does not exist")

    def test_user_preset_options_are_repaired_not_just_created(self):
        """_ensure_user_fields skipped any field that already existed, so a
        rename left swift_preset holding the retired options for ever.

        Asserting the current options would pass on a database an earlier
        migrate had already fixed, so this puts stale options back first and
        checks the installer repairs them.
        """
        from swift_theme.install import _ensure_user_fields

        name = frappe.db.get_value(
            "Custom Field", {"dt": "User", "fieldname": "swift_preset"}, "name")
        self.assertTrue(name, "swift_preset custom field is missing")

        field = frappe.get_doc("Custom Field", name)
        good = field.options
        try:
            field.options = "\nSwift Blue\nMidnight Pro"      # the retired list
            field.save(ignore_permissions=True)
            frappe.clear_cache(doctype="User")

            _ensure_user_fields()
            frappe.clear_cache(doctype="User")

            options = frappe.get_meta("User").get_field("swift_preset").options.split("\n")
            for preset in PREMIUM_THEMES:
                self.assertIn(preset, options, f"{preset} was not restored")
            stale = [o for o in options if o and o not in PREMIUM_THEMES]
            self.assertEqual(stale, [], f"retired presets still offered: {stale}")
        finally:
            field = frappe.get_doc("Custom Field", name)
            field.options = good
            field.save(ignore_permissions=True)
            frappe.clear_cache(doctype="User")

    def test_presets_are_the_marvel_set(self):
        expected = {
            "Iron Man", "Captain America", "Doctor Strange", "Star-Lord",
            "Vision", "Scarlet Witch", "Black Panther", "Loki", "Hulk",
            "Thanos", "Venom", "Winter Soldier",
        }
        self.assertEqual(set(PREMIUM_THEMES), expected)
        modes = [d["mode"] for d in PREMIUM_THEMES.values()]
        self.assertEqual(modes.count("light"), 6, "six light presets expected")
        self.assertEqual(modes.count("dark"), 6, "six dark presets expected")

    def test_stylesheets_match_the_palette(self):
        """themes/*.css is generated; a hand edit or a stale file is a bug."""
        import subprocess
        import sys

        script = frappe.get_app_path(APP, "scripts", "generate_theme_css.py")
        before = {n: open(os.path.join(CSS_DIR, "themes", n)).read()
                  for n in sorted(os.listdir(os.path.join(CSS_DIR, "themes")))}
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = {n: open(os.path.join(CSS_DIR, "themes", n)).read()
                 for n in sorted(os.listdir(os.path.join(CSS_DIR, "themes")))}
        stale = [n for n in after if before.get(n) != after[n]]
        self.assertEqual(stale, [], f"regenerating changed {stale} — commit the rebuild")

    def test_custom_colors_mode_returns_the_chosen_pair(self):
        with settings_patched(
            color_mode="Custom Colors", primary_color="#111111", secondary_color="#222222"
        ):
            config = get_active_theme_config()
        self.assertEqual(config["primary"], "#111111")
        self.assertEqual(config["secondary"], "#222222")
        self.assertIsNone(config["preset"], "custom colours load no preset stylesheet")

    def test_custom_colors_mode_requires_both_colours(self):
        with self.assertRaises(frappe.ValidationError):
            with settings_patched(
                color_mode="Custom Colors", primary_color="#111111", secondary_color=""
            ):
                pass

    def test_apply_theme_writes_a_valid_desk_theme(self):
        """desk_theme options are Light/Dark/Automatic — lowercase was invalid."""
        user = frappe.session.user
        previous = frappe.db.get_value("User", user, ["desk_theme", "swift_preset"], as_dict=True)
        try:
            apply_theme("Black Panther")
            stored = frappe.db.get_value("User", user, "desk_theme")
            options = frappe.get_meta("User").get_field("desk_theme").options.split("\n")
            self.assertIn(stored, options)
            self.assertEqual(frappe.db.get_value("User", user, "swift_preset"), "Black Panther")
        finally:
            # swift_preset overrides the site preset, so leaving it set would
            # leak into every other test that reads the effective preferences.
            frappe.db.set_value("User", user, dict(previous))

    def test_apply_theme_rejects_an_unknown_theme(self):
        with self.assertRaises(frappe.ValidationError):
            apply_theme("Not A Real Theme")


class TestSwiftThemeSounds(IntegrationTestCase):
    def test_play_sound_returns_nothing_when_no_file_is_attached(self):
        """It used to return /assets/.../save.mp3 for files that don't exist."""
        with settings_patched(enable_sounds=1, volume_level=50):
            result = play_sound("save")
        self.assertTrue(result["enabled"])
        self.assertIsNone(result["sound_file"])

    def test_play_sound_scales_volume_to_zero_one(self):
        with settings_patched(enable_sounds=1, volume_level=40):
            self.assertAlmostEqual(play_sound("save")["volume"], 0.4)

    def test_play_sound_is_silent_when_sounds_are_disabled(self):
        with settings_patched(enable_sounds=0):
            result = play_sound("save")
        self.assertFalse(result["enabled"])
        self.assertIsNone(result["sound_file"])

    def test_volume_outside_zero_to_hundred_is_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            with settings_patched(enable_sounds=1, volume_level=900):
                pass

    def test_play_sound_uses_an_attached_file(self):
        with self.sound_events([{"event_key": "save", "sound_file": "/files/ping.mp3"}]):
            self.assertEqual(play_sound("save")["sound_file"], "/files/ping.mp3")

    def test_boot_config_lists_only_events_with_a_file(self):
        rows = [
            {"event_key": "save", "sound_file": "/files/ping.mp3"},
            {"event_key": "error", "sound_file": None},
        ]
        with self.sound_events(rows):
            files = get_effective_prefs()["sounds"]["files"]
        self.assertEqual(files, {"save": "/files/ping.mp3"})

    def test_duplicate_event_keys_are_rejected(self):
        rows = [
            {"event_key": "save", "sound_file": "/files/a.mp3"},
            {"event_key": "save", "sound_file": "/files/b.mp3"},
        ]
        with self.assertRaises(frappe.ValidationError):
            with self.sound_events(rows):
                pass

    @contextmanager
    def sound_events(self, rows):
        doc = frappe.get_single("Swift Theme Settings")
        previous_rows = [r.as_dict() for r in (doc.sound_events or [])]
        previous_enabled = doc.enable_sounds
        try:
            doc.enable_sounds = 1
            doc.set("sound_events", [])
            for row in rows:
                doc.append("sound_events", row)
            doc.save(ignore_permissions=True)
            frappe.clear_cache()
            yield doc
        finally:
            doc = frappe.get_single("Swift Theme Settings")
            doc.enable_sounds = previous_enabled
            doc.set("sound_events", [])
            for row in previous_rows:
                doc.append("sound_events", row)
            doc.save(ignore_permissions=True)
            frappe.clear_cache()


class TestSwiftThemeBackdrops(IntegrationTestCase):
    """The stylesheet existed for a while but was wired to nothing."""

    SHIPPED = {"aurora", "mesh", "grain", "facets", "silk", "none"}

    def test_stylesheet_is_actually_loaded(self):
        for hook in ("app_include_css", "web_include_css"):
            self.assertIn(
                "swift-backdrops.css", loaded_assets(hook),
                f"backdrops.css is not in {hook}, so none of it ever applies")

    def test_every_offered_backdrop_has_a_rule(self):
        """A Settings option with no CSS behind it silently does nothing."""
        css = read_css("swift-backdrops.css")
        for option in settings_json_options("backdrop"):
            key = option.lower()
            self.assertIn(key, self.SHIPPED, f"{option} is not a shipped backdrop")
            self.assertIn(f'data-swift-backdrop="{key}"', css,
                          f"{option} is selectable but has no rule")

    def test_every_preset_ships_a_backdrop(self):
        from swift_theme.api.boot import BACKDROPS

        for name, data in PREMIUM_THEMES.items():
            self.assertIn(data.get("backdrop"), BACKDROPS,
                          f"{name} has no valid default backdrop")

    DESK_CSS = ("swift-preset-base.css", "swift-backdrops.css",
                "swift-desk.css", "swift-perf.css")

    def test_perf_mode_does_not_erase_the_backdrop(self):
        """Perf mode ships on, so whatever it does to the backdrop is what
        everyone sees.

        `html[data-swift-perf="on"] body::before { background: var(--bg-color) }`
        replaced all six backdrops with a flat colour on every stock install,
        and no test caught it because each stylesheet was only ever checked on
        its own — the damage was one file overriding another.
        """
        offenders = []
        for filename in self.DESK_CSS:
            for selector, declarations in css_rules(filename):
                if 'data-swift-perf="on"' not in selector:
                    continue
                if not selects_the_backdrop(selector):
                    continue
                if re.search(r"(^|;)\s*background(-image|-color)?\s*:", declarations):
                    offenders.append(f"{filename}: {selector}")

        self.assertEqual(
            offenders, [],
            "perf mode paints over the backdrop, so no preset shows one: "
            f"{offenders}")

    def test_perf_mode_does_not_stop_the_backdrop_moving(self):
        """Aurora and Silk are defined by their motion.

        Perf mode neutralised it — once by name and once through a blanket
        `*::before` rule — so the two animated backdrops were static for
        everybody. Motion is switched off by data-swift-anim="off" and by
        prefers-reduced-motion; those are the two that should own the decision.
        """
        offenders = []
        for filename in self.DESK_CSS:
            for selector, declarations in css_rules(filename):
                if 'data-swift-perf="on"' not in selector:
                    continue
                if not selects_the_backdrop(selector):
                    continue
                if re.search(r"(^|;)\s*animation(-\w+)?\s*:", declarations):
                    offenders.append(f"{filename}: {selector}")

        self.assertEqual(
            offenders, [],
            f"perf mode freezes the backdrop for every user: {offenders}")

    def test_animation_switch_still_stops_the_backdrop(self):
        """The counterpart: exempting the backdrop from perf must not have
        exempted it from the switch that genuinely means "no motion"."""
        stoppers = [
            selector
            for filename in self.DESK_CSS
            for selector, declarations in css_rules(filename)
            if 'data-swift-anim="off"' in selector
            and selects_the_backdrop(selector)
            and re.search(r"(^|;)\s*animation(-\w+)?\s*:\s*none", declarations)
        ]
        self.assertTrue(
            stoppers,
            "nothing stops the backdrop animating when animation is turned off")

    def test_each_preset_carries_its_own_backdrop(self):
        """The backdrop is part of a preset's identity, not a global setting.

        Picking a preset must bring its backdrop with it, so switching preset
        visibly changes the background treatment and not just the hues.
        """
        from swift_theme.api.boot import resolve_backdrop

        for name, data in PREMIUM_THEMES.items():
            self.assertEqual(
                resolve_backdrop(None, data.get("backdrop")), data.get("backdrop"),
                f"{name} does not get its own backdrop when Settings leaves it blank")

    def test_every_stylesheet_is_actually_loaded(self):
        """A stylesheet nobody loads is dead weight that looks alive.

        The companion test checks the other direction — that hooks do not name
        files which are missing. This one catches a file that exists, is
        maintained, and is simply never served: dropping swift-sidebar.css from
        the hooks would strip the sidebar of every rule and no test noticed.

        Two are loaded outside the hooks and say so here, so the exemption is
        deliberate rather than a hole.
        """
        css_dir = frappe.get_app_path(APP, "public", "css")
        on_disk = {n for n in os.listdir(css_dir)
                   if n.endswith(".css") and ".bundle." not in n}

        hooked = set()
        for hook in ("app_include_css", "web_include_css"):
            hooked.update(loaded_assets(hook))

        # swift-print.css is pulled in by the print block, which builds its own
        # document and shares nothing with the desk or the portal.
        ELSEWHERE = {"swift-print.css"}
        for name in ELSEWHERE:
            self.assertIn(name, on_disk, f"{name} is exempted but no longer exists")

        orphans = sorted(on_disk - hooked - ELSEWHERE)
        self.assertEqual(
            orphans, [],
            f"these stylesheets ship but are never loaded: {orphans}")

    def test_every_styled_attribute_is_actually_written(self):
        """CSS keyed on an attribute nobody sets is CSS that never runs.

        This is the failure this app keeps hitting, so check it in general
        rather than one attribute at a time. The whole of swift-website.css was
        gated on html[data-swift-accent], which no script and no template has
        ever set — the portal took the fonts and the backdrop and none of the
        colour, and every rule in the file was inert.
        """
        used = set()
        for name in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
            for selector, _declarations in css_rules(name):     # comments stripped
                used.update(re.findall(r"data-swift-[a-z-]+", selector))

        written = set()
        js_dir = frappe.get_app_path(APP, "public", "js")
        sources = [os.path.join(js_dir, n) for n in os.listdir(js_dir) if n.endswith(".js")]
        for path in sources:
            with open(path) as handle:
                body = handle.read()
            written.update(re.findall(r"data-swift-[a-z-]+", body))
            # applyAttr("sidebar-fill", …) writes data-swift-sidebar-fill
            written.update(f"data-swift-{m}"
                           for m in re.findall(r'applyAttr\(\s*"([a-z-]+)"', body))

        orphans = sorted(used - written)
        self.assertEqual(
            orphans, [],
            f"these attributes are styled but never set, so the rules behind "
            f"them can never match: {orphans}")

    def test_sidebar_and_navbar_variants_work_end_to_end(self):
        """Every value of all three settings, through the whole chain.

        Each of these has failed at a different link before: navbar_variant
        styled an element the v16 desk does not render, sidebar_variant styled
        the per-page filter panel instead of the navigation sidebar, and
        sidebar_brand_fill was missing from the payload the client reloads. So
        walk every value across every link rather than trusting any one of them.
        """
        meta = frappe.get_meta("Swift Theme Settings")
        CHAIN = {
            # setting: (attribute the client writes, values to walk)
            "navbar_variant": "navbar",
            "sidebar_variant": "sidebar-variant",
            "sidebar_brand_fill": "sidebar-fill",
        }
        boot_js = read_js("swift-boot.js")
        every_sheet = read_css()

        # This test writes real values to a Single, and a Single is not rolled
        # back with the transaction — running the suite turned the admin's
        # brand fill off and left it off. Put back whatever was there.
        restore = {f: frappe.db.get_single_value("Swift Theme Settings", f)
                   for f in CHAIN}

        def put_back():
            for fieldname, value in restore.items():
                frappe.db.set_single_value("Swift Theme Settings", fieldname, value)
            frappe.db.commit()      # nosemgrep: frappe-manual-commit
            frappe.clear_cache()

        self.addCleanup(put_back)

        for fieldname, attribute in CHAIN.items():
            field = meta.get_field(fieldname)
            self.assertIsNotNone(field, f"{fieldname} is not a field any more")

            if field.fieldtype == "Check":
                values = [0, 1]
            else:
                values = [o.strip() for o in (field.options or "").split("\n") if o.strip()]
                self.assertTrue(values, f"{fieldname} offers no options")

            # 1. the client writes this attribute at all
            self.assertRegex(
                boot_js, rf'applyAttr\(\s*"{re.escape(attribute)}"',
                f"{fieldname} is stored and sent but the client never writes "
                f"data-swift-{attribute}, so no rule can ever match it")

            # 2. and writes it on a live reload, not only on first paint
            self.assertIn(
                fieldname, boot_js,
                f"the reload path ignores {fieldname}, so saving Settings "
                f"leaves the open desk on the previous value")

            for value in values:
                with self.subTest(setting=fieldname, value=value):
                    # 3. the server stores it and hands it back
                    frappe.db.set_single_value("Swift Theme Settings", fieldname, value)
                    frappe.clear_cache()
                    from swift_theme.api.boot import get_effective_prefs
                    prefs = get_effective_prefs()
                    self.assertIn(
                        fieldname, prefs,
                        f"{fieldname} never reaches the client")
                    self.assertEqual(
                        str(prefs[fieldname]), str(value),
                        f"{fieldname}={value!r} came back as {prefs[fieldname]!r}")

                    # 4. CSS exists for this exact value, and does something
                    if fieldname == "sidebar_brand_fill" and not value:
                        continue        # off is the unstyled default, by design
                    token = "brand" if fieldname == "sidebar_brand_fill" else value
                    rules = [(sel, decl) for name in sorted(os.listdir(CSS_DIR))
                             if name.endswith(".css")
                             for sel, decl in css_rules(name)
                             if f'data-swift-{attribute}="{token}"' in sel]
                    self.assertTrue(
                        rules,
                        f"{fieldname}={value!r} has no CSS at all, so choosing "
                        f"it changes nothing on screen")
                    self.assertTrue(
                        any(":" in decl for _sel, decl in rules),
                        f"{fieldname}={value!r} matches rules that declare "
                        f"nothing")

            self.assertIn(f'data-swift-{attribute}', every_sheet)

    def test_assets_are_served_from_a_hashed_bundle(self):
        """A raw /assets path never changes, so the browser never refetches it.

        Frappe hashes a filename only when the path contains ".bundle." and is
        not already under /assets — everything else is served from a URL that
        is identical release to release. Listing the files raw meant every
        upgrade left users on the previous release's CSS and JS: a fix could be
        shipped, built and deployed and still not reach the screen. Werkzeug
        serves /assets with a public max-age, and nginx with a longer one.
        """
        for hook, bundle in BUNDLES.items():
            entries = [e for e in (frappe.get_hooks(hook) or [])
                       if "swift" in e.lower()]
            self.assertEqual(
                entries, [bundle.replace(".scss", ".css")],
                f"{hook} does not serve a single hashed bundle")

            for entry in entries:
                self.assertNotIn(
                    "/assets/", entry,
                    f"{hook} lists {entry}, which Frappe serves verbatim: no "
                    f"hash, so a browser holds the old copy after an upgrade")
                self.assertIn(
                    ".bundle.", entry,
                    f"{hook} lists {entry}, which bundled_asset() will not "
                    f"rewrite, so it gets no content hash")

            # And the bundle has to name real files, or the import silently
            # drops a whole stylesheet from the page.
            folder = "css" if hook.endswith("css") else "js"
            for name in loaded_assets(hook):
                self.assertTrue(
                    os.path.exists(frappe.get_app_path(APP, "public", folder, name)),
                    f"{bundle} imports {name}, which does not exist")

    def test_every_script_is_actually_loaded(self):
        """The stylesheet check's twin. A script nobody loads is dead weight.

        Bundling made this reachable: the import list is a second place a file
        can be forgotten, and a script left out of it is as silent as one left
        out of the hooks used to be.
        """
        js_dir = frappe.get_app_path(APP, "public", "js")
        on_disk = {n for n in os.listdir(js_dir)
                   if n.endswith(".js") and ".bundle." not in n}

        hooked = set()
        for hook in ("app_include_js", "web_include_js"):
            hooked.update(loaded_assets(hook))

        # These are loaded by Frappe itself, not by our bundles: doctype_js and
        # the form scripts it names.
        ELSEWHERE = set()
        for scripts in (frappe.get_hooks("doctype_js") or {}).values():
            ELSEWHERE.update(s.rsplit("/", 1)[-1] for s in scripts)

        orphans = sorted(on_disk - hooked - ELSEWHERE)
        self.assertEqual(
            orphans, [],
            f"these scripts ship but are never loaded: {orphans}")

    def test_hooks_do_not_point_at_assets_that_are_not_shipped(self):
        """Every /assets path declared in hooks.py must resolve to a real file.

        A stylesheet naming a file that does not exist is a 404 on every page
        load, and that already happened once with an optional Inter font. The
        same mistake in app_logo_url or an include list is a broken icon on the
        marketplace listing, or a stylesheet that silently never loads.
        """
        app_path = frappe.get_app_path(APP)
        declared = []
        for hook in ("app_include_css", "app_include_js",
                     "web_include_css", "web_include_js", "app_logo_url"):
            value = frappe.get_hooks(hook) or []
            declared.extend(value if isinstance(value, list) else [value])

        missing = []
        for path in declared:
            if not isinstance(path, str) or not path.startswith("/assets/swift_theme/"):
                continue
            relative = path[len("/assets/swift_theme/"):]
            if not os.path.exists(os.path.join(app_path, "public", relative)):
                missing.append(path)

        self.assertEqual(
            missing, [], f"hooks.py points at files that do not ship: {missing}")

    def test_no_stylesheet_asks_for_an_asset_that_is_not_shipped(self):
        """A url to a file the app does not ship is a 404 on every page load.

        swift-fonts.css named an optional local Inter that has never been in
        the repo, so every install fetched it and failed before falling through
        to the CDN.
        """
        app_path = frappe.get_app_path(APP)
        missing = []
        for name in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
            for url in re.findall(r"/assets/swift_theme/([A-Za-z0-9._/-]+)",
                                  read_css(name)):
                if not os.path.exists(os.path.join(app_path, "public", url)):
                    missing.append(f"{name} -> {url}")

        self.assertEqual(
            missing, [], f"these stylesheets point at files that do not ship: {missing}")

    def test_settings_preview_keeps_the_backdrop(self):
        """The live preview must pass the backdrop, not just the colours.

        applyColors clears data-swift-backdrop when the value is blank, so a
        preview that omitted it flattened the background the moment the preset
        dropdown was touched, and only a page reload brought it back.
        """
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "swift_theme_settings.js")
        with open(path) as f:
            js = f.read()

        preview = js.split("function previewColors", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn(
            "backdrop: chosen.backdrop", preview,
            "the preset preview drops the backdrop, so previewing flattens it")

    def test_every_switcher_surface_honours_the_setting(self):
        """Enable Theme Switcher has to reach all three places it appears.

        The navbar chip checked it; the section injected into Frappe's own
        Switch Theme dialog and the command palette did not, so turning the
        switcher off left two ways to change the theme still standing.
        """
        surfaces = {
            "swift-switcher.js": "the navbar chip",
            "swift-theme-dialog.js": "the Switch Theme dialog",
            "swift-palette.js": "the command palette",
        }
        for filename, what in surfaces.items():
            js = read_js(filename)
            self.assertIn(
                "enable_switcher", js,
                f"{what} ignores Enable Theme Switcher, so turning it off "
                f"still leaves a way in")

    def test_theme_sounds_replace_frappes_own(self):
        """Saving made two noises: Frappe's click, then ours.

        form.js calls frappe.utils.play_sound("click") on every save, so with
        the theme's sound engine on you heard both. Wrapped rather than
        removed, and checked per call, so switching sounds off in Settings
        hands Frappe's own back without a reload.
        """
        js = read_js("swift-sounds.js")
        wrapper = js.split("function silenceFrappesOwnSounds", 1)
        self.assertEqual(len(wrapper), 2,
                         "nothing intercepts Frappe's own sounds, so save double-plays")
        body = wrapper[1].split("\n    }", 1)[0]
        self.assertIn("__frappeOriginal", body,
                      "Frappe's own function must be kept, not thrown away")
        self.assertIn("cfg.enabled", body,
                      "the check must be per call, or the setting needs a reload")
        self.assertIn("original.apply", body,
                      "Frappe's sounds must come back when the theme's are off")
        self.assertIn("cfg.files", body,
                      "suppression must depend on the theme actually having a "
                      "file, or ticking Sounds silences a desk that ships no audio")

    def test_backdrop_switches_are_reachable_in_every_colour_mode(self):
        """Both switches govern Theme Preset and Custom Colors alike.

        They were first placed beside the Backdrop select, inside
        custom_colors_section — and a section's depends_on hides everything in
        it, so picking a preset made both checkboxes disappear with no way to
        reach them.
        """
        meta = frappe.get_meta("Swift Theme Settings")
        fields = {f.fieldname: f for f in meta.fields}
        order = [f.fieldname for f in meta.fields]

        for name in ("enable_backdrops", "show_backdrop_through"):
            section = None
            for fieldname in order[:order.index(name)]:
                if fields[fieldname].fieldtype in ("Section Break", "Tab Break"):
                    section = fields[fieldname]

            gates = [fields[name].depends_on or "", (section.depends_on or "") if section else ""]
            self.assertNotIn(
                "color_mode", " ".join(gates),
                f"{name} is hidden by colour mode"
                + (f" via section {section.fieldname}" if section else ""))

    # Containers that span the viewport. Painting any of these opaquely hides
    # the backdrop completely, however correctly it was drawn.
    FULL_PAGE = (".layout-main-section", ".layout-main-section-wrapper",
                 ".layout-main", ".desk-body", ".page-container")

    def test_nothing_full_page_paints_over_the_backdrop(self):
        """The backdrop was wired end to end and still invisible.

        `.layout-main-section` was painted with var(--card-bg) on every route,
        so a full-page opaque slab sat on top of it. Frappe itself only paints
        that container on Workspaces; doing it everywhere was ours.
        """
        offenders = []
        for filename in ("swift-preset-base.css", "swift-desk.css", "swift-layout.css"):
            for selector, declarations in css_rules(filename):
                if 'data-swift-backdrop="none"' in selector:
                    continue                      # no backdrop to hide
                target = selector.split("{")[0]
                if not any(c in target for c in self.FULL_PAGE):
                    continue
                match = re.search(
                    r"(^|;)\s*background(-color)?\s*:\s*([^;]+)", declarations)
                if not match:
                    continue
                value = match.group(3).strip()
                if value.startswith("transparent") or value.startswith("none"):
                    continue
                offenders.append(f"{filename}: {target} -> {value[:40]}")

        self.assertEqual(
            offenders, [],
            f"these cover the whole page, so no backdrop can be seen: {offenders}")

    def test_backdrops_switch_off_when_the_feature_is_off(self):
        """The feature is one checkbox, and off has to mean off."""
        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki",
                                  enable_backdrops=0):
                prefs = get_effective_prefs()
        self.assertEqual(
            prefs["backdrop"], "none",
            "the preset's backdrop is still being drawn with the feature off")

        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki",
                                  enable_backdrops=1):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["backdrop"], PREMIUM_THEMES["Loki"]["backdrop"])

    def test_show_through_reaches_the_client(self):
        for value in (0, 1):
            with settings_patched(enable_backdrops=1, show_backdrop_through=value):
                prefs = get_effective_prefs()
            self.assertEqual(
                prefs["show_backdrop_through"], value,
                "the desk cannot apply a switch it is never told about")

    def test_show_through_cannot_outlive_the_feature(self):
        """Its field is hidden when backdrops are off, so it must stop too.

        Otherwise a stored 1 keeps the desk translucent with no control left in
        the form to switch it back.
        """
        with settings_patched(enable_backdrops=0, show_backdrop_through=1):
            prefs = get_effective_prefs()
        self.assertEqual(
            prefs["show_backdrop_through"], 0,
            "translucent surfaces survive with the feature off and no way back")

    def test_show_through_has_css_behind_it(self):
        """Both switches must reach CSS, or the checkbox does nothing."""
        css = read_css("swift-glass.css")
        self.assertIn('html[data-swift-glass="on"]', css)
        for token in ("--card-bg", "--sidebar-bg", "--navbar-bg"):
            self.assertIn(token, css, f"{token} stays opaque, so panels still hide it")

    def test_glass_stylesheet_is_loaded_after_the_desk(self):
        """It answers swift-desk.css, so it has to come after it."""
        for hook in ("app_include_css", "web_include_css"):
            sheets = loaded_assets(hook)
            self.assertIn("swift-glass.css", sheets,
                          f"swift-glass.css is not in {hook}, so it never applies")
        desk = loaded_assets("app_include_css").index("swift-desk.css")
        glass = loaded_assets("app_include_css").index("swift-glass.css")
        self.assertGreater(glass, desk, "swift-desk.css would override the glass tokens")

    def test_glass_never_creates_a_containing_block(self):
        """The constraint that broke the child-table editor twice already.

        backdrop-filter and filter make an element the containing block for its
        position:fixed descendants, and the grid row editor is exactly that.
        """
        css = read_css("swift-glass.css")
        for prop in ("backdrop-filter", "-webkit-backdrop-filter", "filter:"):
            self.assertNotIn(
                prop, css,
                f"{prop} in the glass layer would trap the child-table editor")

    def test_overlays_stay_opaque_when_glass_is_on(self):
        """A translucent dropdown over a moving backdrop cannot be read."""
        css = read_css("swift-glass.css")
        for selector in (".modal-content", ".dropdown-menu", ".form-in-grid"):
            self.assertIn(selector, css, f"{selector} would be left see-through")

    def test_every_preset_has_its_own_backdrop(self):
        """The backdrop is meant to say which preset you are looking at.

        Five generic treatments shared twelve ways meant Doctor Strange,
        Scarlet Witch and Thanos were the same background in three hues.
        """
        used = {name: data.get("backdrop") for name, data in PREMIUM_THEMES.items()}
        duplicates = {b for b in used.values() if list(used.values()).count(b) > 1}
        self.assertEqual(
            duplicates, set(),
            f"these backdrops are shared by more than one preset: {duplicates}")

    def test_character_backdrops_are_actually_drawn(self):
        """A preset pointing at a backdrop with no CSS shows a flat colour.

        Checking for the key anywhere in the file was not enough: a backdrop
        whose colour field had been deleted still passed on the strength of its
        leftover texture rule, so this asks for the ::before layer by name.
        """
        selectors = {selector for selector, _ in css_rules("swift-backdrops.css")}
        for name, data in PREMIUM_THEMES.items():
            key = data.get("backdrop")
            wanted = f'html[data-swift-backdrop="{key}"] body::before'
            self.assertTrue(
                any(wanted in selector for selector in selectors),
                f"{name} asks for the {key!r} backdrop, but nothing paints it")

    def test_character_backdrops_are_registered(self):
        """resolve_backdrop drops anything not in BACKDROPS back to "none"."""
        from swift_theme.api.boot import BACKDROPS

        for name, data in PREMIUM_THEMES.items():
            self.assertIn(
                data.get("backdrop"), BACKDROPS,
                f"{name}'s backdrop is not registered, so it resolves to none")

    def test_custom_colors_only_offers_the_generic_backdrops(self):
        """A character backdrop belongs to its preset, not to a dropdown."""
        from swift_theme.api.boot import GENERIC_BACKDROPS

        for option in settings_json_options("backdrop"):
            self.assertIn(
                option.lower(), GENERIC_BACKDROPS,
                f"{option} is a preset's own backdrop and should not be selectable")

    def test_preset_mode_ignores_the_settings_backdrop(self):
        """In preset mode the preset owns the backdrop.

        Otherwise one stored choice sits over all twelve and every preset looks
        the same behind the content, which defeats shipping a treatment per
        preset in the first place.
        """
        from swift_theme.api.boot import resolve_backdrop

        self.assertEqual(
            resolve_backdrop("Silk", "aurora", is_preset=True), "aurora",
            "a stored backdrop is overriding the preset's own")
        self.assertEqual(resolve_backdrop(None, "grain", is_preset=True), "grain")
        self.assertEqual(resolve_backdrop("Mesh", None, is_preset=True), "none")

    def test_custom_colors_still_choose_their_own_backdrop(self):
        """Custom Colors has no preset to speak for it, so Settings decides."""
        from swift_theme.api.boot import resolve_backdrop

        self.assertEqual(resolve_backdrop("Silk", "aurora"), "silk", "Settings must win")
        self.assertEqual(resolve_backdrop("", "aurora"), "aurora", "blank falls back")
        self.assertEqual(resolve_backdrop(None, "grain"), "grain")
        self.assertEqual(resolve_backdrop("nonsense", "mesh"), "mesh", "junk falls back")
        self.assertEqual(resolve_backdrop("", None), "none")

    def test_backdrop_reaches_the_client(self):
        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki",
                                  backdrop=""):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["backdrop"], PREMIUM_THEMES["Loki"]["backdrop"])
        self.assertEqual(prefs["backdrop_pinned"], 0)

        # A leftover Settings choice must not sit over the preset's own.
        with no_user_preset():
            with settings_patched(color_mode="Theme Preset", active_preset="Loki",
                                  backdrop="Facets"):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["backdrop"], PREMIUM_THEMES["Loki"]["backdrop"])
        self.assertEqual(prefs["backdrop_pinned"], 0)

    def test_custom_colors_backdrop_reaches_the_client(self):
        """With no preset in play, the Settings choice is the one that ships."""
        with no_user_preset():
            with settings_patched(color_mode="Custom Colors", primary_color="#39e4a5",
                                  secondary_color="#7c3aed", backdrop="Facets"):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["backdrop"], "facets")
        self.assertEqual(prefs["backdrop_pinned"], 1)

    def test_boot_js_applies_the_attribute(self):
        js = read_js("swift-boot.js")
        self.assertIn('applyAttr("backdrop"', js)

    def test_motion_belongs_to_the_backdrop_only(self):
        """preset-base animated the same layer, so a still backdrop such as
        Mesh inherited a drift it never asked for."""
        base = read_css("swift-preset-base.css")
        self.assertNotIn("swift-ambient-drift", base)
        css = read_css("swift-backdrops.css")
        for still in ("mesh", "grain", "facets"):
            block = css.split(f'data-swift-backdrop="{still}"] body::before {{', 1)[1].split("}", 1)[0]
            self.assertIn("animation: none", block, f"{still} does not stop the motion")

    def test_backdrops_use_only_theme_colours(self):
        """A hardcoded hue would ignore the preset and the custom pair alike."""
        css = read_css("swift-backdrops.css")
        hues = re.findall(r"#[0-9a-fA-F]{6}", css)
        self.assertEqual([h for h in hues if h.lower() != "#000000"], [],
                         "backdrops must build from --swift-primary/--swift-secondary")

    def test_backdrop_layers_cannot_trap_the_desk(self):
        """Same rule as everywhere else: nothing behind the desk may become a
        containing block for the position:fixed child-table editor."""
        css = read_css("swift-backdrops.css")
        block = css.split("body::before,", 1)[1].split("}", 1)[0]
        self.assertIn("z-index: -1", block)
        self.assertIn("pointer-events: none", block)


class TestSwiftThemeStyling(IntegrationTestCase):
    """Options and injected elements must have styling that actually exists."""

    def test_every_layout_option_has_a_css_rule(self):
        """Options like "Minimal"/"Bordered" existed with no styling behind them.

        Reads every stylesheet rather than one: what matters is that the option
        is styled at all, and pinning it to a filename made this fail the day
        the sidebar rules moved to a file of their own.
        """
        css = "".join(
            read_css(n) for n in sorted(os.listdir(CSS_DIR)) if n.endswith(".css"))
        for fieldname, attr in (
            ("sidebar_variant", "data-swift-sidebar-variant"),
            ("navbar_variant", "data-swift-navbar"),
        ):
            for option in settings_json_options(fieldname):
                self.assertIn(
                    f'{attr}="{option}"', css, f"{fieldname} option {option!r} has no CSS rule"
                )

    def test_every_preset_ships_its_own_stylesheet(self):
        """Each preset is a separate file so only the active one is loaded."""
        from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
            preset_stylesheet,
        )

        for name, data in PREMIUM_THEMES.items():
            slug = data["slug"]
            path = frappe.get_app_path(APP, "public", "css", "themes", f"{slug}.css")
            self.assertTrue(os.path.exists(path), f"{name} has no stylesheet at {path}")
            self.assertIsNotNone(preset_stylesheet(slug))

            body = COMMENT_RE.sub("", open(path).read())
            self.assertIn(f'html[data-swift-preset="{slug}"]', body)
            # A preset file must not style any other preset.
            for other in PREMIUM_THEMES.values():
                if other["slug"] != slug:
                    self.assertNotIn(f'data-swift-preset="{other["slug"]}"', body)

    def test_preset_dropdown_matches_the_shipped_stylesheets(self):
        """A preset offered in Settings with no file would silently do nothing."""
        for option in settings_json_options("active_preset"):
            self.assertIn(option, PREMIUM_THEMES, f"{option!r} is not a known preset")
            slug = PREMIUM_THEMES[option]["slug"]
            self.assertTrue(
                os.path.exists(frappe.get_app_path(APP, "public", "css", "themes", f"{slug}.css")),
                f"preset {option!r} is selectable but ships no stylesheet",
            )

    def test_desk_views_use_no_undefined_colour_variables(self):
        """The bug: list, report, kanban and dashboards ignored the theme.

        They read --accent-color / --accent-light / --accent-dark / --bg-light,
        which neither a preset nor Frappe ever defines, so every theme rendered
        the same hardcoded blue and dark themes got light-grey report rows.
        """
        ours = set()
        for name in os.listdir(CSS_DIR):
            if name.endswith(".css"):
                ours |= set(re.findall(
                    r"^\s*(--[a-z0-9-]+)\s*:", open(os.path.join(CSS_DIR, name)).read(), re.M))
        theme_dir = os.path.join(CSS_DIR, "themes")
        for name in os.listdir(theme_dir):
            ours |= set(re.findall(
                r"^\s*(--[a-z0-9-]+)\s*:", open(os.path.join(theme_dir, name)).read(), re.M))

        frappe_css = ""
        scss_root = frappe.get_app_path("frappe", "public", "scss")
        for root, _dirs, files in os.walk(scss_root):
            for name in files:
                if name.endswith(".scss"):
                    frappe_css += open(os.path.join(root, name), errors="ignore").read()
        frappe_defined = set(re.findall(r"^\s*(--[a-z0-9-]+)\s*:", frappe_css, re.M))

        css = read_css("swift-desk.css")
        # Only flag var() with no fallback — those render as nothing at all.
        undefined = sorted(
            v for v in set(re.findall(r"var\(\s*(--[a-z0-9-]+)\s*\)", css))
            if v not in ours and v not in frappe_defined
        )
        self.assertEqual(undefined, [], f"swift-desk.css relies on undefined variables: {undefined}")

    def test_no_themed_rule_hardcodes_a_hue(self):
        """A literal colour inside a [data-swift-themed] rule ignores the theme.

        This was scoped to swift-desk.css and so missed preset-base, where the
        number-card figures cycled through six fixed gradients whatever preset
        was active — on top of a card the theme had already coloured.

        Neutrals are allowed: pure black and white are used for shadows and
        highlight overlays, not as brand colour.
        """
        NEUTRAL = {"#000000", "#ffffff", "#fff", "#000"}
        offenders = []
        for name in sorted(os.listdir(CSS_DIR)):
            if not name.endswith(".css") or name in ("login.css", "swift-base.css"):
                continue
            src = COMMENT_RE.sub("", open(os.path.join(CSS_DIR, name)).read())
            for block in re.finditer(r"([^{}]*)\{([^{}]*)\}", src):
                selector, body = block.group(1), block.group(2)
                themed = ("data-swift-themed" in selector or "data-swift-preset" in selector)
                # :not([data-swift-themed]) is the no-theme fallback — there is
                # no palette to read from there, so a literal is correct.
                if not themed or ":not([data-swift-themed]" in selector:
                    continue
                for hue in re.findall(r"#[0-9a-fA-F]{3,6}\b", body):
                    if hue.lower() not in NEUTRAL:
                        offenders.append(f"{name}: {selector.strip()[:48]!r} -> {hue}")
        self.assertEqual(offenders[:8], [], f"{len(offenders)} hardcoded hues: {offenders[:8]}")

    def test_themed_views_do_not_hardcode_the_old_blue(self):
        css = read_css("swift-desk.css")
        for dead in ("--accent-color,", "--accent-light", "--accent-dark", "--bg-light"):
            self.assertNotIn(dead, css, f"{dead} is not defined by any theme")
        self.assertNotIn("#0b84f3", css, "hardcoded blue ignores the active theme")

    def test_report_and_dashboard_follow_the_theme(self):
        css = read_css("swift-desk.css")
        for selector in (".dt-header", ".dt-cell", ".number-card", ".widget", ".kanban-column"):
            self.assertIn(selector, css, f"{selector} has no themed rule")
        # Text sitting on the accent must use the computed on-accent colour.
        self.assertIn("--swift-accent-fg", css)

    def test_number_cards_and_widget_heads_do_not_wash_the_whole_tile(self):
        """A dashboard is several of these next to each other, not one hero card.

        Both used to be painted with a full linear-gradient(primary, secondary)
        wall to wall — every widget header the same loud stripe, every number
        card the same bright tile — which is fine once and garish repeated five
        times on one screen. The pair now shows as a slim accent (a left border,
        a top bar, the figure's own text) on the theme's normal card surface, so
        a dashboard full of these reads as one design, not a wall of colour.
        """
        for filename in ("swift-preset-base.css", "swift-desk.css"):
            for selector, declarations in css_rules(filename):
                target = selector.split("{")[0]
                is_number_card = ".number-card" in target or ".number-widget-box" in target
                is_widget_head = ".widget-head" in target or ".widget-group-head" in target
                if not (is_number_card or is_widget_head):
                    continue
                # A slim accent legitimately carries a gradient: the ::before
                # top bar, or the figure's own text clipped to it
                # (background-clip:text — a colour on the digits, not a fill
                # behind them). The tile or header's own opaque `background`
                # must not — and must still be checked even when the same rule
                # also sets a plain border-left accent alongside it.
                if "::before" in target or "background-clip" in declarations:
                    continue
                match = re.search(r"(^|;)\s*background\s*:\s*([^;]+)", declarations)
                if not match:
                    continue
                value = match.group(2)

                # A gradient sized to a narrow strip and layered over the card
                # colour is an accent, not a wash — that is how the per-preset
                # header mark is drawn. What this is guarding against is a
                # gradient with no size, which fills the element edge to edge.
                strip = re.search(r"/\s*(?:var\([^)]*\)|[\d.]+(?:px|em|rem))\s", value)
                if strip and "var(--card-bg)" in value:
                    continue

                self.assertNotIn(
                    "gradient", value,
                    f"{filename}: {target} washes the whole tile in a gradient "
                    f"again -> {value[:60]}")

    def test_widget_title_does_not_repeat_its_own_headers_accent(self):
        """.widget-title is nested inside .widget-head, so decorating both
        draws the accent twice.

        That is exactly what shipped: a strip down the card's left edge and a
        second one beside the title text, on every widget. The title is the
        label — it carries type, not the card's chrome.
        """
        CHROME = ("border-left", "border-radius", "box-shadow")
        offenders = []
        for selector, declarations in css_rules("swift-desk.css"):
            target = selector.split("{")[0]
            if ".widget-title" not in target:
                continue
            # Only the title on its own. A more specific selector such as
            # .widget-head .widget-title is describing it in context, which is
            # a different thing from giving the bare element card chrome.
            if ".widget-head" in target or ".number-widget-box" in target:
                continue

            for prop in CHROME:
                if re.search(rf"(^|;)\s*{re.escape(prop)}\s*:", declarations):
                    offenders.append(f"{target} sets {prop}")

            bg = re.search(r"(^|;)\s*background\s*:\s*([^;]+)", declarations)
            if bg and "gradient" in bg.group(2):
                offenders.append(f"{target} paints a gradient behind the label")

        self.assertEqual(
            offenders, [],
            "the title repeats the accent its own header already draws: "
            f"{offenders}")

    def test_widget_group_head_is_segregated_from_a_widget_own_header(self):
        """A section label ("Assets", "Reports & Masters") groups several
        widgets — it is not one of them, and must not be styled as one.

        Both used to be the exact same selector list, so a group label and an
        individual widget's own title bar were indistinguishable.
        """
        # Read the rules properly rather than string-splitting on one exact
        # selector line — the earlier version keyed off a trailing comma and
        # broke the moment the rule was legitimately reshaped, which says
        # nothing about whether the two are still distinct.
        shared = [
            selector for selector, _ in css_rules("swift-desk.css")
            if ".widget-group-head" in selector and ".widget-head" in selector
        ]
        self.assertEqual(
            shared, [],
            "widget-group-head is back in the same rule as an individual "
            f"widget's own header — the two are meant to look different: {shared}")

        own = [
            declarations for selector, declarations in css_rules("swift-desk.css")
            if ".widget-group-head" in selector
        ]
        self.assertTrue(own, "widget-group-head has no rule of its own")
        self.assertTrue(
            any("background: transparent" in d for d in own),
            "a section label should not be boxed like the cards it groups")

    # The two workspace elements that repeat often enough to carry a preset's
    # identity: the KPI tile, and the heading that labels each band of cards.
    PRESET_ACCENTED = (
        ".number-card::before",
        ".ce-header::after",
    )

    def test_every_preset_has_its_own_accent_shapes(self):
        """Accent shapes are part of a preset's identity, like its backdrop.

        Before this each was one shape recoloured twelve ways, which is why
        switching preset only ever changed a hue — this checks every preset
        gets a rule of its own for each accented element, not a colour copied
        onto a shape they all share.
        """
        css = read_css("swift-preset-accents.css")
        for element in self.PRESET_ACCENTED:
            rules = {}
            for name, data in PREMIUM_THEMES.items():
                wanted = f'[data-swift-preset="{data["slug"]}"] {element}'
                self.assertIn(
                    wanted, css,
                    f"{name} has no {element} rule of its own in "
                    f"swift-preset-accents.css")
                # Only the declarations. Splitting at the selector and stopping
                # at "}" also swept up the *second* selector in a pair (the
                # .number-widget-box one), which carries the preset's own slug —
                # so every block was trivially unique and two presets could
                # share an identical shape without this noticing.
                block = css.split(wanted, 1)[1].split("{", 1)[1].split("}", 1)[0]
                rules[name] = re.sub(r"\s+", " ", block).strip()

            duplicates = {v for v in rules.values() if list(rules.values()).count(v) > 1}
            self.assertEqual(
                duplicates, set(),
                f"these presets share the exact same {element} shape, colour "
                "aside: " + str([n for n, v in rules.items() if v in duplicates]))

    def test_widgets_never_gain_a_containing_block_on_hover(self):
        """The bug that has bitten this theme twice, in test form.

        transform, filter and backdrop-filter each make an element a
        containing block and a stacking context for its descendants. Every
        widget has a dropdown inside its header, so a hover lift on the card
        traps that dropdown — exactly what happened to the notifications panel
        when a sidebar row had `transform` on hover. Depth here is shadow and
        border only.
        """
        TRAPPING = ("transform", "filter", "backdrop-filter", "-webkit-backdrop-filter")
        WIDGETS = (".widget", ".number-card", ".number-widget-box",
                   ".shortcut-widget-box", ".links-widget-box",
                   ".quick-list-widget-box", ".onboarding-widget-box",
                   ".dashboard-widget-box", ".custom-block-widget-box")

        offenders = []
        for filename in ("swift-desk.css", "swift-preset-accents.css"):
            for selector, declarations in css_rules(filename):
                target = selector.split("{")[0]
                if not any(w in target for w in WIDGETS):
                    continue
                # ::before / ::after are the accent shapes — they are already
                # inside the card and contain nothing, so they cannot trap it.
                if "::before" in target or "::after" in target:
                    continue
                for prop in TRAPPING:
                    if re.search(rf"(^|;)\s*{re.escape(prop)}\s*:", declarations):
                        offenders.append(f"{filename}: {target} sets {prop}")

        self.assertEqual(
            offenders, [],
            "these make a widget a containing block, trapping the dropdown "
            f"inside its own header: {offenders}")

    def test_every_workspace_element_type_is_styled(self):
        """A workspace is built from more than cards.

        Frappe registers eight widget types and renders three editor blocks
        between them; several were left entirely unthemed, so a heading or a
        "+ New Shortcut" placeholder kept Frappe's defaults while everything
        around it followed the preset. The list is taken from Frappe's own
        widget factory rather than written out by hand, so a type added
        upstream shows up here rather than being silently missed.
        """
        factory = open(frappe.get_app_path(
            "frappe", "public", "js", "frappe", "widgets", "widget_group.js")).read()
        registered = set(re.findall(r"^\t(\w+): \w+Widget|^\t(\w+): CustomBlock",
                                    factory, re.M))
        registered = {a or b for a, b in registered}
        self.assertTrue(registered, "could not read Frappe's widget factory")

        css = read_css("swift-desk.css")
        # widget_type -> the class Frappe's own widget puts on its wrapper.
        wrapper = {
            "shortcut": "shortcut-widget-box",
            "links": "links-widget-box",
            "onboarding": "onboarding-widget-box",
            "number_card": "number-widget-box",
            "quick_list": "quick-list-widget-box",
            "custom_block": "custom-block-widget-box",
            "chart": "dashboard-widget-box",
        }
        for widget_type in sorted(registered):
            cls = wrapper.get(widget_type)
            if not cls:
                continue          # `base` has no wrapper class of its own
            self.assertIn(
                f".{cls}", css,
                f"the {widget_type} widget (.{cls}) is registered by Frappe but "
                f"nothing in swift-desk.css themes it")

        # The editor blocks, which are not widgets and so are not in the factory.
        for cls, what in (("ce-header", "workspace headings"),
                          ("spacer", "workspace spacers"),
                          ("new-widget", "the add-a-widget placeholders")):
            self.assertIn(f".{cls}", css, f"{what} (.{cls}) are unthemed")

    def test_preset_accents_are_loaded_after_the_shape_they_override(self):
        """Ties on specificity resolve by source order, so this file has to
        come after swift-desk.css, or the generic strip would always win."""
        sheets = loaded_assets("app_include_css")
        self.assertIn("swift-preset-accents.css", sheets,
                      "swift-preset-accents.css is not loaded at all")
        self.assertLess(
            sheets.index("swift-desk.css"),
            sheets.index("swift-preset-accents.css"),
            "loaded before swift-desk.css, so the generic accent bar would "
            "always win the tie and no preset's own shape would ever show")

    def test_brand_sidebar_edges_are_sound(self):
        """Three things about the panel's edges, each from a real symptom.

        The panel has no gutter: it runs the full height of the window and
        meets its left edge. If one is ever put back, Frappe's `height: 100vh`
        has to come down by exactly what the vertical margin adds, or the
        bottom of the panel — the user card — is pushed past the viewport.

        Frappe also transitions `all` on it, so margin, height, radius and
        shadow animated along with the width and the panel visibly shifted
        whenever any of them changed. Only the width should move.

        And the themed default draws an inset hairline down the right edge with
        a shadow thrown sideways, which reads as a seam once the panel has
        rounded corners and is no longer touching the content.
        """
        block = None
        for selector, declarations in css_rules("swift-sidebar.css"):
            if '[data-swift-sidebar-fill="brand"]' in selector \
                    and selector.rstrip().endswith(".body-sidebar"):
                block = declarations
                break
        self.assertIsNotNone(block, "the brand sidebar rule is gone")

        # Conditional on purpose: with no margin there is nothing to
        # compensate, but the moment a gutter comes back this has to hold.
        margin = re.search(r"(?:^|;)\s*margin\s*:\s*([^;]+)", block)
        vertical = 0
        if margin:
            parts = " ".join(margin.group(1).split()).rstrip(";").split()
            top = parts[0] if parts else "0"
            bottom = parts[2] if len(parts) >= 3 else top
            vertical = sum(
                int(re.match(r"^(\d+)", side).group(1))
                for side in (top, bottom) if re.match(r"^\d+", side))
        if vertical:
            self.assertIn(
                "calc(100vh", block,
                f"the panel adds {vertical}px of vertical margin on top of "
                f"Frappe's 100vh, so it overflows the viewport and the user "
                f"card at its bottom is cut off")

        transition = re.search(r"(?:^|;)\s*transition-property\s*:\s*([^;]+)", block)
        self.assertIsNotNone(
            transition,
            "Frappe transitions `all` on this element; without narrowing that, "
            "the panel animates its own box and dances")
        self.assertNotIn(
            "all", transition.group(1),
            "the panel animates every property again, which is the dance")

        self.assertRegex(
            block, r"box-shadow\s*:",
            "the inherited sideways shadow and inset edge hairline are back — "
            "they read as a seam on a floating panel")

        # Flush against the window edge. Either no margin at all, or one whose
        # left side is zero — never a gap between the panel and the screen.
        if margin:
            self.assertRegex(
                " ".join(margin.group(1).split()), r"\b0\s*(;|$)",
                "the panel has a gap on its left edge; it should meet the window")

    def test_sidebar_selectors_are_classes_frappe_renders(self):
        """The sidebar had two selectors that matched nothing.

        `.desk-sidebar-item` is not rendered anywhere, and the active item was
        keyed off `.selected` when Frappe sets `active-sidebar`
        (ui/sidebar/sidebar.js). Two rules were therefore entirely dead — the
        whole selected-item treatment had never once applied — and a third,
        `.standard-sidebar-section-title`, was equally imaginary.
        """
        source = ""
        base = frappe.get_app_path("frappe", "public", "js", "frappe", "ui", "sidebar")
        for name in os.listdir(base):
            if name.endswith((".html", ".js")):
                with open(os.path.join(base, name), errors="ignore") as f:
                    source += f.read()

        css = ""
        for name in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
            css += read_css(name)

        for dead in ("desk-sidebar-item", "standard-sidebar-section-title"):
            self.assertNotIn(
                f".{dead}", css,
                f".{dead} is styled again but Frappe never renders it — the "
                f"rule matches nothing")

        # And the class that really does mark the current item.
        self.assertIn("active-sidebar", source,
                      "Frappe no longer uses active-sidebar; this needs revisiting")
        self.assertIn(".active-sidebar", css,
                      "the active sidebar item is unstyled again")

    def test_brand_sidebar_is_a_setting_that_reaches_the_desk(self):
        """The filled sidebar is opt-in, so every link in the chain matters:
        the field, the boot payload, the attribute, and the CSS behind it."""
        meta = frappe.get_meta("Swift Theme Settings")
        self.assertTrue(meta.has_field("sidebar_brand_fill"),
                        "the setting is gone from the form")

        for value in (0, 1):
            with settings_patched(sidebar_brand_fill=value):
                prefs = get_effective_prefs()
            self.assertEqual(
                prefs["sidebar_brand_fill"], value,
                "the desk is never told about the setting")

        js = read_js("swift-boot.js")
        self.assertIn('applyAttr("sidebar-fill"', js,
                      "nothing sets the attribute the CSS keys off")

        # applyAll builds its payload from an explicit list of keys, and a
        # setting missing from that list never reaches applyPrefs however well
        # applyPrefs handles it. That is exactly how this shipped broken while
        # a looser "is the name mentioned anywhere" check stayed green.
        apply_all = js.split("function applyAll", 1)
        self.assertEqual(len(apply_all), 2, "applyAll is gone")
        payload = apply_all[1].split("});", 1)[0]
        self.assertIn(
            "sidebar_brand_fill", payload,
            "applyAll does not forward sidebar_brand_fill, so saving Settings "
            "leaves the sidebar unchanged")

        css = read_css("swift-sidebar.css")
        self.assertIn('[data-swift-sidebar-fill="brand"]', css,
                      "the attribute is set but no CSS answers it")
        # Legibility on the filled panel comes from the preset's own computed
        # on-primary colour, not from a hardcoded light or dark.
        self.assertIn("--swift-accent-fg", css,
                      "the filled sidebar does not use the contrast colour "
                      "each preset computes, so text may be unreadable on it")

    def test_kanban_and_breadcrumb_classes_are_real(self):
        """These rules must target what Frappe actually renders.

        The kanban block previously keyed off `.kanban-board`, which Frappe
        does not render anywhere — the container is `.kanban` — so the whole
        section applied to nothing and the board kept its stock look under
        every preset. Same failure mode as the two widget selectors before it:
        silent, because a selector that matches nothing raises nothing.
        """
        real = [
            ("kanban", 'class="kanban"', "views/kanban/kanban_board.html"),
            ("kanban-column", 'class="kanban-column"', "views/kanban/kanban_column.html"),
            ("kanban-column-header", 'class="kanban-column-header"',
             "views/kanban/kanban_column.html"),
            ("kanban-column-title", 'class="kanban-column-title"',
             "views/kanban/kanban_column.html"),
            ("add-card", 'class="add-card"', "views/kanban/kanban_column.html"),
            ("kanban-cards", 'class="kanban-cards"', "views/kanban/kanban_column.html"),
            ("kanban-card-body", 'class="kanban-card-body"', "views/kanban/kanban_card.html"),
            ("kanban-card-title", 'class="kanban-card-title', "views/kanban/kanban_card.html"),
            ("kanban-card-doc", 'class="kanban-card-doc', "views/kanban/kanban_card.html"),
            ("navbar-breadcrumbs", "navbar-breadcrumbs", "ui/page.html"),
            ("sidebar-toggle-btn", "sidebar-toggle-btn", "ui/page.html"),
        ]

        js_root = frappe.get_app_path("frappe", "public", "js", "frappe")
        # Breadcrumbs are in swift-desk.css and the sidebar toggle moved to
        # swift-sidebar.css; both are checked, so neither file's name is what
        # this test is really asserting.
        css = read_css("swift-desk.css") + read_css("swift-sidebar.css")

        for cls, literal, relative in real:
            # Word-boundary, not substring: ".kanban-card" is contained in
            # ".kanban-card-body", so a plain `in` check stayed green even when
            # the rule it was guarding had been renamed away.
            self.assertRegex(
                css, rf"\.{re.escape(cls)}\b",
                f".{cls} is no longer styled — the kanban/breadcrumb work has "
                f"regressed")
            with open(os.path.join(js_root, relative), errors="ignore") as f:
                source = f.read()
            self.assertIn(
                literal, source,
                f".{cls} is used in swift-desk.css but {relative} does not "
                f"render it — the rule matches nothing")

        # Sweep for invented names too. The fixed list above can only check
        # what it already knows about; this catches a kanban class that was
        # never real in the first place.
        rendered = ""
        for relative in ("views/kanban/kanban_board.html",
                         "views/kanban/kanban_column.html",
                         "views/kanban/kanban_card.html"):
            with open(os.path.join(js_root, relative), errors="ignore") as f:
                rendered += f.read()
        with open(frappe.get_app_path(
                "frappe", "public", "scss", "desk", "kanban.scss"), errors="ignore") as f:
            rendered += f.read()

        used = {c for c in re.findall(r"\.(kanban[a-z0-9-]*)", css)}
        for cls in sorted(used):
            self.assertIn(
                cls, rendered,
                f".{cls} is styled in swift-desk.css but nothing in Frappe's "
                f"kanban renders or defines it")

        # The one that was actually wrong.
        self.assertNotIn(
            ".kanban-board", css,
            "the kanban rules target .kanban-board again, which Frappe never "
            "renders")

    def test_breadcrumbs_do_not_rely_on_frappes_own_ink_scale(self):
        """Breadcrumbs must take their colour from the preset.

        Frappe styles them with --ink-gray-4/5/7, which no preset defines, so
        before this the trail above every page stayed the same grey whatever
        theme was active. They are themed directly rather than by redefining
        that scale, which belongs to Frappe and is used well beyond here.
        """
        css = read_css("swift-desk.css")
        block = [
            declarations for selector, declarations in css_rules("swift-desk.css")
            if ".navbar-breadcrumbs" in selector
        ]
        self.assertTrue(block, "breadcrumbs are unthemed again")
        self.assertTrue(
            any("--text-muted" in d or "--heading-color" in d or "--swift-accent" in d
                for d in block),
            "breadcrumbs no longer read any theme variable")

        for declarations in block:
            self.assertNotIn(
                "--ink-gray", declarations,
                "breadcrumbs are back on Frappe's ink scale, which no preset "
                "defines")

    def test_workspace_widget_classes_are_real(self):
        """Shortcut/links/quick-list styling must target classes Frappe
        actually renders, not a guess at one.

        Two of these were wrong the first time this was written — `.list-row`
        for a quick-list row (the real class is `.quick-list-item`) and
        `.action_area` for the widget's icon area (that is a JS property name;
        the element itself is `.widget-control`) — and both failed silently:
        the rule just never matched anything, with no error to notice.

        Each check below is the exact literal Frappe uses to create the class
        (an addClass call, a .find() selector, or the class= attribute in its
        template), not a generic substring search — the naive version of this
        test passed on `action_area` too, because that string legitimately
        appears elsewhere in the same file as a JS property name.
        """
        widgets_dir = frappe.get_app_path("frappe", "public", "js", "frappe", "widgets")

        def widget_src(filename):
            with open(os.path.join(widgets_dir, filename), errors="ignore") as f:
                return f.read()

        css = read_css("swift-desk.css")

        # (class, source-literal-that-proves-it's-real, its file, and the
        # compound selector our own rule must use — not just the bare class,
        # since e.g. .widget-control is also used by the pre-existing
        # widget-head dropdown icon rule, so a bare presence check would stay
        # green even if the shortcut-specific rule using it were swapped out
        # for something else entirely).
        real = [
            ("shortcut-widget-box", 'addClass("shortcut-widget-box")', "shortcut_widget.js",
             "html[data-swift-themed] .shortcut-widget-box {"),
            ("links-widget-box", 'addClass("links-widget-box")', "links_widget.js",
             ".links-widget-box .link-item"),
            ("quick-list-widget-box", 'addClass("quick-list-widget-box")', "quick_list_widget.js",
             ".quick-list-widget-box .quick-list-item"),
            ("widget-control", '.find(".widget-control")', "base_widget.js",
             ".shortcut-widget-box .widget-control"),
            ("link-item", 'class="link-item', "links_widget.js",
             ".links-widget-box .link-item"),
            ("link-content", 'class="link-content', "links_widget.js",
             ".links-widget-box .link-item:hover .link-content"),
            ("quick-list-item", 'class="quick-list-item"', "quick_list_widget.js",
             ".quick-list-widget-box .quick-list-item"),
            ("widget-group-head", 'class="widget-group-head"', "widget_group.js",
             "html[data-swift-themed] .widget-group-head {"),
            ("widget-group-title", 'class="widget-group-title"', "widget_group.js",
             "html[data-swift-themed] .widget-group-title {"),
            ("onboarding-widget-box", 'addClass("onboarding-widget-box")', "onboarding_widget.js",
             ".onboarding-widget-box .onboarding-step"),
            ("onboarding-step", 'class="onboarding-step ${status}"', "onboarding_widget.js",
             ".onboarding-widget-box .onboarding-step"),
            ("step-text", 'class="step-text"', "onboarding_widget.js",
             ".onboarding-step.active .step-text"),
        ]
        # The checks below validate a fixed list of known-good classes, which
        # cannot notice a *new* invented one appearing beside them. So first
        # sweep every widget-ish class we actually use and require Frappe to
        # render it — that is what catches a fabricated name, rather than only
        # a substituted one.
        all_widget_src = "".join(
            widget_src(n) for n in os.listdir(widgets_dir) if n.endswith(".js"))
        WIDGET_PREFIXES = ("shortcut-", "links-", "quick-list-", "onboarding-",
                           "widget-group-", "step-")
        used_classes = {
            c for c in re.findall(r"\.([a-z][a-z0-9-]+)", css)
            if c.startswith(WIDGET_PREFIXES)
        }
        for cls in sorted(used_classes):
            self.assertIn(
                cls, all_widget_src,
                f".{cls} is styled in swift-desk.css but no Frappe widget "
                f"renders a class by that name — the rule matches nothing")

        for cls, literal, filename, compound in real:
            # Required, not just validated when present: a selector swapped
            # for a different (even plausible) one leaves no trace of the
            # original to check, so checking only what happens to be there
            # would have let both original mistakes slip straight through.
            self.assertIn(
                compound, css,
                f"{compound!r} is no longer in swift-desk.css — the "
                f"shortcut/links/quick-list distinction has regressed")
            self.assertIn(
                literal, widget_src(filename),
                f".{cls} is used in swift-desk.css but {filename} does not "
                f"render a class by that name — the rule matches nothing")

    def test_gradients_use_both_of_the_users_colours(self):
        """A user picks a pair; both should be visible, not just the first.

        These surfaces previously faded primary into a shade of itself, so a
        chosen secondary colour never appeared anywhere on the desk.
        """
        css = read_css("swift-desk.css")
        for marker in (".widget .widget-head", ".number-card", ".dt-header",
                       ".kanban-column-title", ".btn-primary"):
            self.assertIn(marker, css, f"{marker} has no themed rule")
        self.assertIn("--swift-secondary", css,
                      "no surface uses the second colour of the pair")

    def test_charts_are_repointed_at_the_theme(self):
        """frappe-charts hardcodes a light palette on :root.

        Without overriding its own variables the chart stays a white slab with
        near-black labels on every dark theme.
        """
        css = read_css("swift-desk.css")
        for var in ("--charts-tooltip-bg", "--charts-label-color",
                    "--charts-axis-line-color", "--charts-legend-label"):
            self.assertIn(var, css, f"{var} is left at the frappe-charts default")

    def test_desk_containers_do_not_trap_fixed_positioned_children(self):
        """Child tables broke on this.

        Frappe opens a grid row as .form-in-grid { position: fixed } behind a
        z-index 1040 backdrop. Lifting desk containers with
        `position: relative; z-index: <n>` makes them a stacking context, which
        caps that panel underneath the backdrop — the row opens but is hidden.
        The ambient wash must therefore paint behind (negative z-index) rather
        than push content in front.
        """
        base = read_css("swift-preset-base.css")

        # The wash sits behind everything instead of lifting the desk.
        self.assertRegex(base, r"body::before\s*\{[^}]*z-index:\s*-1")

        containers = (".layout-main", ".desk-body >", ".layout-main-section-wrapper",
                      ".page-container", ".main-section")
        for block in re.findall(r"\{[^{}]*\}", base):
            if "z-index" not in block or "position" not in block:
                continue
            if re.search(r"z-index:\s*-", block):
                continue
            start = base.rfind("}", 0, base.index(block))
            selector = base[start + 1: base.index(block)]
            for name in containers:
                self.assertNotIn(
                    name, selector,
                    f"{name} is given a stacking context, which traps the "
                    "position:fixed child-table editor under the backdrop",
                )

    def test_nothing_contains_the_desk(self):
        """Second cause of the broken child table, and the subtler one.

        `content-visibility: auto` (and `contain: paint/strict/content`) gives
        an element paint containment, which makes it a stacking context, the
        containing block for position:fixed descendants, and a clip boundary.
        Frappe opens a grid row as position:fixed at z-index 1021 inside
        .layout-main-section — under containment it was mispositioned, capped
        below the backdrop and clipped, so the row could not be typed into.
        Perf mode ships enabled, so every install had this.
        """
        containment = re.compile(
            r"(content-visibility\s*:\s*auto|contain\s*:\s*(paint|strict|content|layout))")
        for name in sorted(os.listdir(CSS_DIR)):
            if not name.endswith(".css"):
                continue
            src = COMMENT_RE.sub("", open(os.path.join(CSS_DIR, name)).read())
            for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", src):
                selector, body = block.group(1), block.group(2)
                if not containment.search(body):
                    continue
                self.assertNotRegex(
                    selector,
                    r"layout-main|frappe-card|form-section|desk-body|list-row|page-container",
                    f"{name}: containment on {selector.strip()[:60]!r} traps the "
                    "position:fixed child-table editor",
                )

    def test_theme_does_not_redeclare_frappes_editor_mechanics(self):
        """Colour it, don't re-engineer it.

        The editor works because Frappe puts .form-in-grid at z-index 1021 over
        a 1020 backdrop. Re-declaring position/z-index/opacity here would mean
        fighting Frappe on every upgrade, so the theme only sets surfaces.
        """
        css = read_css("swift-desk.css")
        for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
            selector, body = block.group(1), block.group(2)
            if "form-in-grid" not in selector and "#freeze" not in selector:
                continue
            for prop in ("z-index", "opacity", "position", "pointer-events", "overflow"):
                self.assertNotRegex(
                    body, rf"(^|;)\s*{prop}\s*:",
                    f"the theme overrides {prop} on {selector.strip()[:50]!r}; "
                    "leave Frappe's own value alone",
                )

    def test_child_table_editor_surface_follows_the_theme(self):
        """Frappe paints the editor with --modal-bg, which it leaves white."""
        css = read_css("swift-desk.css")
        # The panel surface must follow the theme; Frappe leaves --modal-bg white.
        self.assertRegex(css, r"--modal-bg:\s*var\(--card-bg\)")
        self.assertIn(".grid-row-open .form-in-grid", css)

    def test_theme_crossfade_uses_the_attribute_that_exists(self):
        """It was written as [data-swift-theme]; we set data-swift-themed."""
        base = read_css("swift-preset-base.css")
        self.assertNotRegex(base, r"\[data-swift-theme\]")
        # ...and must not fade the child-table editor in and out.
        self.assertRegex(base, r"data-swift-themed\]\s*\*:not\(#freeze\)")

    def test_child_table_grid_is_themed(self):
        css = read_css("swift-desk.css")
        for selector in (".form-grid", ".grid-heading-row", ".grid-row",
                         ".btn-open-row", ".grid-row-open", ".form-in-grid"):
            self.assertIn(selector, css, f"{selector} has no themed rule")
        # The open row has to look selected, not just be open.
        self.assertRegex(css, r"grid-row-open[^{]*\{[^}]*box-shadow")

    def test_navbar_follows_the_theme(self):
        css = read_css("swift-desk.css")
        self.assertIn("html[data-swift-themed] .navbar", css)

    def test_animated_background_is_wired_up(self):
        """The layer lives in preset-base; the motion belongs to whichever
        backdrop asks for it, so the two files are checked separately."""
        base = read_css("swift-preset-base.css")
        self.assertIn("body::before", base)
        self.assertIn("--swift-ambient", base)

        backdrops = read_css("swift-backdrops.css")
        self.assertIn("@keyframes swift-aurora", backdrops)
        self.assertIn("@keyframes swift-silk", backdrops)
        for data in PREMIUM_THEMES.values():
            path = os.path.join(CSS_DIR, "themes", f"{data['slug']}.css")
            self.assertIn("--swift-ambient", open(path).read(),
                          f"{data['slug']} defines no ambient background")

    def test_performance_mode_uses_the_attribute_boot_actually_sets(self):
        """The old rule keyed off data-swift-performance, which nothing set."""
        css = read_css("swift-desk.css")
        self.assertNotIn("data-swift-performance", css)
        self.assertIn("data-swift-perf", css)

    def test_hidden_sidebar_has_a_css_rule(self):
        """Alt+B set data-swift-sidebar="off" but nothing styled it."""
        self.assertIn('data-swift-sidebar="off"', read_css("swift-sidebar.css"))

    def test_toasts_are_anchored_to_the_top(self):
        """Frappe pins #alert-container to bottom:0; save confirmations belong up top."""
        css = read_css("swift-toast.css")
        self.assertIn("#alert-container", css)
        self.assertIn("bottom: auto", css)

    def test_nothing_traps_a_dropdown_inside_itself(self):
        """transform, filter and backdrop-filter all make an element the
        containing block for its position:fixed descendants.

        The navbar and the sidebar rows both host dropdowns — notifications
        lives inside a sidebar row — and a blur on the sidebar plus a 3px
        translate on row hover left that dropdown clipped and mispositioned.
        Same rule that governs the child-table editor, applied where popups
        actually live.
        """
        hosts = ("navbar", "sidebar", "dropdown", "item-anchor",
                 "standard-sidebar-item", "desk-sidebar-item")
        offenders = []
        for filename in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
            for selector, declarations in css_rules(filename):
                if not any(host in selector for host in hosts):
                    continue
                if "swift-sidebar-restore" in selector:
                    continue                 # our own button, hosts nothing
                for prop in ("transform", "filter", "backdrop-filter", "perspective"):
                    if re.search(rf"(^|;)\s*{prop}\s*:\s*(?!none)", declarations):
                        offenders.append(f"{filename}: {selector[:50]} sets {prop}")

        self.assertEqual(
            offenders, [], f"these trap their own dropdowns: {offenders}")

    def test_collapsed_sidebar_leaves_room_for_the_icon(self):
        """The collapsed rail is icon-width; margin on the row squeezed it out.

        Checking that a narrowing rule merely exists was not enough, and this
        shipped broken twice because of it: the rule stayed in the file while a
        later, more specific one beat it. Frappe gives the collapsed panel 50px
        with 8px of padding a side — 34px — and the icon wants 30px of that. So
        resolve the cascade the way a browser would and measure what actually
        wins, for every combination of variant and fill the app can be in.
        """
        PANEL, PADDING, ICON = 50, 8, 30
        room = PANEL - (PADDING * 2)

        def specificity(selector):
            sel = re.sub(r"::?[a-z-]+(\([^)]*\))?", "", selector)
            ids = len(re.findall(r"#[\w-]+", sel))
            classes = len(re.findall(r"[.:][\w-]+|\[[^\]]+\]", selector))
            types = len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", sel))
            return (ids, classes, types)

        # Every state the sidebar can be in, as the attributes the boot script
        # writes on <html> plus the class Frappe puts on the container.
        variants = [v.strip() for v in
                    frappe.get_meta("Swift Theme Settings").get_field("sidebar_variant").options.split("\n")
                    if v.strip()]
        states = [{"fill": fill, "variant": variant}
                  for fill in ("", "brand") for variant in variants]

        for state in states:
            with self.subTest(**state):
                winner, best = None, None
                for name in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
                    for selector, declarations in css_rules(name):
                        if ".standard-sidebar-item" not in selector:
                            continue
                        # Only rules that match a collapsed sidebar in this state.
                        if ".expanded" in selector and ":not(.expanded)" not in selector:
                            continue
                        if "sidebar-fill" in selector and state["fill"] != "brand":
                            continue
                        if ("sidebar-variant" in selector
                                and f'"{state["variant"]}"' not in selector):
                            continue
                        if any(x in selector for x in (":hover", ":focus", "active-sidebar")):
                            continue
                        margin = re.search(
                            r"(?:^|;)\s*margin\s*:\s*([^;]+)", declarations)
                        if not margin:
                            continue
                        rank = specificity(selector)
                        if best is None or rank >= best:   # later source order wins ties
                            winner, best = (selector, margin.group(1).strip()), rank

                if winner is None:
                    continue    # nothing sets it; Frappe's own margin applies

                selector, value = winner
                parts = value.split()
                horizontal = parts[1] if len(parts) >= 2 else parts[0]
                resolved = horizontal
                for _ in range(4):      # follow var() indirection to a length
                    token = re.match(r"var\((--[\w-]+)", resolved)
                    if not token:
                        break
                    declared = re.findall(
                        rf"{token.group(1)}\s*:\s*([^;]+);",
                        read_css("swift-sidebar.css"))
                    # The collapsed value is the base one — the smallest declared.
                    lengths = [d.strip() for d in declared
                               if re.match(r"^\d+px$", d.strip())]
                    if not lengths:
                        break
                    resolved = min(lengths, key=lambda d: int(d[:-2]))

                measure = re.match(r"^(\d+)px$", resolved)
                self.assertIsNotNone(
                    measure,
                    f"{selector} sets margin {value!r}, which does not resolve "
                    f"to a length this test can measure")

                left = room - (int(measure.group(1)) * 2)
                self.assertGreaterEqual(
                    left, ICON,
                    f"collapsed, {selector} leaves the row {left}px of the "
                    f"{room}px available and the icon needs {ICON}px, so the "
                    f"sidebar renders as an empty strip")

    def test_brand_sidebar_text_is_readable_on_every_preset(self):
        """The panel is a gradient, so the text must clear the floor on both ends.

        Picking the text colour against the brand colour alone was not enough:
        on a mid-tone primary neither black nor white cleared 4.5:1 across the
        whole panel, and Black Panther and Winter Soldier shipped at 3.4:1 and
        3.9:1 — styled, present, and unreadable. The generator now moves the
        panel to fit the text, and this is what keeps it honest.
        """
        import sys
        sys.path.insert(0, frappe.get_app_path(APP, "scripts"))
        from colour import contrast

        theme_dir = os.path.join(CSS_DIR, "themes")
        sheets = sorted(n for n in os.listdir(theme_dir) if n.endswith(".css"))
        self.assertTrue(sheets, "no preset stylesheets ship")

        for name in sheets:
            with self.subTest(preset=name[:-4]):
                css = read_css(os.path.join("themes", name)) \
                    if False else open(os.path.join(theme_dir, name)).read()

                def token(key):
                    found = re.search(rf"{re.escape(key)}:\s*(#[0-9a-fA-F]{{3,8}})", css)
                    self.assertIsNotNone(
                        found, f"{name} does not define {key}, so the sidebar "
                        f"falls back to a colour nothing has checked")
                    return found.group(1)

                start = token("--swift-sidebar-fill-start")
                end = token("--swift-sidebar-fill-end")
                text = token("--swift-sidebar-fg")

                for label, background in (("top", start), ("bottom", end)):
                    ratio = contrast(text, background)
                    self.assertGreaterEqual(
                        round(ratio, 2), 4.5,
                        f"{name[:-4]}: {text} on {background} at the {label} of "
                        f"the sidebar is {ratio:.2f}:1, below the 4.5:1 floor")

    def test_brand_fill_recolours_every_text_element_it_covers(self):
        """The panel goes brand-coloured, so the text on it must follow.

        Frappe sets `color: var(--ink-gray-6)` on .item-anchor, which means the
        row cannot inherit the panel's colour — it has to be overridden. Two
        rules once got merged into one during an edit and the surviving
        declaration was `stroke`, so every label kept Frappe's mid-grey on a
        saturated panel: the sidebar looked empty while the items were all
        there. Checking the selector exists is not enough; check what it sets.
        """
        NEEDS_COLOUR = (
            ".sidebar-item-label",     # the row's text
            ".item-anchor",            # what Frappe colours explicitly
            ".avatar-name-email span",  # the person at the bottom
        )
        NEEDS_STROKE = (".sidebar-item-icon svg",)

        declared = {}
        for selector, declarations in css_rules("swift-sidebar.css"):
            if 'sidebar-fill="brand"' not in selector:
                continue
            if any(x in selector for x in (":hover", "active-sidebar", "section-item")):
                continue        # state and section overrides are not the base
            properties = {d.split(":", 1)[0].strip()
                          for d in declarations.split(";") if ":" in d}
            for part in selector.split(","):
                key = part.strip().replace('html[data-swift-sidebar-fill="brand"] ', "")
                key = key.replace(".body-sidebar ", "")
                declared.setdefault(key, set()).update(properties)

        for target in NEEDS_COLOUR:
            self.assertIn(
                "color", declared.get(target, set()),
                f"under the brand fill, {target} is never given a colour, so it "
                f"keeps Frappe's ink-gray on a brand-coloured panel")

        for target in NEEDS_STROKE:
            self.assertTrue(
                {"stroke", "color"} & declared.get(target, set()),
                f"under the brand fill, {target} is never repainted, so the "
                f"icons stay dark on a dark panel")

    def test_brand_fill_never_paints_text_onto_its_own_colour(self):
        """A container styled as a badge swallows whatever sits inside it.

        .sidebar-item-suffix is where Frappe puts any suffix — the notification
        count, but also the "Ctrl + K" hint next to Search. Painting the
        container with the surface colour and the hint with the on-brand
        colour put near-white text on a white panel: the hint rendered as a
        blank pill. Only the count is a badge; the container is not.
        """
        surfaces = {}
        for selector, declarations in css_rules("swift-sidebar.css"):
            if 'sidebar-fill="brand"' not in selector:
                continue
            background = re.search(
                r"(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)", declarations)
            colour = re.search(r"(?:^|;)\s*color\s*:\s*([^;]+)", declarations)
            key = selector.rsplit(" ", 1)[-1]
            if background:
                surfaces.setdefault(key, {})["bg"] = background.group(1).strip()
            if colour:
                surfaces.setdefault(key, {})["fg"] = colour.group(1).strip()

        suffix = surfaces.get(".sidebar-item-suffix", {})
        self.assertNotIn(
            "swift-surface", suffix.get("bg", ""),
            "the suffix container is painted as a badge, so the Ctrl+K hint "
            "inside it renders as light text on a light panel")

        # The count still has to look like a badge.
        count = surfaces.get(".sidebar-notification-count", {})
        self.assertTrue(
            count.get("bg"), "the notification count lost its badge surface")
        self.assertTrue(
            count.get("fg"), "the notification count has no text colour, so it "
            "inherits the on-brand one and disappears into its own badge")

    def test_brand_fill_keeps_frappe_clipping_the_sidebar_on_phones(self):
        """Frappe hides the sidebar on small screens by clipping it.

        It sets width:0 and leans on overflow:hidden — the content keeps its
        intrinsic width. The brand fill needs overflow:visible so the collapse
        button can sit on the panel edge, and that rule outranks Frappe's, so
        the whole panel spilled across a phone screen. It has to be given back.
        """
        css = read_css("swift-sidebar.css")
        self.assertIn(
            "overflow: visible", css,
            "the collapse control is back to being clipped by the panel")

        guard = re.search(
            r"@media\s*\(max-width:\s*575\.98px\)\s*\{(.*?)\n\}", css, re.S)
        self.assertIsNotNone(
            guard, "no small-screen rule restores the clipping Frappe relies on")
        self.assertIn("overflow: hidden", guard.group(1))
        self.assertIn("body-sidebar", guard.group(1))

    def test_user_theme_fields_follow_the_server_permission(self):
        """The form must not offer what set_user_pref will refuse.

        Those fields were editable regardless, so a user could change one and
        have the save rejected, or stored and then ignored.
        """
        js = read_js("user_form.js")
        for fieldname in ("swift_preset", "swift_primary", "swift_secondary"):
            self.assertIn(fieldname, js, f"{fieldname} is left editable on the form")
        self.assertIn("read_only", js)
        self.assertIn("enable_switcher", js)
        self.assertIn("can_switch_theme", js)

        self.assertEqual(
            frappe.get_hooks("doctype_js", {}).get("User"),
            ["public/js/user_form.js"],
            "the User form script is not registered, so it never runs")

    def test_breadcrumbs_use_a_chevron_and_not_before_the_first_crumb(self):
        """Frappe writes the separator in CSS, so replacing it is a cascade job.

        Two of its rules matter: `a:before { content: "/" }` sets the mark, and
        `li:first-child a:before { content: none }` blanks it in front of the
        opening crumb. The second is the trap — it scores one class and two
        types, so a rule specific enough to beat the first also beats it, and a
        stray chevron appears before the module name.
        """
        rules = [(selector, declarations)
                 for selector, declarations in css_rules("swift-desk.css")
                 if "navbar-breadcrumbs" in selector and "content" in declarations]
        self.assertTrue(rules, "nothing replaces Frappe's slash separator")

        for selector, declarations in rules:
            self.assertIn(
                ":not(:first-child)", selector,
                f"{selector} sets the separator without excluding the opening "
                f"crumb, so it draws one in front of the module name")
            self.assertNotIn(
                '"/"', declarations, f"{selector} still writes a slash")
            # \203A is a single right-pointing angle quote: the chevron.
            self.assertRegex(
                declarations, r'content:\s*"\\203A"',
                f"{selector} does not set the chevron")

    def test_settings_form_is_organised_in_tabs(self):
        """Tabs, not two columns of sections stacked down one page.

        Every setting on one scroll meant the colour controls and the sound
        controls shared a screen, and a column break put unrelated fields
        side by side.
        """
        meta = frappe.get_meta("Swift Theme Settings")
        tabs = [f.label for f in meta.fields if f.fieldtype == "Tab Break"]
        self.assertGreaterEqual(
            len(tabs), 3, f"the form is not split into tabs, only {tabs}")

        columns = [f.fieldname for f in meta.fields if f.fieldtype == "Column Break"]
        self.assertEqual(
            columns, [],
            f"these column breaks still split the form sideways: {columns}")

        # A field before the first Tab Break lands on an unnamed leading tab.
        order = [f.fieldtype for f in meta.fields]
        self.assertEqual(
            order[0], "Tab Break",
            f"{meta.fields[0].fieldname} sits ahead of the first tab")

        for field in meta.fields:
            if field.fieldtype in ("Tab Break", "Section Break", "Column Break"):
                continue
            self.assertTrue(
                field.label or field.hidden,
                f"{field.fieldname} has no label to show under its tab")

    def test_restore_control_is_styled(self):
        css = read_css("swift-sidebar.css")
        self.assertIn(".swift-sidebar-restore", css,
                      ".swift-sidebar-restore is injected by JS but never styled")

    def test_sidebar_pinning_is_gone_completely(self):
        """Removed feature, removed remains.

        Pinning put a star on Frappe's own sidebar rows and reordered its nav on
        every mutation. Leaving any half of it behind — CSS with no JS, a stored
        setting with nothing reading it — is how dead options accumulate.
        """
        for filename in sorted(n for n in os.listdir(CSS_DIR) if n.endswith(".css")):
            css = read_css(filename)
            for token in ("swift-pin-btn", "swift-pinned", "data-swift-pin"):
                self.assertNotIn(token, css, f"{token} still styled in {filename}")

        for filename in sorted(n for n in os.listdir(JS_DIR) if n.endswith(".js")):
            self.assertNotIn("swift-pin-btn", read_js(filename),
                             f"{filename} still injects a pin button")

        self.assertFalse(
            frappe.get_meta("Swift Theme Settings").has_field("pin_behavior"),
            "the pin setting is still on the form with nothing reading it")

    def test_desk_listens_for_the_settings_broadcast(self):
        """Without this listener, saving Settings needs a hard refresh."""
        js = read_js("swift-boot.js")
        self.assertIn('frappe.realtime.on("swift_theme_updated"', js)

    def test_switcher_reacts_to_live_preference_changes(self):
        self.assertIn("swift:prefs:applied", read_js("swift-boot.js"))
        self.assertIn("swift:prefs:applied", read_js("swift-switcher.js"))

    def test_feature_flags_are_honoured_by_their_modules(self):
        for filename, flag in (
            ("swift-switcher.js", "enable_switcher"),
            ("swift-focus.js", "enable_focus_mode"),
            ("swift-palette.js", "enable_command_palette"),
        ):
            self.assertIn(flag, read_js(filename), f"{filename} ignores {flag}")

    def test_sidebar_no_longer_watches_the_desk(self):
        """The observer existed only to re-apply pins after every re-render.

        With pinning gone it has no job, and a MutationObserver on Frappe's
        sidebar is exactly the kind of standing cost a theme should not carry.
        """
        # Comments stripped first: read_js keeps them, unlike read_css, and the
        # file's own note explaining the removal names the class.
        js = COMMENT_RE.sub("", read_js("swift-sidebar.js"))
        js = re.sub(r"//[^\n]*", "", js)
        self.assertNotIn("new MutationObserver", js,
                         "the sidebar still observes the desk with nothing to apply")


    def test_presets_are_offered_in_frappes_own_theme_dialog(self):
        """One place to switch theme, not two competing ones."""
        js = read_js("swift-theme-dialog.js")
        self.assertIn("frappe.ui.ThemeSwitcher", js)
        self.assertIn("setup_dialog", js)
        self.assertIn("setCustomColors", js, "custom pair must be pickable there too")
        self.assertIn("clearPersonalTheme", js, "and a way back to the site default")

    def test_theme_dialog_is_loaded_on_the_desk(self):
        self.assertIn("swift-theme-dialog.js", loaded_assets("app_include_js"))

    def test_theme_dialog_elements_are_styled(self):
        css = read_css("swift-desk.css")
        for selector in (".swift-switch", ".swift-custom", ".swift-theme-grid"):
            self.assertIn(selector, css, f"{selector} is built by JS but never styled")

    def test_presets_reuse_frappes_own_card_markup(self):
        """Cards must look like Frappe's Light/Dark ones, not a separate widget."""
        js = read_js("swift-theme-dialog.js")
        self.assertIn("theme-grid", js, "cards belong in Frappe's own grid class")
        for part in ("background", "preview-check", "theme-title", "foreground"):
            self.assertIn(part, js, f"card markup is missing .{part}")

    def test_custom_colours_are_a_second_step(self):
        """The pickers stay hidden until the Custom Colors card is chosen."""
        js = read_js("swift-theme-dialog.js")
        self.assertIn('hidden', js)
        self.assertIn("removeAttr", js)

    def test_switcher_ui_is_gated_on_the_role_flag(self):
        for filename in ("swift-theme-dialog.js", "swift-switcher.js", "swift-palette.js"):
            self.assertIn(
                "can_switch_theme", read_js(filename), f"{filename} does not check the role"
            )

    def test_boot_exposes_a_custom_colour_api(self):
        js = read_js("swift-boot.js")
        self.assertIn("setCustomColors", js)
        self.assertIn("swift_primary", js)

    def test_boot_js_actually_applies_the_theme(self):
        """Runs swift-boot.js for real, rather than grepping its source.

        The string assertions elsewhere in this class prove code is present;
        this proves it works — the attributes and the stylesheet link that the
        CSS keys off are genuinely produced.
        """
        import shutil
        import subprocess

        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")

        harness = frappe.get_app_path(APP, "tests", "boot_js_contract.js")
        result = subprocess.run(
            [node, harness], capture_output=True, text=True, timeout=60
        )
        self.assertEqual(
            result.returncode, 0, f"swift-boot.js contract failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_boot_swaps_a_single_theme_stylesheet(self):
        """Presets must retarget one <link>, not stack stylesheets."""
        js = read_js("swift-boot.js")
        self.assertIn("swapThemeStylesheet", js)
        self.assertIn("swift-theme-css", js)

    def test_boot_handles_both_colour_modes(self):
        js = read_js("swift-boot.js")
        self.assertIn("--swift-primary", js)
        self.assertIn("--swift-secondary", js)
        self.assertIn("data-swift-themed", js)

    def test_no_javascript_still_references_the_removed_accent_system(self):
        """default_accent / full themes were folded into Color Mode."""
        for filename in os.listdir(JS_DIR):
            if not filename.endswith(".js"):
                continue
            body = read_js(filename)
            for dead in ("swift_accent", "data-swift-accent", "setFullTheme", "hex_override"):
                self.assertNotIn(dead, body, f"{filename} still references {dead}")

    def test_sidebar_removes_the_restore_button(self):
        self.assertIn("removeRestoreButton", read_js("swift-sidebar.js"))

    def test_sound_failures_cannot_break_document_saving(self):
        """The engine wraps frappe.ui.form.save, so it must never throw."""
        js = read_js("swift-sounds.js")
        save_wrapper = js.split("hookFormActions", 1)[1]
        self.assertIn("try {", save_wrapper)

    def test_every_registered_asset_exists_on_disk(self):
        """A typo in hooks.py yields a 404 and a silently missing feature."""
        hooks = frappe.get_hooks()
        for key in ("app_include_js", "app_include_css", "web_include_js", "web_include_css"):
            for path in hooks.get(key) or []:
                if not path.startswith(f"/assets/{APP}/"):
                    continue
                relative = path.replace(f"/assets/{APP}/", "")
                self.assertTrue(
                    os.path.exists(frappe.get_app_path(APP, "public", *relative.split("/"))),
                    f"{key} references a missing file: {path}",
                )


class TestSwiftThemeInstall(IntegrationTestCase):
    def test_code_defaults_match_the_doctype_defaults(self):
        """Two places answer "what is the default", and they must not drift.

        On a fresh install tabSingles is empty, so get_single() answers from
        the DocType's own `default` for every field — which means _seed_settings
        finds nothing unset and writes nothing at all. The app still starts up
        correctly, but only because the two agree: change SETTINGS_DEFAULTS
        alone and a new site silently gets the DocType's value while the code
        believes it seeded its own.
        """
        from swift_theme.install import SETTINGS_DEFAULTS

        meta = frappe.get_meta("Swift Theme Settings")
        mismatched = []
        for fieldname, expected in SETTINGS_DEFAULTS.items():
            field = meta.get_field(fieldname)
            if not field:
                mismatched.append(f"{fieldname}: no such field on the DocType")
                continue
            if str(field.default) != str(expected):
                mismatched.append(
                    f"{fieldname}: code says {expected!r}, DocType says {field.default!r}")

        self.assertEqual(
            mismatched, [],
            "a fresh install would not get the default the code intends: "
            f"{mismatched}")

    def test_seed_settings_is_idempotent(self):
        """after_migrate runs it on every migrate; it must not clobber choices."""
        from swift_theme.install import _seed_settings

        with settings_patched(active_preset="Scarlet Witch", enable_switcher=0):
            _seed_settings()
            settings = frappe.get_single("Swift Theme Settings")
            self.assertEqual(settings.active_preset, "Scarlet Witch")
            self.assertEqual(settings.enable_switcher, 0)

    def test_user_fields_are_owned_by_this_apps_module(self):
        """Uninstall has to leave the User doctype as it found it.

        Frappe removes records whose `module` points at the app being removed
        (installer._delete_linked_documents), and Custom Field has exactly such
        a field — so ownership is the entire uninstall story here, and a field
        created without it would be silently orphaned on someone else's site
        with nothing left to clean it up.
        """
        from swift_theme.install import USER_FIELDS

        for fieldname, *_ in USER_FIELDS:
            module = frappe.db.get_value(
                "Custom Field", {"dt": "User", "fieldname": fieldname}, "module")
            self.assertEqual(
                module, "Swift Theme",
                f"User.{fieldname} is not owned by this app's module, so "
                f"uninstalling would leave it behind")

    def test_user_preference_fields_exist(self):
        from swift_theme.install import USER_FIELDS

        meta = frappe.get_meta("User")
        for fieldname, *_ in USER_FIELDS:
            self.assertTrue(meta.has_field(fieldname), f"User.{fieldname} was never created")

    def test_apply_theme_target_field_accepts_every_preset(self):
        """apply_theme writes the preset name into swift_preset."""
        options = frappe.get_meta("User").get_field("swift_preset").options.split("\n")
        for name in PREMIUM_THEMES:
            self.assertIn(name, options, f"preset {name!r} is not a valid swift_preset option")

    def test_patches_are_registered_and_importable(self):
        patches = frappe.get_file_items(frappe.get_app_path(APP, "patches.txt"))
        for entry in patches:
            if entry.startswith("[") or entry.startswith("execute:"):
                continue
            frappe.get_attr(f"{entry}.execute")

    def test_value_migration_runs_before_the_flag_patch(self):
        """Ordering is load-bearing, not cosmetic.

        enable_feature_flags reads Settings. Until color_mode has been converted
        to the new option list, loading it is a validation error waiting to
        happen, so the conversion has to be listed first.
        """
        patches = frappe.get_file_items(frappe.get_app_path(APP, "patches.txt"))
        order = [p for p in patches if not p.startswith("[")]
        convert = order.index("swift_theme.patches.v1_0.migrate_to_preset_or_custom_colors")
        flags = order.index("swift_theme.patches.v1_0.enable_feature_flags")
        self.assertLess(
            convert, flags,
            "enable_feature_flags is listed before the value migration; on a site "
            "upgrading from the old schema it will abort the whole bench migrate")

    def test_flag_patch_survives_a_value_the_new_schema_rejects(self):
        """The exact upgrade that broke: an old color_mode still in the row.

        This is what a real pre-upgrade site looks like at the moment patches
        start running. The patch has nothing to do with color_mode and must not
        care about it.
        """
        from swift_theme.patches.v1_0.enable_feature_flags import execute

        with stale_single_value("color_mode", "Preset Themes"):
            frappe.db.set_single_value("Swift Theme Settings", "enable_switcher", 0)
            execute()
            self.assertEqual(
                frappe.db.get_single_value("Swift Theme Settings", "enable_switcher"), 1,
                "the flag patch did not turn the switcher back on")

    def test_seeding_repairs_a_stale_select_instead_of_dying(self):
        """One retired preset name must not cost every new field its default.

        _seed_settings saves the document, so a value the Select no longer
        offers raised ValidationError and every genuinely new field stayed NULL.
        """
        from swift_theme.install import _seed_settings

        with stale_single_value("active_preset", "Midnight Pro"):
            frappe.db.set_single_value("Swift Theme Settings", "custom_mode", None)
            _seed_settings()

            settings = frappe.get_single("Swift Theme Settings")
            self.assertIn(
                settings.active_preset, PREMIUM_THEMES,
                "the retired preset name was left in place")
            self.assertEqual(
                settings.custom_mode, "Dark",
                "seeding aborted, so the new field never got its default")

    def test_every_select_can_account_for_being_blank(self):
        """A Select must either be seeded or genuinely allow blank.

        Some fields are deliberately blank — `backdrop` blank means "whatever
        this preset ships with" — and those list "" as an option. A Select that
        does neither shows an empty box the form will refuse to save, which is
        how custom_mode and custom_strength shipped.
        """
        from swift_theme.install import SETTINGS_DEFAULTS

        meta = frappe.get_meta("Swift Theme Settings")
        offenders = []
        for field in meta.fields:
            if field.fieldtype != "Select" or field.hidden:
                continue
            if field.fieldname in SETTINGS_DEFAULTS:
                continue
            if "" in (field.options or "").split("\n"):
                continue          # blank is a real choice here
            offenders.append(field.fieldname)

        self.assertEqual(
            offenders, [],
            f"these Selects show blank but do not accept blank: {offenders}")


class TestSwiftThemeLoginPage(IntegrationTestCase):
    """The page is Frappe's markup and Frappe's script. Only the design is ours.

    An earlier version wrote its own form and its own login script, and it
    drifted at once: sign-up linked to /signup, which is not a route; the social
    providers, LDAP and the email-link sign-in were absent; and signed-in users
    were sent to /app, the v15 desk. Every check here exists to keep that from
    coming back.
    """

    TEMPLATE = frappe.get_app_path(APP, "www", "login.html")
    FRAPPE_TEMPLATE = os.path.join(frappe.get_app_path("frappe"), "www", "login.html")

    def template(self):
        with open(self.TEMPLATE) as handle:
            return handle.read()

    def test_every_section_frappe_renders_is_still_here(self):
        """Frappe's login.js binds by section, so a missing one is a dead route.

        Nothing errors when one is dropped — the link simply goes nowhere,
        which is how the sign-up link came to point at a 404 for so long.
        """
        ours = self.template()
        with open(self.FRAPPE_TEMPLATE) as handle:
            theirs = handle.read()

        sections = set(re.findall(r"<section class='(for-[\w-]+)", theirs))
        self.assertTrue(sections, "could not read Frappe's login sections")

        missing = sorted(s for s in sections if s not in ours)
        self.assertEqual(
            missing, [],
            f"Frappe's login script drives these and they are not on the page, "
            f"so those routes are dead: {missing}")

    def test_the_login_script_is_frappes_and_ours_is_gone(self):
        """The behaviour has to be Frappe's, not a copy of it."""
        ours = self.template()
        self.assertIn(
            'include "templates/includes/login/login.js"', ours,
            "the page does not include Frappe's login script, so none of its "
            "sign-in, sign-up or reset behaviour is wired up")

        self.assertFalse(
            os.path.exists(os.path.join(JS_DIR, "login.js")),
            "a second login script ships alongside Frappe's; two scripts "
            "binding the same form is how the two drifted apart before")

        # The form must post through Frappe, not through a fetch of our own.
        for name in os.listdir(JS_DIR):
            if not name.endswith(".js"):
                continue
            with open(os.path.join(JS_DIR, name)) as handle:
                body = handle.read()
            self.assertNotIn(
                '"/api/method/login"', body,
                f"{name} performs its own login instead of leaving it to "
                f"Frappe's script")

    def test_the_layout_is_rendered_by_the_server_not_added_afterwards(self):
        """The layout decides the whole shape, so it cannot arrive late.

        Applied by a script after first paint, the page visibly rearranges
        itself as it loads.
        """
        with open(frappe.get_app_path(APP, "www", "login.py")) as handle:
            controller = handle.read()
        self.assertIn(
            'context["body_class"]', controller,
            "the layout is not put on the body server-side, so the page "
            "changes shape after it has painted")

    def test_every_login_layout_is_styled(self):
        """Each option the Select offers has to change something."""
        options = [o.strip() for o in
                   frappe.get_meta("Swift Theme Settings")
                   .get_field("login_layout").options.split("\n") if o.strip()]
        self.assertTrue(options, "login_layout offers nothing")

        css = read_css("swift-login.css")
        for layout in options:
            self.assertIn(
                f"swift-login-{layout}", css,
                f"choosing the {layout} layout changes nothing on screen")

    def test_the_design_targets_markup_that_actually_exists(self):
        """Styling Frappe's markup means its class names are the contract.

        A selector matching nothing is silent — the page just looks unstyled.
        """
        sources = [self.template(), self.FRAPPE_TEMPLATE]
        blob = self.template()
        for extra in (self.FRAPPE_TEMPLATE,
                      os.path.join(frappe.get_app_path("frappe"),
                                   "templates/includes/login/login.js"),
                      os.path.join(frappe.get_app_path("frappe"),
                                   "templates/web.html"),
                      os.path.join(frappe.get_app_path("frappe"),
                                   "templates/base.html")):
            if os.path.exists(extra):
                with open(extra) as handle:
                    blob += handle.read()
        with open(os.path.join(JS_DIR, "swift-website.js")) as handle:
            blob += handle.read()

        # The per-layout class is built rather than written — "swift-login-" +
        # the chosen layout — so the whole name appears in no file. Each option
        # the field offers is a name the page can really carry.
        for option in (frappe.get_meta("Swift Theme Settings")
                       .get_field("login_layout").options or "").split("\n"):
            if option.strip():
                blob += f"\nswift-login-{option.strip()}\n"

        targets = set()
        for selector, _declarations in css_rules("swift-login.css"):
            if "swift-login" not in selector:
                continue
            for part in selector.split(","):
                leaf = part.strip().split()[-1] if part.strip() else ""
                targets.update(re.findall(r"\.([\w-]+)", leaf))

        missing = sorted(name for name in targets if name not in blob)
        self.assertEqual(
            missing, [],
            f"the login stylesheet targets classes nothing renders, so those "
            f"rules can never match: {missing}")

    def test_the_brand_panel_reads_every_word_from_settings(self):
        """It used to be written into the template, so it could not be changed."""
        ours = self.template()
        for fieldname in ("login_heading_lines", "login_description",
                          "login_points", "login_stat_value", "login_stat_label",
                          "login_show_brand_panel"):
            self.assertIn(
                fieldname, ours,
                f"the brand panel ignores {fieldname}, so that part of it "
                f"cannot be changed from Settings")

        # And nothing may be left hard-coded beside them.
        panel = re.search(r"<aside class=\"swift-login-brand\".*?</aside>",
                          ours, re.S)
        self.assertIsNotNone(panel, "the brand panel markup is gone")
        self.assertNotIn(
            "_(\"", panel.group(0),
            "the brand panel still prints a string of its own instead of the "
            "one configured in Settings")

    def test_a_backdrop_ships_so_a_fresh_install_is_not_blank(self):
        """The centred layout is built around a picture, so one has to be there.

        Without a default it lands on a flat colour until somebody uploads an
        image, which is the one layout where that reads as unfinished. Drawn
        rather than photographed: it costs a few kilobytes, scales to any
        screen, and carries no licence with it.
        """
        images = frappe.get_app_path(APP, "public", "images")
        self.assertTrue(
            os.path.isdir(images), "no images ship with the app")

        css = read_css("swift-login.css")
        referenced = re.findall(r'url\("?/assets/swift_theme/images/([^")]+)"?\)', css)
        self.assertTrue(
            referenced,
            "no default backdrop is applied, so the centred layout starts blank")

        for name in referenced:
            self.assertTrue(
                os.path.exists(os.path.join(images, name)),
                f"the stylesheet points at images/{name}, which does not ship — "
                f"every login page would request a 404")

        # It has to be overridable, or the setting is decoration.
        self.assertRegex(
            css, r"var\(--swift-login-bg,\s*url\(",
            "the backdrop is applied unconditionally, so uploading a Login "
            "Background Image would change nothing")

    def test_the_login_panels_follow_the_preset(self):
        """Each preset should look like itself here, not like one fixed brand.

        The designs these were drawn from are one company's colours; hard-coding
        them would give every site that company's login page.
        """
        offenders = []
        for selector, declarations in css_rules("swift-login.css"):
            if "swift-login" not in selector:
                continue
            # Error states are exempt on purpose. Red means "this went wrong"
            # in every theme, and tying it to the brand would make the errors
            # invisible on exactly the preset that most needs them to stand
            # out — a red one.
            if re.search(r"invalid|error|danger", selector):
                continue
            for prop in ("background", "background-color", "border-color"):
                for match in re.finditer(
                        rf"(?:^|;)\s*{prop}\s*:\s*([^;]+)", declarations):
                    value = match.group(1)
                    # Neutrals are structure, not brand: white cards, dark
                    # scrims and translucent glass are the same on every theme.
                    for literal in re.findall(r"#[0-9a-fA-F]{3,8}", value):
                        rgb = literal.lstrip("#")
                        if len(rgb) == 3:
                            rgb = "".join(c * 2 for c in rgb)
                        r, g, b = (int(rgb[i:i + 2], 16) for i in (0, 2, 4))
                        spread = max(r, g, b) - min(r, g, b)
                        if spread > 40:      # a colour, not a grey or near-grey
                            offenders.append(f"{selector[:60]} -> {literal}")
        self.assertEqual(
            offenders, [],
            f"these paint a fixed brand colour instead of the preset's: "
            f"{offenders}")

    def test_the_centred_card_stays_readable_over_either_backdrop(self):
        """Two backdrops, two guarantees, and both have to hold.

        The shipped photograph is known to be dark — measured at 0.04 average —
        so it can be shown vividly under a light card. An uploaded one is an
        unknown quantity, and the commonest mistake is a logo, which is a white
        field, so that path uses a heavier wash and a darker card. The page
        tells the two apart with a class, and each has to clear 4.5:1 on its
        own worst case.
        """
        def linear(channel):
            channel /= 255
            return channel / 12.92 if channel <= 0.04045 else \
                ((channel + 0.055) / 1.055) ** 2.4

        def layers(selector_test):
            """The card's paint and the shell's wash, for one of the two paths."""
            card = shell = None
            for selector, declarations in css_rules("swift-login.css"):
                if "swift-login-Centered" not in selector:
                    continue
                if not selector_test(selector):
                    continue
                leaves = {part.strip().split()[-1] for part in selector.split(",")
                          if part.strip()}
                found = re.findall(
                    r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)",
                    declarations)
                if not found:
                    continue
                if leaves & {".page-card", ".login-content"}:
                    card = max(found, key=lambda c: float(c[3]))
                elif leaves & {".swift-login-shell"}:
                    shell = max(found, key=lambda c: float(c[3]))
            return card, shell

        CASES = (
            # name, matches the custom-bg path, worst backdrop it must survive
            ("the shipped photograph",
             lambda sel: "custom-bg" not in sel, 0.20),
            ("an uploaded picture",
             lambda sel: "custom-bg" in sel, 1.0),
        )

        for name, matcher, worst in CASES:
            with self.subTest(backdrop=name):
                card, shell = layers(matcher)
                self.assertIsNotNone(card, f"{name}: the card has no paint")
                self.assertIsNotNone(shell, f"{name}: the shell has no wash")

                def luminance(colour):
                    return (0.2126 * linear(float(colour[0]))
                            + 0.7152 * linear(float(colour[1]))
                            + 0.0722 * linear(float(colour[2])))

                behind = worst * (1 - float(shell[3])) \
                    + luminance(shell) * float(shell[3])
                on_card = behind * (1 - float(card[3])) \
                    + luminance(card) * float(card[3])
                contrast = 1.05 / (on_card + 0.05)

                self.assertGreaterEqual(
                    round(contrast, 2), 4.5,
                    f"over {name} at its worst, the card leaves white text at "
                    f"{contrast:.2f}:1 — below the readable floor")

    def test_the_login_backdrop_is_not_painted_on_the_body(self):
        """This app forces the body transparent, so a backdrop there is lost.

        swift-backdrops.css carries
        `html[data-swift-themed] body { background: transparent !important }`
        so the desk's own backdrop can show through the chrome. The login page
        is themed too, so a backdrop set on <body> was overruled by this app's
        own stylesheet — the whole layout came out white, taking its
        white-on-photograph text with it. It has to go on an element of ours.
        """
        for selector, declarations in css_rules("swift-login.css"):
            if not re.search(r"background(-image)?\s*:", declarations):
                continue
            for part in selector.split(","):
                part = part.strip()
                # A rule that ends at the body itself, rather than reaching
                # into something inside it.
                if re.fullmatch(r"body(\.[\w-]+)*", part):
                    self.fail(
                        f"{part} paints a background on the body, which "
                        f"swift-backdrops.css overrides with !important — it "
                        f"will never be seen")

    def test_the_login_wrapper_is_not_a_second_card(self):
        """Frappe already draws the card. Painting the wrapper too stacks them.

        .for-login is the section around .page-card, so giving both a surface,
        a border and a shadow put one panel behind the other.
        """
        for selector, declarations in css_rules("swift-login.css"):
            if "for-login" not in selector or "page-card" in selector:
                continue
            painted = re.search(r"(?:^|;)\s*background\s*:([^;]+)", declarations)
            if painted and painted.group(1).strip() not in ("none", "transparent"):
                self.fail(
                    f"{selector[:70]} gives the section its own surface, so it "
                    f"renders as a second card behind Frappe's own")

    def test_autofilled_fields_do_not_turn_into_pale_boxes(self):
        """Chrome paints an autofilled field with its own colour, by UA rule.

        An ordinary background declaration cannot reach it: the field turns
        solid pale blue the moment a saved password is offered, which on a
        glass card over a photograph is the design coming apart at exactly the
        moment most people meet the page. Only an inset shadow tall enough to
        cover the control paints over it.
        """
        css = read_css("swift-login.css")
        self.assertIn(
            ":-webkit-autofill", css,
            "nothing handles autofill, so a saved password turns the field "
            "into Chrome's pale blue box")

        rules = [(sel, dec) for sel, dec in css_rules("swift-login.css")
                 if ":-webkit-autofill" in sel]
        painted = [dec for _sel, dec in rules if "-webkit-box-shadow" in dec]
        self.assertTrue(
            painted,
            "autofill is mentioned but never painted over — only an inset "
            "-webkit-box-shadow can override Chrome's own fill")

        self.assertTrue(
            any("-webkit-text-fill-color" in dec for _sel, dec in rules),
            "the fill is covered but the text colour is not, so autofilled "
            "text keeps Chrome's dark ink on whatever is painted behind it")

    def test_every_state_frappes_script_can_produce_is_styled(self):
        """The fields were styled empty and idle. They are rarely either.

        Frappe's login script marks a group invalid, writes into .field-error,
        shows .login-error-banner and disables the secondary actions. All of
        that is styled by Frappe for a white card, so on glass it arrives as
        pale red on pale red, or as a disabled button that looks live.
        """
        css = read_css("swift-login.css")
        for state, what in (
            (".form-group.invalid", "a field marked invalid"),
            (".field-error", "the message under a field"),
            (".login-error-banner", "the banner above the form"),
            (":disabled", "a disabled action"),
            (":focus", "the focused field"),
        ):
            self.assertIn(
                state, css,
                f"{what} is left to Frappe's own styling, which is built for a "
                f"white card")

        # The messages need a surface of their own: the card is translucent, so
        # how bright it is depends on the picture behind it, and bare red text
        # cannot be guaranteed to clear the floor wherever that is pale.
        for selector, declarations in css_rules("swift-login.css"):
            if ".field-error" not in selector and ".login-error-banner" not in selector:
                continue
            if "svg" in selector:
                continue
            if "swift-login-Centered" not in selector:
                continue
            self.assertRegex(
                declarations, r"background\s*:",
                f"{selector[:60]} leaves the error as bare text on glass")

    def test_the_login_page_fits_the_screen_it_is_on(self):
        """The page must not scroll, on any screen, and must not trap anyone.

        Frappe's own login stylesheet gives .page-content-wrapper 60px of top
        padding and a min-height, so a full-viewport shell inside it comes out
        taller than the screen by exactly that much — a scrollbar on every
        login. And 100vh on a phone is the viewport with the browser chrome
        hidden, which is taller than what you can see.
        """
        css = read_css("swift-login.css")

        self.assertRegex(
            css, r"\.page-content-wrapper\s*\{[^}]*padding-top:\s*0",
            "Frappe's 60px of wrapper padding is still there, so the page is "
            "taller than the screen and scrolls")

        self.assertIn(
            "100dvh", css,
            "the shell is sized in vh only, which on a phone is taller than "
            "the visible viewport")

        # A page that never scrolls is only right while everything fits. On a
        # short screen the button has to stay reachable.
        self.assertRegex(
            css, r"@media\s*\(max-height:",
            "nothing adapts to a short screen, so on a landscape phone the "
            "sign-in button sits below the fold with no way to reach it")

        # The panel beside the form is a second screenful once stacked.
        narrow = re.search(
            r"@media\s*\(max-width:\s*899\.98px\)\s*\{(.*?)\n\}", css, re.S)
        self.assertIsNotNone(
            narrow, "nothing responds at the tablet breakpoint")
        self.assertIn(
            "swift-login-brand", narrow.group(1),
            "the brand panel is still shown on narrow screens, where it "
            "stacks under the form and becomes a second screenful")

    def test_the_tagline_setting_is_what_the_page_prints(self):
        """The line under the title is Login Tagline, not Frappe's wording.

        Frappe hard-codes "Welcome! Please sign in to continue." there. The
        setting existed and was simply never read, so changing it did nothing.
        """
        with open(self.TEMPLATE) as handle:
            template = handle.read()

        # The call contains nested parentheses — _('Sign In') — so a lazy
        # "up to the first )" stops inside the first argument.
        headings = re.findall(r"logo_section\((.*?)\)\s*\}\}", template)
        self.assertTrue(headings, "the page has no heading section at all")

        sign_in = [h for h in headings if "Sign In" in h]
        self.assertTrue(sign_in, "the sign-in heading is gone")
        for call in sign_in:
            self.assertIn(
                "login_tagline", call,
                "the sign-in subtitle ignores Login Tagline, so the setting "
                "changes nothing on the page")
            self.assertIn(
                "or _(", call,
                "no fallback: a site that has set no tagline would get a blank "
                "line where Frappe's own wording used to be")

    def test_the_palette_reaches_the_login_page(self):
        """Every themed rule on this page reads var(--swift-accent).

        The variables come from the preset stylesheet, which is keyed on an
        attribute of <html> — and this page does not own that tag. Without them
        the button's fill, the borders and the surfaces are all invalid at
        computed-value time and drop, and the page renders unstyled however
        much CSS is aimed at it.
        """
        with open(self.TEMPLATE) as handle:
            template = handle.read()
        self.assertIn(
            "theme_variables", template,
            "the palette is never written into the page")

        from swift_theme.www.login import ROLE_VARS
        boot = read_js("swift-boot.js")
        for role, names in ROLE_VARS.items():
            for name in names:
                self.assertIn(
                    name, boot,
                    f"{name} is written on the login page but the desk's own "
                    f"script does not know it — the two have drifted")

    def test_the_background_image_setting_reaches_the_page(self):
        """Centered is built around the image; it used to be dropped there.

        The image was only ever applied to the brand panel, which that layout
        hides — so the one layout designed around a photograph never showed one.
        """
        self.assertIn(
            "--swift-login-bg", self.template(),
            "login_bg_image is stored but never reaches the page")
        self.assertIn(
            "var(--swift-login-bg", read_css("swift-login.css"),
            "nothing paints the background image the setting provides")

    def test_no_credentials_are_committed_anywhere_in_the_app(self):
        """Guards against the leaked pair reappearing in any shipped file."""
        app_root = frappe.get_app_path(APP)
        leaked = re.compile(r"iamaliraza777@gmail\.com|its-alikhokher")
        offenders = []
        for root, dirs, files in os.walk(app_root):
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
            for name in files:
                if not name.endswith((".html", ".js", ".json", ".py")):
                    continue
                # Skip tests — this file contains the pattern by definition.
                if name.startswith("test_"):
                    continue
                path = os.path.join(root, name)
                with open(path, errors="ignore") as f:
                    body = f.read()
                for match in leaked.finditer(body):
                    line = body[: match.start()].count("\n") + 1
                    context = body.splitlines()[line - 1]
                    # A copyright byline is fine; a credential is not.
                    if "opyright" in context:
                        continue
                    # Publisher metadata is fine too — the marketplace requires
                    # a contact address, and it is the address on its own that
                    # appears there. What this test exists to catch is the
                    # address next to the password it was leaked with, which is
                    # a different thing from an author field.
                    if re.match(r"\s*(app_email|app_publisher|author\w*)\s*=", context):
                        continue
                    offenders.append(f"{path}:{line}")
        self.assertEqual(offenders, [], f"credentials found in: {offenders}")
