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

from swift_theme.api.boot import get_effective_prefs, set_user_pref
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
        with settings_patched(default_accent="emerald"):
            self.assertEqual(get_effective_prefs()["accent"], "emerald")

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

    def test_every_preset_defines_the_colours_the_client_reads(self):
        for name, data in PREMIUM_THEMES.items():
            for key in ("primary", "secondary", "bg_body", "bg_card"):
                self.assertIn(key, data["colors"], f"preset {name} is missing {key}")
            self.assertIn(data["mode"], ("light", "dark"), f"preset {name} has no valid mode")

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

    def test_apply_theme_writes_a_valid_desk_theme(self):
        """desk_theme options are Light/Dark/Automatic — lowercase was invalid."""
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

    def test_hidden_sidebar_has_a_css_rule(self):
        """Alt+B set data-swift-sidebar="off" but nothing styled it."""
        self.assertIn('data-swift-sidebar="off"', read_css("swift-desk.css"))

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

        with settings_patched(default_accent="rose", enable_switcher=0):
            _seed_settings()
            settings = frappe.get_single("Swift Theme Settings")
            self.assertEqual(settings.default_accent, "rose")
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
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
            html = self.render()
        primary = PREMIUM_THEMES["Midnight Pro"]["colors"]["primary"]
        self.assertIn(f"--primary: {primary}", html)

    def test_login_page_marks_dark_presets(self):
        with settings_patched(color_mode="Preset Themes", active_preset="Midnight Pro"):
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
