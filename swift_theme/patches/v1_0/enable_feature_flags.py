"""Turn the Swift Theme feature switches back on.

An earlier release dropped these fields from Swift Theme Settings while the
desk JS still gated on them, so every install ended up with the theme
switcher, command palette and focus mode silently disabled — the stored `0`
is leftover state from that period, not a choice anyone made in the UI.

Runs once, and only over values that are still falsy, so a deliberate
"off" set after this patch is never reverted.
"""

import frappe

FLAGS = [
    "enable_switcher",
    "enable_command_palette",
    "enable_focus_mode",
    "enable_perf_mode",
    "enable_styled_scrollbar",
    "enable_toast_theming",
    "enable_print_theming",
]


def execute():
    if not frappe.db.exists("DocType", "Swift Theme Settings"):
        return

    settings = frappe.get_single("Swift Theme Settings")
    changed = False

    for flag in FLAGS:
        if not settings.meta.has_field(flag):
            continue
        if not settings.get(flag):
            settings.set(flag, 1)
            changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save(ignore_permissions=True)
