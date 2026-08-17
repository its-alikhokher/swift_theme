"""Turn the Swift Theme feature switches back on.

An earlier release dropped these fields from Swift Theme Settings while the
desk JS still gated on them, so every install ended up with the theme
switcher, command palette and focus mode silently disabled — the stored `0`
is leftover state from that period, not a choice anyone made in the UI.

Runs once, and only over values that are still falsy, so a deliberate
"off" set after this patch is never reverted.

Writes each flag on its own rather than saving the document, because a save
validates every other field too. On a site upgrading from the old schema that
meant this patch died on a stale `color_mode` it has nothing to do with, and
took the entire `bench migrate` down with it before the patch that fixes
`color_mode` had a chance to run.
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

    meta = frappe.get_meta("Swift Theme Settings")

    for flag in FLAGS:
        if not meta.has_field(flag):
            continue
        if not frappe.db.get_single_value("Swift Theme Settings", flag):
            frappe.db.set_single_value("Swift Theme Settings", flag, 1)
