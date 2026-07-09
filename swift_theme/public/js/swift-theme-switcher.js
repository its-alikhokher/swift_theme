/* Swift Theme — Desk Navbar Switcher
   Injects a "chip" into the Frappe navbar that opens a palette of schemes.
   Persists the choice to the current user via /api/method. */

(function () {
    if (!window.frappe) return;

    frappe.after_ajax(function () {
        setTimeout(injectSwitcher, 200);
    });

    function injectSwitcher() {
        try {
            var boot = frappe.boot && frappe.boot.swift_theme;
            if (!boot || !boot.enable_switcher) return;
            if (document.querySelector(".swift-theme-switcher")) return;

            var navbar = document.querySelector(".navbar .navbar-collapse .navbar-nav, .navbar .nav.navbar-nav, header .navbar-nav");
            if (!navbar) return;

            var chip = document.createElement("button");
            chip.type = "button";
            chip.className = "swift-theme-switcher";
            chip.title = "Change theme";
            chip.innerHTML = '<span class="swift-dot"></span><span class="swift-label">Theme</span>';
            chip.addEventListener("click", openPalette);

            var wrapper = document.createElement("li");
            wrapper.className = "nav-item swift-theme-nav-item";
            wrapper.style.display = "flex";
            wrapper.style.alignItems = "center";
            wrapper.style.margin = "0 8px";
            wrapper.appendChild(chip);

            navbar.insertBefore(wrapper, navbar.firstChild);
        } catch (e) { console.warn("SwiftTheme switcher inject failed", e); }
    }

    function openPalette(evt) {
        evt.stopPropagation();
        closePalette();

        var schemes = (window.SwiftTheme && window.SwiftTheme._schemes) || [];
        var current = document.documentElement.getAttribute("data-swift-scheme");

        var pop = document.createElement("div");
        pop.className = "swift-palette";
        pop.setAttribute("role", "menu");

        schemes.forEach(function (s) {
            var row = document.createElement("div");
            row.className = "swift-palette-item" + (s.key === current ? " active" : "");
            row.setAttribute("role", "menuitem");

            var sw = document.createElement("span");
            sw.className = "swatch";
            sw.style.background = swatchGradient(s.key);
            row.appendChild(sw);

            var label = document.createElement("span");
            label.textContent = s.label + (s.dark ? " · dark" : "");
            row.appendChild(label);

            row.addEventListener("click", function () {
                window.SwiftTheme.apply(s.key);
                persistScheme(s.key);
                closePalette();
            });

            pop.appendChild(row);
        });

        // Extras
        pop.appendChild(divider());
        pop.appendChild(actionItem("Toggle sidebar", function () {
            window.SwiftTheme.toggleSidebar();
        }));
        pop.appendChild(actionItem("Toggle reduced motion", function () {
            var cur = document.documentElement.getAttribute("data-swift-anim") === "off";
            window.SwiftTheme.setAnim(cur); // if currently off, turn on
        }));

        document.body.appendChild(pop);
        positionNear(pop, evt.currentTarget);
        setTimeout(function () {
            document.addEventListener("click", closePalette, { once: true });
        }, 0);
    }

    function closePalette() {
        var existing = document.querySelector(".swift-palette");
        if (existing) existing.remove();
    }

    function positionNear(pop, anchor) {
        var rect = anchor.getBoundingClientRect();
        pop.style.top = (rect.bottom + 8) + "px";
        pop.style.left = Math.max(8, rect.right - 260) + "px";
    }

    function divider() {
        var d = document.createElement("div");
        d.style.height = "1px";
        d.style.margin = "6px 4px";
        d.style.background = "var(--swift-border)";
        return d;
    }

    function actionItem(label, onClick) {
        var row = document.createElement("div");
        row.className = "swift-palette-item";
        row.textContent = label;
        row.addEventListener("click", onClick);
        return row;
    }

    function swatchGradient(key) {
        var map = {
            "swift-light": "linear-gradient(135deg,#ffffff,#4f46e5)",
            "swift-dark":  "linear-gradient(135deg,#171a21,#7c7cff)",
            "ocean-blue":  "linear-gradient(135deg,#eef4fb,#0369a1)",
            "nord":        "linear-gradient(135deg,#2e3440,#88c0d0)",
            "dracula":     "linear-gradient(135deg,#282a36,#bd93f9)",
            "solarized":   "linear-gradient(135deg,#fdf6e3,#268bd2)",
            "forest":      "linear-gradient(135deg,#f2f6f1,#2f7d3a)",
        };
        return map[key] || "linear-gradient(135deg,#eee,#333)";
    }

    function persistScheme(scheme) {
        if (!frappe.session || frappe.session.user === "Guest") return;
        frappe.call({
            method: "swift_theme.api.boot.set_user_scheme",
            args: { scheme: scheme },
            freeze: false,
        }).catch(function (e) { console.warn("Failed to persist scheme", e); });
    }
})();
