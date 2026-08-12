/* Swift Theme — Navbar switcher chip + palette popover */

(function () {
    if (!window.frappe) return;

    frappe.after_ajax(function () { setTimeout(syncSwitcher, 200); });

    // Re-evaluated whenever settings are saved, so toggling "Enable Theme
    // Switcher" shows or hides the chip without a reload.
    document.addEventListener("swift:prefs:applied", syncSwitcher);

    function syncSwitcher() {
        var boot = frappe.boot && frappe.boot.swift_theme;
        var existing = document.querySelector(".swift-nav-item");

        if (!boot || !boot.enable_switcher) {
            if (existing) existing.remove();
            closePalette();
            return;
        }
        injectSwitcher();
    }

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
        var presets = boot.presets || [];

        var pop = document.createElement("div");
        pop.className = "swift-palette";

        if (boot.color_mode === "Custom Colors") {
            // The site is on a fixed brand pair; offering presets here would
            // silently contradict Swift Theme Settings.
            var note = document.createElement("div");
            note.className = "swift-palette-note";
            note.textContent = "This site uses custom brand colours. Switch Color Mode to “Theme Preset” in Swift Theme Settings to choose a theme.";
            pop.appendChild(section("Theme", note));
        } else {
            pop.appendChild(section("Theme", presetList(presets)));
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

    // Each row previews the preset's own primary/secondary pair, so the choice
    // is visible before it's applied.
    function presetList(presets) {
        var list = document.createElement("div");
        list.className = "swift-preset-list";

        presets.forEach(function (p) {
            var row = document.createElement("div");
            row.className = "swift-menu-item swift-preset-item";

            var chip = document.createElement("span");
            chip.className = "swift-preset-swatch";
            chip.style.background = "linear-gradient(135deg, " + p.primary + ", " + p.secondary + ")";
            row.appendChild(chip);

            var label = document.createElement("span");
            label.className = "swift-preset-label";
            label.textContent = p.label;
            row.appendChild(label);

            var mode = document.createElement("span");
            mode.className = "swift-preset-mode";
            mode.textContent = p.mode === "dark" ? "Dark" : "Light";
            row.appendChild(mode);

            if ((document.documentElement.getAttribute("data-swift-preset") || "") === p.key) {
                row.classList.add("active");
                var tag = document.createElement("span");
                tag.className = "swift-tag";
                tag.textContent = "active";
                row.appendChild(tag);
            }

            row.addEventListener("click", function () {
                window.SwiftTheme.setPreset(p.key);
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

})();
