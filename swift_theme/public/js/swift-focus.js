/* Swift Theme — Focus / Reading shortcuts
   F  = toggle focus mode (hide chrome)
   R  = toggle reading mode (widen content)
   Both are disabled while typing in inputs. */

(function () {
    document.addEventListener("keydown", function (e) {
        if (isTyping(e.target)) return;

        var boot = window.frappe && frappe.boot && frappe.boot.swift_theme;
        if (boot && !boot.enable_focus_mode) return;

        if (e.key === "f" || e.key === "F") { window.SwiftTheme.toggleFocus(); }
        else if (e.key === "r" || e.key === "R") { window.SwiftTheme.toggleReading(); }
    });

    function isTyping(el) {
        if (!el) return false;
        var tag = (el.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || tag === "select") return true;
        if (el.isContentEditable) return true;
        return false;
    }
})();
