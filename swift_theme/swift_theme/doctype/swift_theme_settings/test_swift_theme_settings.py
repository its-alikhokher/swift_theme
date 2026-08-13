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
    "navbar_variant", "sidebar_variant", "pin_behavior",
    "enable_switcher", "enable_command_palette", "enable_focus_mode",
    "enable_perf_mode", "enable_styled_scrollbar", "enable_toast_theming",
    "enable_print_theming", "print_font_family",
    "brand_name", "brand_logo", "brand_logo_dark", "brand_favicon",
    "login_layout", "login_bg_image", "login_tagline", "login_show_signup",
    "enable_auto_dark", "auto_dark_start", "auto_dark_end",
    "enable_sounds", "volume_level", "sound_events",
    "custom_css", "custom_js",
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

    def test_custom_js_is_administrator_only(self):
        """Custom JS runs on every desk page — System Manager is too broad."""
        settings = frappe.get_single("Swift Theme Settings")
        previous = settings.custom_js
        user = frappe.session.user
        try:
            frappe.set_user("Guest")  # any non-Administrator session
            settings = frappe.get_single("Swift Theme Settings")
            settings.custom_js = "console.log('injected')"
            with self.assertRaises(frappe.PermissionError):
                settings.save(ignore_permissions=True)
        finally:
            frappe.set_user(user)
            settings = frappe.get_single("Swift Theme Settings")
            settings.custom_js = previous
            settings.save(ignore_permissions=True)
            frappe.clear_cache()


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
                set_user_pref("swift_preset", "Crimson Red")
            with self.assertRaises(frappe.PermissionError):
                set_user_pref("swift_primary", "#123456")
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

    def test_pin_behavior_is_exposed_to_the_client(self):
        """CSS keys off data-swift-pin, which boot.js derives from this."""
        self.assertIn("pin_behavior", get_effective_prefs())

    def test_sounds_config_is_shipped_in_boot(self):
        prefs = get_effective_prefs()
        self.assertIn("sounds", prefs)
        self.assertIn("enabled", prefs["sounds"])
        self.assertIn("files", prefs["sounds"])

    def test_saved_value_is_visible_to_the_next_read(self):
        with no_user_preset():
            with settings_patched(active_preset="Emerald Luxury"):
                prefs = get_effective_prefs()
        self.assertEqual(prefs["preset_name"], "Emerald Luxury")
        self.assertEqual(prefs["preset"], "emerald-luxury")
        self.assertEqual(prefs["theme_css"], "/assets/swift_theme/css/themes/emerald-luxury.css")

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
            frappe.db.set_value("User", user, "swift_preset", "Midnight Pro")

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
            frappe.db.set_value("User", user, "swift_preset", "Midnight Pro")
            with settings_patched(login_tagline="Unrelated change"):
                self.assertEqual(
                    frappe.db.get_value("User", user, "swift_preset"), "Midnight Pro"
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
                "User", user, {"swift_preset": "Crimson Red", "swift_primary": "#0abab5"}
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
            with settings_patched(color_mode="Theme Preset", active_preset="Emerald Luxury"):
                frappe.db.set_value("User", user, "swift_preset", "Crimson Red")
                self.assertEqual(get_effective_prefs()["preset_name"], "Crimson Red")

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
            with settings_patched(active_preset="Emerald Luxury"):
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


class TestSwiftThemeColors(IntegrationTestCase):
    def test_theme_config_flattens_colours(self):
        """login.js reads config.primary, not config.colors.primary."""
        with settings_patched(color_mode="Theme Preset", active_preset="Midnight Pro"):
            config = get_active_theme_config()

        expected = PREMIUM_THEMES["Midnight Pro"]["colors"]
        self.assertEqual(config["primary"], expected["primary"])
        self.assertEqual(config["secondary"], expected["secondary"])
        # bg1/bg2 are what the page's gradient variables bind to.
        self.assertEqual(config["bg1"], expected["bg_body"])
        self.assertEqual(config["bg2"], expected["bg_card"])

    def test_dark_preset_reports_dark_mode(self):
        with settings_patched(color_mode="Theme Preset", active_preset="Midnight Pro"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], True)
        with settings_patched(color_mode="Theme Preset", active_preset="Pearl White"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], False)

    def test_every_preset_defines_the_colours_the_client_reads(self):
        for name, data in PREMIUM_THEMES.items():
            for key in ("primary", "secondary", "bg_body", "bg_card"):
                self.assertIn(key, data["colors"], f"preset {name} is missing {key}")
            self.assertIn(data["mode"], ("light", "dark"), f"preset {name} has no valid mode")

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
            apply_theme("Midnight Pro")
            stored = frappe.db.get_value("User", user, "desk_theme")
            options = frappe.get_meta("User").get_field("desk_theme").options.split("\n")
            self.assertIn(stored, options)
            self.assertEqual(frappe.db.get_value("User", user, "swift_preset"), "Midnight Pro")
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


class TestSwiftThemeStyling(IntegrationTestCase):
    """Options and injected elements must have styling that actually exists."""

    def test_every_layout_option_has_a_css_rule(self):
        """Options like "Minimal"/"Bordered" existed with no styling behind them."""
        css = read_css("swift-layout.css")
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
            slug = data["value"]
            path = frappe.get_app_path(APP, "public", "css", "themes", f"{slug}.css")
            self.assertTrue(os.path.exists(path), f"{name} has no stylesheet at {path}")
            self.assertIsNotNone(preset_stylesheet(slug))

            body = COMMENT_RE.sub("", open(path).read())
            self.assertIn(f'html[data-swift-preset="{slug}"]', body)
            # A preset file must not style any other preset.
            for other in PREMIUM_THEMES.values():
                if other["value"] != slug:
                    self.assertNotIn(f'data-swift-preset="{other["value"]}"', body)

    def test_preset_dropdown_matches_the_shipped_stylesheets(self):
        """A preset offered in Settings with no file would silently do nothing."""
        for option in settings_json_options("active_preset"):
            self.assertIn(option, PREMIUM_THEMES, f"{option!r} is not a known preset")
            slug = PREMIUM_THEMES[option]["value"]
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
        """The wash needs the rule, the keyframes and a per-theme gradient."""
        base = read_css("swift-preset-base.css")
        self.assertIn("body::before", base)
        self.assertIn("swift-ambient-drift", base)
        self.assertIn("--swift-ambient", base)
        for data in PREMIUM_THEMES.values():
            path = os.path.join(CSS_DIR, "themes", f"{data['value']}.css")
            self.assertIn("--swift-ambient", open(path).read(),
                          f"{data['value']} defines no ambient background")

    def test_performance_mode_uses_the_attribute_boot_actually_sets(self):
        """The old rule keyed off data-swift-performance, which nothing set."""
        css = read_css("swift-desk.css")
        self.assertNotIn("data-swift-performance", css)
        self.assertIn("data-swift-perf", css)

    def test_hidden_sidebar_has_a_css_rule(self):
        """Alt+B set data-swift-sidebar="off" but nothing styled it."""
        self.assertIn('data-swift-sidebar="off"', read_css("swift-desk.css"))

    def test_toasts_are_anchored_to_the_top(self):
        """Frappe pins #alert-container to bottom:0; save confirmations belong up top."""
        css = read_css("swift-toast.css")
        self.assertIn("#alert-container", css)
        self.assertIn("bottom: auto", css)

    def test_pin_and_restore_controls_are_styled(self):
        css = read_css("swift-desk.css")
        for selector in (".swift-pin-btn", ".swift-pinned", ".swift-sidebar-restore"):
            self.assertIn(selector, css, f"{selector} is injected by JS but never styled")

    def test_login_layouts_are_styled(self):
        css = read_css("login.css")
        for option in settings_json_options("login_layout"):
            self.assertIn(f'data-swift-login-layout="{option}"', css)

    def test_pin_behaviour_tokens_agree_between_js_and_css(self):
        """boot.js maps the label to a short token; CSS must use the same one."""
        js = read_js("swift-boot.js")
        css = read_css("swift-desk.css")
        for label in settings_json_options("pin_behavior"):
            self.assertIn(f'"{label}"', js, f"boot.js does not map pin behaviour {label!r}")
        # "click" is the neutral default and intentionally has no rule.
        for token in ("hover", "always"):
            self.assertIn(f'data-swift-pin="{token}"', css)


class TestSwiftThemeClientContract(IntegrationTestCase):
    """Guards on the shipped JS.

    The defining bug of this app was a server event with no client listener —
    invisible to any Python-only assertion.
    """

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

    def test_sidebar_does_not_re_enter_its_own_mutation_observer(self):
        """Reordering pinned items re-triggered the observer every 120ms."""
        js = read_js("swift-sidebar.js")
        self.assertIn("withObserverPaused", js)
        self.assertIn("takeRecords", js)

    def test_presets_are_offered_in_frappes_own_theme_dialog(self):
        """One place to switch theme, not two competing ones."""
        js = read_js("swift-theme-dialog.js")
        self.assertIn("frappe.ui.ThemeSwitcher", js)
        self.assertIn("setup_dialog", js)
        self.assertIn("setCustomColors", js, "custom pair must be pickable there too")
        self.assertIn("clearPersonalTheme", js, "and a way back to the site default")

    def test_theme_dialog_is_loaded_on_the_desk(self):
        self.assertIn(
            "/assets/swift_theme/js/swift-theme-dialog.js",
            frappe.get_hooks("app_include_js") or [],
        )

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
    def test_seed_settings_is_idempotent(self):
        """after_migrate runs it on every migrate; it must not clobber choices."""
        from swift_theme.install import _seed_settings

        with settings_patched(active_preset="Rose Gold", enable_switcher=0):
            _seed_settings()
            settings = frappe.get_single("Swift Theme Settings")
            self.assertEqual(settings.active_preset, "Rose Gold")
            self.assertEqual(settings.enable_switcher, 0)

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


class TestSwiftThemeLoginPage(IntegrationTestCase):
    TEMPLATE = frappe.get_app_path(APP, "www", "login.html")

    def render(self):
        from frappe.website.serve import get_response_content

        with as_guest():
            return get_response_content("login")

    def test_login_page_renders_for_guests(self):
        self.assertNotIn("Server Error", self.render())

    def test_login_template_has_no_hardcoded_credentials(self):
        """The shipped page carried a real email and password in value=""."""
        with open(self.TEMPLATE) as f:
            template = f.read()
        for field in ('id="usr"', 'id="pwd"'):
            block = template.split(field, 1)[1].split(">", 1)[0]
            self.assertNotIn("value=", block, f"{field} must not ship a value")

    def test_login_form_posts_to_the_real_auth_endpoint(self):
        """It used to fake a setTimeout and show an alert instead."""
        self.assertIn('action="/api/method/login"', self.render())

    def test_login_page_is_themed_server_side(self):
        with settings_patched(color_mode="Theme Preset", active_preset="Midnight Pro"):
            html = self.render()
        primary = PREMIUM_THEMES["Midnight Pro"]["colors"]["primary"]
        self.assertIn(f"--primary: {primary}", html)

    def test_login_page_marks_dark_presets(self):
        with settings_patched(color_mode="Theme Preset", active_preset="Midnight Pro"):
            self.assertIn("dark-mode", self.render())

    def test_login_layout_reaches_the_markup(self):
        for layout in settings_json_options("login_layout"):
            with settings_patched(login_layout=layout):
                html = self.render()
            self.assertIn(f'data-swift-login-layout="{layout}"', html)

    def test_login_page_exposes_a_csrf_slot(self):
        self.assertIn("data-csrf-token", self.render())

    def test_login_page_sanitises_the_redirect_target(self):
        """Echoing redirect-to unchecked would make this an open redirect."""
        from frappe.www.login import sanitize_redirect

        source = open(frappe.get_app_path(APP, "www", "login.py")).read()
        self.assertIn("sanitize_redirect", source)
        self.assertTrue(callable(sanitize_redirect))

    def test_login_javascript_performs_a_real_login(self):
        js = read_js("login.js")
        self.assertNotIn("alert(", js)
        self.assertNotIn("Login functionality would connect", js)
        self.assertIn("/api/method/login", js)
        self.assertIn("X-Frappe-CSRF-Token", js)

    def test_login_javascript_reads_the_documented_sound_contract(self):
        """JS once read sound_file/volume_level while the API sent sound/volume."""
        js = read_js("login.js")
        self.assertIn("sound_file", js)
        self.assertNotIn("volume_level", js, "volume arrives pre-scaled as `volume`")

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
                    offenders.append(f"{path}:{line}")
        self.assertEqual(offenders, [], f"credentials found in: {offenders}")
