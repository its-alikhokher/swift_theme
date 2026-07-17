frappe.ui.form.on("Swift Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Apply Now (preview)"), () => {
            frappe.call({ method: "swift_theme.api.boot.get_effective_prefs" }).then(r => {
                if (window.SwiftTheme && r.message) window.SwiftTheme.applyPrefs(r.message);
                frappe.show_alert({message: __("Swift Theme reloaded"), indicator: "green"});
            });
        });

        frm.add_custom_button(__("Copy Export JSON"), () => {
            navigator.clipboard.writeText(frm.doc.export_preset_json || "");
            frappe.show_alert({message: __("Copied"), indicator: "green"});
        });

        toggleAccentVisibility(frm);
    },
    default_accent(frm) { livePreview(frm); },
    default_theme(frm) {
        toggleAccentVisibility(frm);
        livePreview(frm);
    },
    default_density(frm) { livePreview(frm); },
    default_radius(frm) { livePreview(frm); },
    default_font_scale(frm) { livePreview(frm); },
    default_font_family(frm) { livePreview(frm); },
});

function toggleAccentVisibility(frm) {
    // When a Full Theme is active, the theme owns its accent — hide the picker.
    const hasFullTheme = !!frm.doc.default_theme;
    frm.toggle_display("default_accent", !hasFullTheme);
    frm.toggle_display("brand_hex_override", !hasFullTheme);
    if (hasFullTheme) {
        frm.set_df_property("default_theme", "description",
            __("Full theme provides its own accent color. Clear this field to pick an accent manually."));
    } else {
        frm.set_df_property("default_theme", "description", "");
    }
}

function livePreview(frm) {
    if (!window.SwiftTheme) return;
    window.SwiftTheme.applyPrefs({
        accent: frm.doc.default_accent,
        theme: frm.doc.default_theme,
        density: frm.doc.default_density,
        radius: frm.doc.default_radius,
        font_scale: frm.doc.default_font_scale,
        font_family: frm.doc.default_font_family,
        navbar_variant: frm.doc.navbar_variant,
        sidebar_variant: frm.doc.sidebar_variant,
    });
}
