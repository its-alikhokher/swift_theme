/* Swift Theme — the theme fields on the User form

   These are Custom Fields this app adds to User. Whether they can actually be
   changed is decided on the server, in api.boot.set_user_pref: the colour
   fields need the theme switcher to be on and the user to be allowed to switch.

   Left alone, the form offered every one of them as editable and the save was
   simply refused, or the value was stored and then ignored. So the form is
   made to agree with the server: what cannot take effect is shown read-only
   rather than looking available.

   Read-only, not hidden — a user should still be able to see what their theme
   is set to, and a field that vanishes reads as a bug. */

frappe.ui.form.on("User", {
    refresh(frm) {
        const boot = (frappe.boot && frappe.boot.swift_theme) || {};

        // Exactly the set the server guards behind can_switch_theme.
        const colourFields = ["swift_preset", "swift_primary", "swift_secondary"];
        const mayChangeColours = !!(boot.enable_switcher && boot.can_switch_theme);

        colourFields.forEach((fieldname) => {
            if (!frm.get_field(fieldname)) return;
            frm.set_df_property(fieldname, "read_only", mayChangeColours ? 0 : 1);
            frm.set_df_property(
                fieldname, "description",
                mayChangeColours ? "" : __("The theme switcher is turned off in Swift Theme Settings.")
            );
        });

        frm.refresh_fields(colourFields.filter((f) => frm.get_field(f)));
    },
});
