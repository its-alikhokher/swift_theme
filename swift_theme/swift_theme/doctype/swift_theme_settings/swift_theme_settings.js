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
    },
    default_accent(frm) { livePreview(frm); },
    default_theme(frm) { livePreview(frm); },
    default_density(frm) { livePreview(frm); },
    default_radius(frm) { livePreview(frm); },
    default_font_scale(frm) { livePreview(frm); },
    default_font_family(frm) { livePreview(frm); },
});

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
