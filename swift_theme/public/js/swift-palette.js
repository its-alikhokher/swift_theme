/* Swift Theme — Command Palette (Ctrl+Shift+T) */

(function () {
    document.addEventListener("keydown", function (e) {
        if (e.ctrlKey && e.shiftKey && (e.key === "T" || e.key === "t")) {
            e.preventDefault();
            openCmdk();
        }
    });
    document.addEventListener("swift:cmdk:open", openCmdk);

    function openCmdk() {
        if (document.querySelector(".swift-cmdk-backdrop")) return;

        var boot = (window.frappe && frappe.boot && frappe.boot.swift_theme) || {};
        var commands = buildCommands(boot);

        var backdrop = document.createElement("div");
        backdrop.className = "swift-cmdk-backdrop";

        var box = document.createElement("div");
        box.className = "swift-cmdk";
        box.innerHTML =
            '<input type="text" placeholder="Type a command… (accent, theme, density, focus…)" autofocus />' +
            '<div class="swift-cmdk-list"></div>';

        backdrop.appendChild(box);
        document.body.appendChild(backdrop);

        var input = box.querySelector("input");
        var list = box.querySelector(".swift-cmdk-list");
        var active = 0;

        function render(filter) {
            list.innerHTML = "";
            var q = (filter || "").toLowerCase().trim();
            var filtered = q ? commands.filter(function (c) { return c.label.toLowerCase().indexOf(q) !== -1; }) : commands;
            filtered.slice(0, 30).forEach(function (c, i) {
                var row = document.createElement("div");
                row.className = "swift-cmdk-item" + (i === active ? " active" : "");
                row.innerHTML = '<span>' + c.label + '</span>' + (c.kbd ? '<span class="kbd">' + c.kbd + '</span>' : '');
                row.addEventListener("mouseenter", function () { active = i; render(input.value); });
                row.addEventListener("click", function () { c.run(); close(); });
                list.appendChild(row);
            });
        }

        function close() {
            backdrop.remove();
            document.removeEventListener("keydown", nav, true);
        }

        function nav(e) {
            if (!document.body.contains(backdrop)) return;
            var items = list.children;
            if (e.key === "Escape") { e.preventDefault(); close(); }
            else if (e.key === "ArrowDown") { e.preventDefault(); active = Math.min(items.length - 1, active + 1); render(input.value); }
            else if (e.key === "ArrowUp")   { e.preventDefault(); active = Math.max(0, active - 1); render(input.value); }
            else if (e.key === "Enter")     { e.preventDefault(); if (items[active]) items[active].click(); }
        }

        input.addEventListener("input", function () { active = 0; render(input.value); });
        document.addEventListener("keydown", nav, true);
        backdrop.addEventListener("click", function (e) { if (e.target === backdrop) close(); });

        render("");
    }

    function buildCommands(boot) {
        var cmds = [];
        (boot.accents || []).forEach(function (a) {
            cmds.push({ label: "Accent → " + a.label, run: function () { window.SwiftTheme.setAccent(a.key); } });
        });
        (boot.themes || []).forEach(function (t) {
            cmds.push({ label: "Full theme → " + t.label, run: function () { window.SwiftTheme.setFullTheme(t.key); } });
        });
        ["Compact","Comfortable","Cozy"].forEach(function (d) {
            cmds.push({ label: "Density → " + d, run: function () { window.SwiftTheme.setDensity(d); } });
        });
        ["Sharp","Rounded","Pill"].forEach(function (r) {
            cmds.push({ label: "Shape → " + r, run: function () { window.SwiftTheme.setRadius(r); } });
        });
        ["S","M","L","XL"].forEach(function (s) {
            cmds.push({ label: "Font size → " + s, run: function () { window.SwiftTheme.setFontScale(s); } });
        });
        ["Inter","Poppins","Manrope","Roboto","System"].forEach(function (f) {
            cmds.push({ label: "Font family → " + f, run: function () { window.SwiftTheme.setFontFamily(f); } });
        });
        cmds.push({ label: "Toggle Focus mode",   kbd: "F", run: function () { window.SwiftTheme.toggleFocus(); } });
        cmds.push({ label: "Toggle Reading mode", kbd: "R", run: function () { window.SwiftTheme.toggleReading(); } });
        cmds.push({ label: "Open Swift Theme Settings", run: function () { frappe.set_route("Form", "Swift Theme Settings", "Swift Theme Settings"); } });
        return cmds;
    }
})();
