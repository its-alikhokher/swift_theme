/* Swift Theme — Public website + login bootstrap */

(function () {
    var html = document.documentElement;

    // Apply accent from localStorage
    try {
        var accent = localStorage.getItem("swift_accent") || "indigo";
        if (!html.getAttribute("data-swift-accent")) html.setAttribute("data-swift-accent", accent);
        var theme = localStorage.getItem("swift_theme_full") || "";
        if (theme && !html.getAttribute("data-swift-theme")) html.setAttribute("data-swift-theme", theme);
    } catch (e) {}

    // Detect login page and set layout + brand
    document.addEventListener("DOMContentLoaded", function () {
        var isLogin = !!document.querySelector("body.for-login, body[data-path='login'], .for-login, .for-signup, .for-forgot");
        if (!isLogin) return;

        fetch("/api/method/swift_theme.api.boot.get_effective_prefs", { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                var p = (j && j.message) || {};
                document.body.setAttribute("data-swift-login", p.login_layout || "Split");

                if (p.login_bg_image) {
                    document.body.style.setProperty("--swift-login-bg", "url('" + p.login_bg_image + "')");
                }

                if (p.brand_name || p.brand_logo) injectBrand(p);
                if (p.login_tagline) injectTagline(p.login_tagline);
                if (!p.login_show_signup) hideSignupLinks();
            }).catch(function () { /* not logged into system with settings; ignore */ });

        // Splash
        var splash = document.querySelector(".swift-splash");
        if (splash) setTimeout(function () { splash.classList.add("hide"); }, 300);
    });

    function injectBrand(p) {
        var head = document.querySelector(".page-card-head, .login-content .page-header");
        if (!head) return;
        var brand = document.createElement("div");
        brand.className = "swift-login-brand";
        var isDark = document.documentElement.getAttribute("data-theme") === "dark";
        var logo = (isDark && p.brand_logo_dark) || p.brand_logo;
        var html = "";
        if (logo) html += '<img src="' + logo + '" alt="logo" />';
        if (p.brand_name) html += '<div class="name">' + escapeHtml(p.brand_name) + '</div>';
        brand.innerHTML = html;
        head.parentElement.insertBefore(brand, head);
    }
    function injectTagline(text) {
        var head = document.querySelector(".page-card-head h4, .login-content h4");
        if (!head) return;
        var t = document.createElement("div");
        t.className = "swift-login-tagline";
        t.textContent = text;
        head.after(t);
    }
    function hideSignupLinks() {
        document.querySelectorAll(".signup-link, .toggle-signup, a[href*='signup']").forEach(function (a) { a.style.display = "none"; });
    }
    function escapeHtml(s) { return String(s).replace(/[&<>"']/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]; }); }
})();
