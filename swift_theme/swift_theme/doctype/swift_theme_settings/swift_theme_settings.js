frappe.ui.form.on("Swift Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Apply Now (preview)"), () => {
            frappe.call({ method: "swift_theme.api.boot.get_effective_prefs" }).then(r => {
                if (window.SwiftTheme && r.message) window.SwiftTheme.applyPrefs(r.message);
                frappe.show_alert({message: __("Swift Theme reloaded"), indicator: "green"});
            });
        });

        toggleFieldVisibility(frm);
    },
    
    color_mode(frm) {
        toggleFieldVisibility(frm);
    },
    
    enable_sounds(frm) {
        frm.toggle_display("volume_level", frm.doc.enable_sounds == 1);
        frm.toggle_display("sound_events", frm.doc.enable_sounds == 1);
    }
});

function toggleFieldVisibility(frm) {
    // Toggle Preset Themes fields
    frm.toggle_display("active_preset", frm.doc.color_mode === "Preset Themes");
    
    // Toggle Custom Gradient fields
    const isCustomGradient = frm.doc.color_mode === "Custom Gradient";
    frm.toggle_display("gradient_start", isCustomGradient);
    frm.toggle_display("gradient_end", isCustomGradient);
}
