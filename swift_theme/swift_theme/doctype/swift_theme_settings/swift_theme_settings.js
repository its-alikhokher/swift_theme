frappe.ui.form.on("Swift Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Reapply Theme"), () => {
            reloadTheme().then(() => {
                frappe.show_alert({ message: __("Swift Theme reapplied"), indicator: "green" });
            });
        });

        toggleFieldVisibility(frm);
        showSoundHint(frm);
    },

    sound_events(frm) {
        showSoundHint(frm);
    },

    // Saving broadcasts swift_theme_updated to every desk session, but apply it
    // here too so the admin sees the change the instant the save returns.
    after_save() {
        reloadTheme();
    },

    color_mode(frm) {
        toggleFieldVisibility(frm);
    },

    active_preset(frm) {
        previewColors(frm);
    },

    primary_color(frm) {
        previewColors(frm);
    },

    secondary_color(frm) {
        previewColors(frm);
    },

    custom_mode(frm) {
        previewColors(frm);
    },

    custom_strength(frm) {
        previewColors(frm);
    },

    enable_sounds(frm) {
        toggleFieldVisibility(frm);
        showSoundHint(frm);
    },
});

// Sounds enabled with no file attached is a silent no-op — the app ships no
// audio, so say so on the form instead of letting it look broken.
function showSoundHint(frm) {
    frm.dashboard.clear_comment();
    if (!frm.doc.enable_sounds) return;

    const configured = (frm.doc.sound_events || []).filter((row) => row.sound_file);
    if (configured.length) return;

    frm.dashboard.add_comment(
        __(
            "Sounds are enabled but no sound file is attached. Add a row to <b>Sound Events</b>, pick an <b>Event Key</b> and attach an audio file — events without a file stay silent."
        ),
        "yellow",
        true
    );
}

// Live preview before saving, so picking a preset or a colour shows straight
// away instead of only after the save round-trips.
function previewColors(frm) {
    if (!(window.SwiftTheme && window.SwiftTheme.applyColors)) return;

    if (frm.doc.color_mode === "Custom Colors") {
        window.SwiftTheme.applyColors({
            preset: "",
            primary: frm.doc.primary_color,
            secondary: frm.doc.secondary_color,
            // Without these the preview always derived a Dark/Subtle palette,
            // so switching Custom Mode to Light showed nothing until saved.
            mode: frm.doc.custom_mode,
            strength: frm.doc.custom_strength,
        });
        return;
    }

    const catalog = (frappe.boot.swift_theme && frappe.boot.swift_theme.presets) || [];
    const chosen = catalog.find((p) => p.label === frm.doc.active_preset);
    if (!chosen) return;

    window.SwiftTheme.applyColors({
        preset: chosen.key,
        primary: chosen.primary,
        secondary: chosen.secondary,
        theme_css: chosen.css,
    });
}

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
    const isPreset = frm.doc.color_mode === "Theme Preset";
    const isCustom = frm.doc.color_mode === "Custom Colors";

    frm.toggle_display("active_preset", isPreset);
    frm.toggle_display("primary_color", isCustom);
    frm.toggle_display("secondary_color", isCustom);

    const soundsOn = frm.doc.enable_sounds == 1;
    frm.toggle_display("volume_level", soundsOn);
    frm.toggle_display("sound_events", soundsOn);
}
