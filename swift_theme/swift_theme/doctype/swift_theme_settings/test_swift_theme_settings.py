"""Regression tests for Swift Theme.

Each test here maps to a defect that shipped silently: the desk JS gated on
Settings fields that no longer existed, the login page called whitelisted
methods as Guest, and several CSS attribute values had no rule behind them.
None of those raised an exception — they just quietly did nothing, which is
exactly the class of bug that needs a test rather than a manual check.
"""

import os
import re
from contextlib import contextmanager

import frappe
from frappe.tests import IntegrationTestCase

from swift_theme.api.boot import get_effective_prefs
from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
    PREMIUM_THEMES,
    get_active_theme_config,
    play_sound,
)

CSS_DIR = frappe.get_app_path("swift_theme", "public", "css")

# Every Settings field read by api/boot.py or the desk JS. If one goes missing
# again the features it gates fail silently, so assert the whole set.
REQUIRED_SETTINGS_FIELDS = [
    "color_mode", "active_preset", "gradient_start", "gradient_end",
    "default_accent", "default_theme", "default_density", "default_radius",
    "default_font_scale", "default_font_family", "brand_hex_override",
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


def read_css():
    blob = ""
    for name in os.listdir(CSS_DIR):
        if name.endswith(".css"):
            with open(os.path.join(CSS_DIR, name)) as f:
                blob += f.read()
    return blob


@contextmanager
def settings_patched(**values):
    """Apply Settings values for the duration of a test, then put them back."""
    doc = frappe.get_single("Swift Theme Settings")
    previous = {k: doc.get(k) for k in values}
    for k, v in values.items():
        doc.set(k, v)
    doc.save(ignore_permissions=True)
    frappe.clear_cache()
    try:
        yield doc
    finally:
        doc = frappe.get_single("Swift Theme Settings")
        for k, v in previous.items():
            doc.set(k, v)
        doc.save(ignore_permissions=True)
        frappe.clear_cache()


@contextmanager
def as_guest():
    original = frappe.session.user
    frappe.set_user("Guest")
    try:
        yield
    finally:
        frappe.set_user(original)


class TestSwiftThemeSettings(IntegrationTestCase):
    # ---------- schema ----------

    def test_settings_has_every_field_the_code_reads(self):
        """The rewrite dropped ~25 fields while boot.py still read them."""
        meta = frappe.get_meta("Swift Theme Settings")
        missing = [f for f in REQUIRED_SETTINGS_FIELDS if not meta.has_field(f)]
        self.assertEqual(missing, [], f"Swift Theme Settings is missing: {missing}")

    def test_sound_event_child_table_is_configured_as_a_child_table(self):
        meta = frappe.get_meta("Swift Theme Sound Event")
        self.assertTrue(meta.istable, "Swift Theme Sound Event must be a child table")
        # autoname/unique are meaningless on a child table and the unique index
        # would have blocked the same event key across parents.
        self.assertFalse(meta.autoname, "child tables are hash-named")
        self.assertFalse(meta.get_field("event_key").unique)

    # ---------- boot preferences ----------

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

    def test_guest_prefs_exclude_custom_code(self):
        """The login page needs prefs, but Guests must not receive custom JS/CSS."""
        with as_guest():
            prefs = get_effective_prefs()
        self.assertNotIn("custom_js", prefs)
        self.assertNotIn("custom_css", prefs)
        self.assertIn("login_layout", prefs, "login page still needs its layout")

    # ---------- theme config used by the login page ----------

    def test_theme_config_is_readable_by_guest(self):
        with as_guest():
            config = get_active_theme_config()
        self.assertTrue(config)

    def test_theme_config_flattens_colours(self):
        """login.js reads config.primary, not config.colors.primary."""
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
            config = get_active_theme_config()

        expected = PREMIUM_THEMES["Midnight Pro"]["colors"]
        self.assertEqual(config["primary"], expected["primary"])
        self.assertEqual(config["secondary"], expected["secondary"])
        # bg1/bg2 are what the page's gradient variables bind to.
        self.assertEqual(config["bg1"], expected["bg_body"])
        self.assertEqual(config["bg2"], expected["bg_card"])

    def test_dark_preset_reports_dark_mode(self):
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], True)
        with settings_patched(color_mode="Preset Themes", active_preset="Pearl White"):
            self.assertIs(get_active_theme_config()["is_dark_mode"], False)

    def test_custom_gradient_mode_returns_the_chosen_colours(self):
        with settings_patched(
            color_mode="Custom Gradient", gradient_start="#111111", gradient_end="#222222"
        ):
            config = get_active_theme_config()
        self.assertEqual(config["bg1"], "#111111")
        self.assertEqual(config["bg2"], "#222222")

    def test_gradient_mode_requires_both_colours(self):
        with self.assertRaises(frappe.ValidationError):
            with settings_patched(
                color_mode="Custom Gradient", gradient_start="#111111", gradient_end=""
            ):
                pass

    # ---------- sounds ----------

    def test_play_sound_returns_nothing_when_no_file_is_attached(self):
        """It used to return /assets/.../save.mp3 for files that don't exist."""
        with settings_patched(enable_sounds=1, volume_level=50):
            result = play_sound("save")
        self.assertTrue(result["enabled"])
        self.assertIsNone(result["sound_file"])

    def test_play_sound_scales_volume_to_zero_one(self):
        with settings_patched(enable_sounds=1, volume_level=40):
            self.assertAlmostEqual(play_sound("save")["volume"], 0.4)

    def test_play_sound_clamps_out_of_range_volume(self):
        with settings_patched(enable_sounds=1, volume_level=900):
            self.assertLessEqual(play_sound("save")["volume"], 1.0)

    def test_play_sound_is_silent_when_sounds_are_disabled(self):
        with settings_patched(enable_sounds=0):
            result = play_sound("save")
        self.assertFalse(result["enabled"])
        self.assertIsNone(result["sound_file"])

    def test_play_sound_uses_an_attached_file(self):
        doc = frappe.get_single("Swift Theme Settings")
        previous_rows = [r.as_dict() for r in (doc.sound_events or [])]
        previous_enabled = doc.enable_sounds
        try:
            doc.enable_sounds = 1
            doc.set("sound_events", [])
            doc.append("sound_events", {"event_key": "save", "sound_file": "/files/ping.mp3"})
            doc.save(ignore_permissions=True)
            frappe.clear_cache()
            self.assertEqual(play_sound("save")["sound_file"], "/files/ping.mp3")
        finally:
            doc = frappe.get_single("Swift Theme Settings")
            doc.enable_sounds = previous_enabled
            doc.set("sound_events", [])
            for row in previous_rows:
                doc.append("sound_events", row)
            doc.save(ignore_permissions=True)
            frappe.clear_cache()

    # ---------- instant apply ----------

    def test_saving_settings_broadcasts_to_open_sessions(self):
        """Without this event the desk only updates on a hard refresh."""
        published = []
        original = frappe.publish_realtime

        def spy(event=None, message=None, **kwargs):
            published.append(event)
            return original(event, message, **kwargs)

        frappe.publish_realtime = spy
        try:
            with settings_patched(default_accent="emerald"):
                pass
        finally:
            frappe.publish_realtime = original

        self.assertIn("swift_theme_updated", published)

    def test_saved_value_is_visible_to_the_next_read(self):
        with settings_patched(default_accent="emerald"):
            self.assertEqual(get_effective_prefs()["accent"], "emerald")

    # ---------- CSS / option agreement ----------

    def test_every_layout_option_has_a_css_rule(self):
        """Options like "Minimal"/"Bordered" existed with no styling behind them."""
        css = read_css()
        meta = frappe.get_meta("Swift Theme Settings")
        checks = {
            "sidebar_variant": "data-swift-sidebar-variant",
            "navbar_variant": "data-swift-navbar",
        }
        for fieldname, attr in checks.items():
            for option in filter(None, (meta.get_field(fieldname).options or "").split("\n")):
                self.assertIn(
                    f'{attr}="{option}"',
                    css,
                    f"{fieldname} option {option!r} has no CSS rule",
                )

    def test_hidden_sidebar_has_a_css_rule(self):
        """Alt+B set data-swift-sidebar="off" but nothing styled it."""
        self.assertIn('data-swift-sidebar="off"', read_css())

    def test_pin_and_restore_controls_are_styled(self):
        css = read_css()
        for selector in (".swift-pin-btn", ".swift-pinned", ".swift-sidebar-restore"):
            self.assertIn(selector, css, f"{selector} is injected by JS but never styled")

    # ---------- user theme application ----------

    def test_apply_theme_writes_a_valid_desk_theme(self):
        """desk_theme options are Light/Dark/Automatic — lowercase was invalid."""
        from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
            apply_theme,
        )

        user = frappe.session.user
        previous = frappe.db.get_value("User", user, "desk_theme")
        try:
            apply_theme("Midnight Pro")
            stored = frappe.db.get_value("User", user, "desk_theme")
            options = frappe.get_meta("User").get_field("desk_theme").options.split("\n")
            self.assertIn(stored, options)
        finally:
            frappe.db.set_value("User", user, "desk_theme", previous)

    def test_apply_theme_rejects_an_unknown_theme(self):
        from swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings import (
            apply_theme,
        )

        with self.assertRaises(frappe.ValidationError):
            apply_theme("Not A Real Theme")


class TestSwiftThemeLoginPage(IntegrationTestCase):
    TEMPLATE = frappe.get_app_path("swift_theme", "www", "login.html")

    def render(self):
        from frappe.website.serve import get_response_content

        with as_guest():
            return get_response_content("login")

    def test_login_page_renders_for_guests(self):
        html = self.render()
        self.assertNotIn("Server Error", html)

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
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
            html = self.render()
        primary = PREMIUM_THEMES["Midnight Pro"]["colors"]["primary"]
        self.assertIn(f"--primary: {primary}", html)

    def test_login_page_marks_dark_presets(self):
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
            self.assertIn("dark-mode", self.render())

    def test_login_layout_reaches_the_markup(self):
        for layout in ("Split", "Centered", "Minimal"):
            with settings_patched(login_layout=layout):
                html = self.render()
            self.assertIn(f'data-swift-login-layout="{layout}"', html)

    def test_login_page_exposes_a_csrf_slot(self):
        self.assertIn("data-csrf-token", self.render())

    def test_no_javascript_file_still_fakes_a_login(self):
        js_path = frappe.get_app_path("swift_theme", "public", "js", "login.js")
        with open(js_path) as f:
            js = f.read()
        self.assertNotIn("alert(", js)
        self.assertNotIn("Login functionality would connect", js)
        self.assertIn("/api/method/login", js)

    def test_no_credentials_are_committed_anywhere_in_the_app(self):
        """Guards against the leaked pair reappearing in any shipped file."""
        app_root = frappe.get_app_path("swift_theme")
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
                # A copyright byline is fine; a value="" attribute is not.
                for match in leaked.finditer(body):
                    line = body[: match.start()].count("\n") + 1
                    context = body.splitlines()[line - 1]
                    if "Copyright" in context or "copyright" in context:
                        continue
                    offenders.append(f"{path}:{line}")
        self.assertEqual(offenders, [], f"credentials found in: {offenders}")
