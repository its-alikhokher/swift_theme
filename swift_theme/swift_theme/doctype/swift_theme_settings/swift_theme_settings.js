frappe.ui.form.on("Swift Theme Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Preview Schemes"), () => {
            window.open("/app/swift-theme-settings#preview", "_blank");
        });
    },
    default_scheme(frm) {
        if (window.SwiftTheme && frm.doc.default_scheme) {
            window.SwiftTheme.apply(frm.doc.default_scheme);
        }
    },
});
