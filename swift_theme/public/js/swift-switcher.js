/* Swift Theme — Navbar switcher chip + palette popover */

(function () {
    if (!window.frappe) return;

    frappe.after_ajax(function () { setTimeout(injectSwitcher, 200); });

    function injectSwitcher() {
        try {
            var boot = frappe.boot && frappe.boot.swift_theme;
            if (!boot || !boot.enable_switcher) return;
            if (document.querySelector(".swift-chip")) return;

            var navbar = document.querySelector("header .navbar-nav, .navbar .nav.navbar-nav, .navbar .navbar-collapse .navbar-nav");
            if (!navbar) return;

            var li = document.createElement("li");
            li.className = "nav-item swift-nav-item";
            li.style.cssText = "display:flex;align-items:center;margin:0 8px;";

            var chip = document.createElement("button");
            chip.type = "button";
            chip.className = "swift-chip";
            chip.title = "Swift Theme";
            chip.innerHTML = '<span class="swift-dot"></span><span>Theme</span>';
            chip.addEventListener("click", function (e) {
                e.stopPropagation();
                openPalette(chip);
            });

            li.appendChild(chip);
            navbar.insertBefore(li, navbar.firstChild);
        } catch (e) { console.warn("Swift switcher inject failed", e); }
    }

    function openPalette(anchor) {
        closePalette();
        var boot = frappe.boot.swift_theme || {};
        var accents = boot.accents || [];
        var themes  = boot.themes  || [];

        var pop = document.createElement("div");
        pop.className = "swift-palette";

        // Full themes ALWAYS on top so users see the premium options first
        pop.appendChild(section("Premium theme", themesList(themes)));

        // Accents — only show when NO full theme is active
        var currentTheme = document.documentElement.getAttribute("data-swift-theme") || "";
        if (!currentTheme) {
            pop.appendChild(section("Accent", accentsGrid(accents)));
        } else {
            var note = document.createElement("div");
            note.className = "swift-palette-note";
            note.textContent = "Accent picker is hidden — the active theme provides its own accent. Pick “None” above to choose your own.";
            pop.appendChild(section("Accent", note));
        }

        // Layout
        pop.appendChild(section("Density", segmented(["Compact","Comfortable","Cozy"], "density")));
        pop.appendChild(section("Shape",   segmented(["Sharp","Rounded","Pill"], "radius")));
        pop.appendChild(section("Size",    segmented(["S","M","L","XL"], "font-scale")));

        // Toggles
        pop.appendChild(section("Toggles", togglesList()));

        document.body.appendChild(pop);
        var r = anchor.getBoundingClientRect();
        pop.style.top = (r.bottom + 8) + "px";
        pop.style.left = Math.max(8, r.right - 320) + "px";

        setTimeout(function () {
            document.addEventListener("click", closePaletteIfOutside, true);
        }, 0);
    }

    function closePaletteIfOutside(e) {
        var pop = document.querySelector(".swift-palette");
        if (!pop) return;
        if (!pop.contains(e.target)) closePalette();
    }
    function closePalette() {
        var pop = document.querySelector(".swift-palette");
        if (pop) pop.remove();
        document.removeEventListener("click", closePaletteIfOutside, true);
    }

    function section(title, node) {
        var wrap = document.createElement("div");
        var h = document.createElement("h6");
        h.textContent = title;
        wrap.appendChild(h);
        wrap.appendChild(node);
        var div = document.createElement("div");
        div.className = "swift-divider";
        wrap.appendChild(div);
        return wrap;
    }

    function accentsGrid(accents) {
        var grid = document.createElement("div");
        grid.className = "swift-accent-grid";
        accents.forEach(function (a) {
            var sw = document.createElement("button");
            sw.className = "swift-accent-swatch";
            sw.title = a.label;
            sw.style.background = accentColor(a.key);
            if (document.documentElement.getAttribute("data-swift-accent") === a.key) sw.classList.add("active");
            sw.addEventListener("click", function () {
                window.SwiftTheme.setAccent(a.key);
                grid.querySelectorAll(".swift-accent-swatch").forEach(function (n) { n.classList.remove("active"); });
                sw.classList.add("active");
            });
            grid.appendChild(sw);
        });
        return grid;
    }

    function themesList(themes) {
        var list = document.createElement("div");
        themes.forEach(function (t) {
            var row = document.createElement("div");
            row.className = "swift-menu-item";
            row.textContent = t.label;
            if ((document.documentElement.getAttribute("data-swift-theme") || "") === t.key) {
                var tag = document.createElement("span");
                tag.className = "swift-tag";
                tag.textContent = "active";
                row.appendChild(tag);
            }
            row.addEventListener("click", function () {
                window.SwiftTheme.setFullTheme(t.key);
                closePalette();
            });
            list.appendChild(row);
        });
        return list;
    }

    function segmented(options, kind) {
        var wrap = document.createElement("div");
        wrap.style.cssText = "display:flex;gap:4px;padding:0 4px;";
        var active = document.documentElement.getAttribute("data-swift-" + kind) || "";
        options.forEach(function (opt) {
            var b = document.createElement("button");
            b.className = "swift-chip";
            b.style.flex = "1";
            b.textContent = opt;
            if (active === opt) b.style.borderColor = "var(--swift-accent)";
            b.addEventListener("click", function () {
                if (kind === "density")    window.SwiftTheme.setDensity(opt);
                if (kind === "radius")     window.SwiftTheme.setRadius(opt);
                if (kind === "font-scale") window.SwiftTheme.setFontScale(opt);
                wrap.querySelectorAll("button").forEach(function (n) { n.style.borderColor = ""; });
                b.style.borderColor = "var(--swift-accent)";
            });
            wrap.appendChild(b);
        });
        return wrap;
    }

    function togglesList() {
        var wrap = document.createElement("div");
        var sidebarOff = window.SwiftSidebar && window.SwiftSidebar.isOff && window.SwiftSidebar.isOff();
        var pins = (window.SwiftSidebar && window.SwiftSidebar.getPins && window.SwiftSidebar.getPins()) || [];
        var items = [
            { label: "Focus mode (F)",   onClick: function () { window.SwiftTheme.toggleFocus(); } },
            { label: "Reading mode (R)", onClick: function () { window.SwiftTheme.toggleReading(); } },
            { label: (sidebarOff ? "Show sidebar (Alt+B)" : "Hide sidebar totally (Alt+B)"),
              onClick: function () {
                  if (window.SwiftSidebar) window.SwiftSidebar.toggleOff();
                  closePalette();
              }
            },
            { label: "Clear pinned items (" + pins.length + ")",
              onClick: function () {
                  if (window.SwiftSidebar) window.SwiftSidebar.clearPins();
                  closePalette();
              }
            },
            { label: "Command palette (Ctrl+Shift+T)", onClick: function () { document.dispatchEvent(new CustomEvent("swift:cmdk:open")); closePalette(); } },
        ];
        items.forEach(function (i) {
            var row = document.createElement("div");
            row.className = "swift-menu-item";
            row.textContent = i.label;
            row.addEventListener("click", i.onClick);
            wrap.appendChild(row);
        });
        // Show list of currently pinned items
        if (pins.length) {
            var hint = document.createElement("div");
            hint.className = "swift-palette-note";
            hint.style.marginTop = "6px";
            hint.textContent = "Pinned: " + pins.slice(0, 5).join(", ") + (pins.length > 5 ? "…" : "");
            wrap.appendChild(hint);
        } else {
            var hint2 = document.createElement("div");
            hint2.className = "swift-palette-note";
            hint2.style.marginTop = "6px";
            hint2.textContent = "Tip: hover any sidebar item and click ★ to pin it to the top.";
            wrap.appendChild(hint2);
        }
        return wrap;
    }

    function accentColor(key) {
        var map = {
            indigo:"#4f46e5", violet:"#7c3aed", blue:"#2563eb", sky:"#0284c7",
            teal:"#0d9488", emerald:"#059669", amber:"#d97706",
            rose:"#e11d48", pink:"#db2777", slate:"#475569",
        };
        return map[key] || "#999";
    }
})();
