/* Swift Theme — Mode Observer
   Watches Frappe's [data-theme] attribute on <html> so we can react when the
   user switches Light/Dark/Auto from Frappe's built-in menu. */

(function () {
    var html = document.documentElement;

    function onFrappeThemeChange() {
        // Nothing to do CSS-wise (accents auto-adapt via [data-theme="dark"]).
        // We just fire a custom event for extensions.
        var mode = html.getAttribute("data-theme") || "light";
        document.dispatchEvent(new CustomEvent("swift:mode-changed", { detail: { mode: mode } }));
    }

    try {
        var obs = new MutationObserver(function (muts) {
            muts.forEach(function (m) {
                if (m.attributeName === "data-theme" || m.attributeName === "data-theme-mode") {
                    onFrappeThemeChange();
                }
            });
        });
        obs.observe(html, { attributes: true, attributeFilter: ["data-theme", "data-theme-mode"] });
    } catch (e) {}
})();
