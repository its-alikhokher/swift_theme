/* Swift Theme — Sidebar

   Hides the sidebar entirely and offers a floating button to bring it back.
   Alt+B toggles it. The choice is per browser, in localStorage.

   Pinning sidebar items used to live here too: a star on every item, a stored
   list of labels, and a MutationObserver to put the pinned ones back on top
   after each of Frappe's re-renders. It was removed — the stars sat on Frappe's
   own sidebar rows, and reordering another app's nav on every mutation is a
   fight with the desk rather than a theme. Everything that existed only to
   serve it went with it, the observer included. */

(function () {
    if (!window) return;

    var KEY_OFF = "swift_sidebar_off";
    var html = document.documentElement;

    function getOff() {
        try { return localStorage.getItem(KEY_OFF) === "on"; } catch (e) { return false; }
    }

    function setOff(v) {
        try {
            if (v) localStorage.setItem(KEY_OFF, "on");
            else   localStorage.removeItem(KEY_OFF);
        } catch (e) {}
    }

    // Applied before paint, so a hidden sidebar never flashes into view.
    if (getOff()) html.setAttribute("data-swift-sidebar", "off");

    function ensureRestoreButton() {
        if (document.querySelector(".swift-sidebar-restore")) return;
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "swift-sidebar-restore";
        btn.title = "Show sidebar (Alt+B)";
        btn.setAttribute("aria-label", "Show sidebar");
        btn.innerHTML = "▸";
        btn.addEventListener("click", function () {
            window.SwiftSidebar.setOff(false);
        });
        document.body.appendChild(btn);
    }

    function removeRestoreButton() {
        var btn = document.querySelector(".swift-sidebar-restore");
        if (btn) btn.remove();
    }

    window.SwiftSidebar = {
        setOff: function (v) {
            setOff(!!v);
            if (v) {
                html.setAttribute("data-swift-sidebar", "off");
                ensureRestoreButton();
            } else {
                html.removeAttribute("data-swift-sidebar");
                // Without this the floating restore button stayed on screen
                // permanently once the sidebar had been hidden even once.
                removeRestoreButton();
            }
        },
        toggleOff: function () { this.setOff(!getOff()); },
        isOff: getOff,
    };

    function boot() {
        if (getOff()) ensureRestoreButton();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
    document.addEventListener("app_ready", boot);
    if (window.frappe && frappe.after_ajax) frappe.after_ajax(boot);

    document.addEventListener("keydown", function (e) {
        if (e.altKey && !e.ctrlKey && !e.metaKey && (e.key === "b" || e.key === "B")) {
            if (isTyping(e.target)) return;
            e.preventDefault();
            window.SwiftSidebar.toggleOff();
        }
    });

    function isTyping(el) {
        if (!el) return false;
        var tag = (el.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || tag === "select") return true;
        return !!el.isContentEditable;
    }
})();
