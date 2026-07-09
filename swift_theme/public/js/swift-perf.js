/* Swift Theme — Desk Performance helpers
   - Debounces heavy resize/scroll listeners set up by Frappe if user opts in.
   - Preloads fonts + primary icons when idle.
   - Lazy-loads images below the fold. */

(function () {
    document.addEventListener("DOMContentLoaded", init);

    function init() {
        if (document.documentElement.getAttribute("data-swift-perf") !== "on") return;

        whenIdle(preloadFonts);
        whenIdle(lazyImages);
        whenIdle(hintPaint);
    }

    function whenIdle(fn) {
        if ("requestIdleCallback" in window) requestIdleCallback(fn, { timeout: 1500 });
        else setTimeout(fn, 200);
    }

    function preloadFonts() {
        try {
            var urls = [
                "/assets/swift_theme/fonts/inter-var.woff2",
            ];
            urls.forEach(function (href) {
                var l = document.createElement("link");
                l.rel = "preload";
                l.as = "font";
                l.type = "font/woff2";
                l.crossOrigin = "anonymous";
                l.href = href;
                document.head.appendChild(l);
            });
        } catch (e) {}
    }

    function lazyImages() {
        try {
            document.querySelectorAll("img:not([loading])").forEach(function (img) {
                img.setAttribute("loading", "lazy");
                img.setAttribute("decoding", "async");
            });
        } catch (e) {}
    }

    function hintPaint() {
        // Hint the browser to promote scrollable regions to their own layer.
        try {
            document.querySelectorAll(".layout-main-section, .list-row-container").forEach(function (el) {
                el.style.willChange = "transform";
            });
        } catch (e) {}
    }
})();
