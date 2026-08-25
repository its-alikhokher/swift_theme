/* Swift Theme — Public website + login bootstrap */

(function () {
    var html = document.documentElement;

    // swift-boot.js already restores the colour scheme from localStorage on
    // every page including this one, so there is nothing to re-apply here.

    // Detect login page and set layout + brand
    document.addEventListener("DOMContentLoaded", function () {
        // Every page in the sign-in journey, not only the first one. The reset
        // and set-password pages were missing from this list, so they never got
        // the attribute the whole stylesheet is gated on and stayed on Frappe's
        // default look — which is exactly where a password reset lands you.
        var isLogin = !!document.querySelector([
            "body.for-login",
            "body[data-path='login']",
            ".for-login",
            ".for-signup",
            ".for-forgot",
            ".for-reset-password",
            
            ".for-email-login",
        ].join(", "));
        if (!isLogin) return;

        fetch("/api/method/swift_theme.api.boot.get_effective_prefs", { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                var p = (j && j.message) || {};
                // Our own login page has this from the server, in body_class.
                // The other pages in the journey — forgot, reset, set password
                // — are Frappe's own templates, so they get it here.
                var layout = p.login_layout || "Split";
                document.body.classList.add("swift-login", "swift-login-" + layout);

                if (p.login_bg_image) {
                    document.body.style.setProperty("--swift-login-bg", "url('" + p.login_bg_image + "')");
                }

                // The brand mark and the tagline are rendered by the page
                // itself now, from Settings, before first paint. Adding them
                // again here printed each of them twice.
                labelSocialLogins();
            }).catch(function () { /* not logged into system with settings; ignore */ });

        // Splash
        var splash = document.querySelector(".swift-splash");
        if (splash) setTimeout(function () { splash.classList.add("hide"); }, 300);
    });

    /* Frappe stacks the social providers as full-width buttons with no caption
       above them. The centred design shows them as marks under a caption, and
       the caption is real text rather than a CSS ::before so it translates
       like everything else on the page. */
    function labelSocialLogins() {
        var block = document.querySelector(".social-logins");
        if (!block || block.querySelector(".swift-login-divider")) return;
        var label = document.createElement("span");
        label.className = "swift-login-divider";
        label.textContent = (window.__ && window.__("or login with")) || "or login with";
        block.insertBefore(label, block.firstChild);
    }

})();
