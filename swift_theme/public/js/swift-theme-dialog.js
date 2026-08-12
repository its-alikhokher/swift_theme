/* Swift Theme — presets inside Frappe's own "Switch Theme" dialog

   Frappe's navbar theme switcher only offers Light / Dark / Automatic. This
   extends that same dialog with the Swift presets and a custom colour pair, so
   there is one place to change theme rather than two competing ones.

   It wraps setup_dialog rather than replacing the class, so Frappe's own grid
   and keyboard handling keep working untouched. */

(function () {
    if (!window.frappe) return;

    frappe.after_ajax(function () {
        var Switcher = frappe.ui && frappe.ui.ThemeSwitcher;
        if (!Switcher || Switcher.prototype.__swiftExtended) return;
        Switcher.prototype.__swiftExtended = true;

        var originalSetup = Switcher.prototype.setup_dialog;

        Switcher.prototype.setup_dialog = function () {
            originalSetup.call(this);
            try {
                appendSwiftSection(this);
            } catch (e) {
                // Frappe's own switcher must keep working even if ours can't render.
                console.warn("Swift theme section failed to render", e);
            }
        };
    });

    function boot() {
        return (window.frappe && frappe.boot && frappe.boot.swift_theme) || {};
    }

    function appendSwiftSection(switcher) {
        var prefs = boot();
        var presets = prefs.presets || [];
        if (!presets.length) return;

        var $body = switcher.dialog.$body;
        $("<div class='swift-switch-sep'></div>").appendTo($body);

        var $section = $(
            "<div class='swift-switch'>" +
            "<div class='swift-switch-head'>" +
            "<span>" + __("Swift Theme") + "</span>" +
            "<button type='button' class='swift-switch-reset'>" + __("Use site default") + "</button>" +
            "</div>" +
            "<div class='swift-switch-grid'></div>" +
            "</div>"
        ).appendTo($body);

        var $grid = $section.find(".swift-switch-grid");
        var activePreset = document.documentElement.getAttribute("data-swift-preset") || "";
        var usingCustom = !activePreset;

        presets.forEach(function (p) {
            var $card = $(
                "<button type='button' class='swift-swatch' title='" + frappe.utils.escape_html(p.label) + "'>" +
                "<span class='swift-swatch-chip'></span>" +
                "<span class='swift-swatch-name'></span>" +
                "<span class='swift-swatch-mode'></span>" +
                "</button>"
            );
            $card.find(".swift-swatch-chip").css(
                "background", "linear-gradient(135deg, " + p.primary + ", " + p.secondary + ")");
            $card.find(".swift-swatch-name").text(p.label);
            $card.find(".swift-swatch-mode").text(p.mode === "dark" ? __("Dark") : __("Light"));
            if (p.key === activePreset) $card.addClass("selected");

            $card.on("click", function () {
                $grid.find(".swift-swatch").removeClass("selected");
                $card.addClass("selected");
                $section.find(".swift-custom").removeClass("selected");
                window.SwiftTheme.setPreset(p.key);
                frappe.show_alert({ message: __("Theme set to {0}", [p.label]), indicator: "green" });
            });

            $grid.append($card);
        });

        appendCustomPicker($section, usingCustom);

        $section.find(".swift-switch-reset").on("click", function () {
            if (!(window.SwiftTheme && window.SwiftTheme.clearPersonalTheme)) return;
            window.SwiftTheme.clearPersonalTheme();
            $section.find(".swift-swatch, .swift-custom").removeClass("selected");
            frappe.show_alert({ message: __("Using the site theme"), indicator: "blue" });
        });
    }

    // Two colour inputs; applied together so a half-set pair never lands.
    function appendCustomPicker($section, active) {
        var prefs = boot();
        var primary = prefs.primary || "#4f46e5";
        var secondary = prefs.secondary || "#7c3aed";

        var $custom = $(
            "<div class='swift-custom" + (active ? " selected" : "") + "'>" +
            "<div class='swift-custom-head'>" + __("Custom colours") + "</div>" +
            "<div class='swift-custom-row'>" +
            "<label><span>" + __("Primary") + "</span>" +
            "<input type='color' class='swift-color-primary'></label>" +
            "<label><span>" + __("Secondary") + "</span>" +
            "<input type='color' class='swift-color-secondary'></label>" +
            "<button type='button' class='btn btn-xs btn-default swift-custom-apply'>" +
            __("Apply") + "</button>" +
            "</div>" +
            "<div class='swift-custom-preview'></div>" +
            "</div>"
        ).appendTo($section);

        var $primary = $custom.find(".swift-color-primary").val(primary);
        var $secondary = $custom.find(".swift-color-secondary").val(secondary);
        var $preview = $custom.find(".swift-custom-preview");

        function paintPreview() {
            $preview.css("background",
                "linear-gradient(135deg, " + $primary.val() + ", " + $secondary.val() + ")");
        }
        paintPreview();
        $primary.on("input", paintPreview);
        $secondary.on("input", paintPreview);

        $custom.find(".swift-custom-apply").on("click", function () {
            if (!(window.SwiftTheme && window.SwiftTheme.setCustomColors)) return;
            window.SwiftTheme.setCustomColors($primary.val(), $secondary.val());
            $section.find(".swift-swatch").removeClass("selected");
            $custom.addClass("selected");
            frappe.show_alert({ message: __("Custom colours applied"), indicator: "green" });
        });
    }
})();
