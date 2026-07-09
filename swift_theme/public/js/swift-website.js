/* Swift Theme — Public website & login page bootstrap */

(function () {
    // Apply theme to <html> ASAP; login/portal pages don't have Frappe boot
    var html = document.documentElement;
    if (!html.getAttribute("data-swift-scheme")) {
        var cached = null;
        try { cached = localStorage.getItem("swift_theme_scheme"); } catch (e) {}
        html.setAttribute("data-swift-scheme", cached || "swift-light");
    }

    // Splash for slow first paints
    document.addEventListener("DOMContentLoaded", function () {
        var splash = document.querySelector(".swift-splash");
        if (splash) setTimeout(function () { splash.classList.add("hide"); }, 200);
    });
})();
