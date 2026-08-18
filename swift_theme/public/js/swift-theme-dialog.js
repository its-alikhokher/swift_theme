/* Swift Theme — presets inside Frappe's own "Switch Theme" dialog

   Frappe's navbar switcher only offers Light / Dark / Automatic. This extends
   that same dialog with the Swift presets, drawn as the same preview cards so
   the whole dialog reads as one list rather than two different widgets.

   Two deliberate choices:
   * The cards are placed in a .theme-grid, which is Frappe's own class, so they
     inherit its card styling instead of duplicating it here.
   * "Custom Colors" is a card like any other; the two pickers only appear once
     it is chosen, so the dialog stays a simple list until you ask for more.

   setup_dialog is wrapped rather than replaced, leaving Frappe's own grid and
   keyboard handling untouched. */

(function () {
    if (!window.frappe) return;

    var CUSTOM_KEY = "__swift_custom__";

    frappe.after_ajax(function () {
        var Switcher = frappe.ui && frappe.ui.ThemeSwitcher;
        if (!Switcher || Switcher.prototype.__swiftExtended) return;
        Switcher.prototype.__swiftExtended = true;

        var originalSetup = Switcher.prototype.setup_dialog;
        Switcher.prototype.setup_dialog = function () {
            originalSetup.call(this);
            try {
                render(this);
            } catch (e) {
                // Frappe's own switcher must keep working even if ours can't.
                console.warn("Swift theme section failed to render", e);
            }
        };
    });

    function boot() {
        return (window.frappe && frappe.boot && frappe.boot.swift_theme) || {};
    }

    function render(switcher) {
        var prefs = boot();
        // Both gates, not just the permission one. Enable Theme Switcher is the
        // site-wide switch, and it has to reach here too: the navbar chip
        // honoured it while this section carried on adding presets to Frappe's
        // own Switch Theme dialog, so turning the switcher off only half worked.
        if (!prefs.enable_switcher) return;          // turned off site-wide
        if (!prefs.can_switch_theme) return;         // restricted to admins
        var presets = prefs.presets || [];
        if (!presets.length) return;

        var $body = switcher.dialog.$body;

        var $section = $(
            '<div class="swift-switch">' +
            '<div class="swift-switch-head">' +
            "<span>" + __("Swift Theme") + "</span>" +
            '<button type="button" class="swift-switch-reset">' + __("Use site default") + "</button>" +
            "</div>" +
            '<div class="theme-grid swift-theme-grid"></div>' +
            '<div class="swift-custom" hidden></div>' +
            "</div>"
        ).appendTo($body);

        var $grid = $section.find(".swift-theme-grid");
        var $custom = $section.find(".swift-custom");

        var activePreset = document.documentElement.getAttribute("data-swift-preset") || "";
        var onCustom = !activePreset && prefs.color_mode === "Custom Colors";

        presets.forEach(function (p) {
            $grid.append(card(p, p.key === activePreset, function () {
                select($grid, p.key);
                $custom.attr("hidden", true);
                window.SwiftTheme.setPreset(p.key);
                frappe.show_alert({ message: __("Theme set to {0}", [p.label]), indicator: "green" });
            }));
        });

        // Custom colours as a card in the same grid; picking it reveals step two.
        $grid.append(card(customPreview(prefs), onCustom, function () {
            select($grid, CUSTOM_KEY);
            $custom.removeAttr("hidden");
            $custom.find("input").first().trigger("focus");
        }));

        buildCustomPanel($custom, $grid, prefs);
        if (onCustom) $custom.removeAttr("hidden");

        $section.find(".swift-switch-reset").on("click", function () {
            if (!(window.SwiftTheme && window.SwiftTheme.clearPersonalTheme)) return;
            window.SwiftTheme.clearPersonalTheme();
            $grid.find("[data-swift-card]").removeClass("selected");
            $custom.attr("hidden", true);
            frappe.show_alert({ message: __("Using the site theme"), indicator: "blue" });
        });
    }

    function customPreview(prefs) {
        return {
            key: CUSTOM_KEY,
            label: __("Custom Colors"),
            mode: prefs.is_dark ? "dark" : "light",
            primary: prefs.primary || "#4f46e5",
            secondary: prefs.secondary || "#7c3aed",
            bg: prefs.is_dark ? "#0f172a" : "#f5f7fa",
            card: prefs.is_dark ? "#1e293b" : "#ffffff",
            muted: prefs.is_dark ? "#94a3b8" : "#64748b",
        };
    }

    /* Mirrors the markup Frappe builds for its own themes, with the preset's
       colours fed in as custom properties so the card previews the real thing. */
    function card(p, selected, onClick) {
        var $card = $(
            '<div data-swift-card="' + p.key + '" class="' + (selected ? "selected" : "") + '">' +
            "<div>" +
            '<div class="background">' +
            '<div><div class="preview-check">' + frappe.utils.icon("tick", "xs") + "</div></div>" +
            '<div class="navbar"></div>' +
            '<div class="p-2">' +
            '<div class="toolbar"><span class="text"></span><span class="primary"></span></div>' +
            '<div class="foreground"></div>' +
            '<div class="foreground"></div>' +
            "</div>" +
            "</div>" +
            "</div>" +
            '<div class="mt-3 text-center"><h5 class="theme-title"></h5></div>' +
            "</div>"
        );

        $card.find(".theme-title").text(p.label);
        $card.attr("title", p.label + " · " + (p.mode === "dark" ? __("Dark") : __("Light"))
            + (p.backdrop && p.backdrop !== "none" ? " · " + p.backdrop : ""));
        $card.find(".background").css({
            "--bg-color": p.bg,
            "--card-bg": p.card,
            "--subtle-accent": p.card,
            "--primary-color": p.primary,
            "--text-light": p.muted,
            "background-color": p.bg,
        });
        $card.find(".primary").css("background", "linear-gradient(135deg," + p.primary + "," + p.secondary + ")");
        $card.find(".text").css("background-color", p.muted);
        $card.find(".foreground").css("background-color", p.card);
        $card.find(".navbar").css("background-color", p.card);

        $card.on("click", onClick);
        return $card;
    }

    function select($grid, key) {
        $grid.find("[data-swift-card]").removeClass("selected");
        $grid.find('[data-swift-card="' + key + '"]').addClass("selected");
    }

    /* Step two: only reached once the Custom Colors card is chosen. */
    function buildCustomPanel($custom, $grid, prefs) {
        $custom.html(
            '<div class="swift-custom-head">' + __("Pick your two colours") + "</div>" +
            '<div class="swift-custom-row">' +
            "<label><span>" + __("Primary") + "</span>" +
            '<input type="color" class="swift-color-primary"></label>' +
            "<label><span>" + __("Secondary") + "</span>" +
            '<input type="color" class="swift-color-secondary"></label>' +
            '<button type="button" class="btn btn-sm btn-primary swift-custom-apply">' +
            __("Apply") + "</button>" +
            "</div>" +
            '<div class="swift-custom-preview"></div>'
        );

        var $primary = $custom.find(".swift-color-primary").val(prefs.primary || "#4f46e5");
        var $secondary = $custom.find(".swift-color-secondary").val(prefs.secondary || "#7c3aed");
        var $preview = $custom.find(".swift-custom-preview");

        function paint() {
            var css = "linear-gradient(135deg," + $primary.val() + "," + $secondary.val() + ")";
            $preview.css("background", css);
            $grid.find('[data-swift-card="' + CUSTOM_KEY + '"] .primary').css("background", css);
        }
        paint();
        $primary.on("input", paint);
        $secondary.on("input", paint);

        $custom.find(".swift-custom-apply").on("click", function () {
            if (!(window.SwiftTheme && window.SwiftTheme.setCustomColors)) return;
            window.SwiftTheme.setCustomColors($primary.val(), $secondary.val());
            select($grid, CUSTOM_KEY);
            frappe.show_alert({ message: __("Custom colours applied"), indicator: "green" });
        });
    }
})();
