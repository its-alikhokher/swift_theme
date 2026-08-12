frappe.ui.form.on("Swift Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Reapply Theme"), () => {
            reloadTheme().then(() => {
                frappe.show_alert({ message: __("Swift Theme reapplied"), indicator: "green" });
            });
        });

        toggleFieldVisibility(frm);
    },

    // Saving broadcasts swift_theme_updated to every desk session, but apply it
    // here too so the admin sees the change the instant the save returns.
    after_save() {
        reloadTheme();
    },

    color_mode(frm) {
        toggleFieldVisibility(frm);
    },

    enable_sounds(frm) {
        toggleFieldVisibility(frm);
    },
});

function reloadTheme() {
    if (window.SwiftTheme && window.SwiftTheme.reload) {
        return Promise.resolve(window.SwiftTheme.reload());
    }
    // Fallback if swift-boot.js hasn't initialised yet.
    return frappe
        .call({ method: "swift_theme.api.boot.get_effective_prefs", freeze: false })
        .then((r) => {
            if (r && r.message && window.SwiftTheme) {
                frappe.boot.swift_theme = r.message;
                window.SwiftTheme.applyPrefs(r.message);
            }
        });
}

function toggleFieldVisibility(frm) {
    const isPreset = frm.doc.color_mode === "Preset Themes";
    const isCustomGradient = frm.doc.color_mode === "Custom Gradient";

    frm.toggle_display("active_preset", isPreset);
    frm.toggle_display("gradient_start", isCustomGradient);
    frm.toggle_display("gradient_end", isCustomGradient);

    const soundsOn = frm.doc.enable_sounds == 1;
    frm.toggle_display("volume_level", soundsOn);
    frm.toggle_display("sound_events", soundsOn);
}
