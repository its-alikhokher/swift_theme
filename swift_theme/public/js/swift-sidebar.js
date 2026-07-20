/* Swift Theme — Sidebar features
   1. Totally hide sidebar (off mode) + floating restore button
   2. Pin/unpin sidebar items (localStorage-backed, per user, per site)
   3. Public API: window.SwiftSidebar
*/

(function () {
    if (!window) return;

    var KEY_OFF = "swift_sidebar_off";
    var KEY_PIN = "swift_sidebar_pins";     // JSON array of item labels
    var html = document.documentElement;

    // ---------------- Storage helpers ----------------
    function getOff() { try { return localStorage.getItem(KEY_OFF) === "on"; } catch (e) { return false; } }
    function setOff(v) {
        try {
            if (v) localStorage.setItem(KEY_OFF, "on");
            else   localStorage.removeItem(KEY_OFF);
        } catch (e) {}
    }
    function getPins() {
        try {
            var raw = localStorage.getItem(KEY_PIN);
            return raw ? JSON.parse(raw) : [];
        } catch (e) { return []; }
    }
    function savePins(list) {
        try { localStorage.setItem(KEY_PIN, JSON.stringify(list || [])); } catch (e) {}
    }
    function isPinned(label) { return getPins().indexOf((label || "").trim()) > -1; }
    function togglePin(label) {
        label = (label || "").trim();
        if (!label) return false;
        var list = getPins();
        var i = list.indexOf(label);
        if (i > -1) { list.splice(i, 1); }
        else        { list.push(label); }
        savePins(list);
        return list.indexOf(label) > -1;
    }

    // ---------------- Apply off mode from storage on load ----------------
    if (getOff()) html.setAttribute("data-swift-sidebar", "off");

    // ---------------- Restore button (only in off mode) ----------------
    function ensureRestoreButton() {
        if (document.querySelector(".swift-sidebar-restore")) return;
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "swift-sidebar-restore";
        btn.title = "Show sidebar";
        btn.setAttribute("aria-label", "Show sidebar");
        btn.innerHTML = "▸";
        btn.addEventListener("click", function () {
            window.SwiftSidebar.setOff(false);
        });
        document.body.appendChild(btn);
    }

    // ---------------- Sidebar item selector — v16 verified ----------------
    var SIDEBAR_ITEM_SELECTORS = [
        ".body-sidebar .standard-sidebar-item",
        ".body-sidebar .sidebar-items .nav-item",
        ".layout-side-section .list-sidebar .list-link",
        ".layout-side-section .list-sidebar .list-tags .tag-pill",
    ];
    function getSidebarItems() {
        var nodes = [];
        SIDEBAR_ITEM_SELECTORS.forEach(function (sel) {
            document.querySelectorAll(sel).forEach(function (n) { nodes.push(n); });
        });
        return nodes;
    }
    function itemLabel(el) {
        var lbl = el.querySelector(".sidebar-item-label, .list-link-label, .tag-label");
        var text = lbl ? lbl.textContent : el.textContent;
        return (text || "").trim();
    }

    // ---------------- Inject pin buttons + apply pinned state ----------------
    function decorateItem(el) {
        if (el._swiftDecorated) return;
        el._swiftDecorated = true;

        var label = itemLabel(el);
        if (!label) return;

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "swift-pin-btn";
        btn.title = "Pin to top";
        btn.setAttribute("data-swift-pin", label);
        btn.textContent = "★";
        btn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            var nowPinned = togglePin(label);
            applyPinnedState();
            if (window.frappe && frappe.show_alert) {
                frappe.show_alert({
                    message: (nowPinned ? "Pinned: " : "Unpinned: ") + label,
                    indicator: "green",
                });
            }
        });
        el.appendChild(btn);
    }

    function applyPinnedState() {
        var pins = getPins();
        getSidebarItems().forEach(function (el) {
            decorateItem(el);
            var lbl = itemLabel(el);
            if (pins.indexOf(lbl) > -1) el.classList.add("swift-pinned");
            else                        el.classList.remove("swift-pinned");
        });
        reorderPinnedInParents();
    }

    // Move pinned items to the top of their parent container, add a divider
    function reorderPinnedInParents() {
        var parents = new Set();
        document.querySelectorAll(".swift-pinned").forEach(function (n) {
            if (n.parentElement) parents.add(n.parentElement);
        });
        parents.forEach(function (p) {
            var pinned = Array.prototype.slice.call(p.querySelectorAll(":scope > .swift-pinned"));
            // Reverse so first-pinned ends up on top after successive prepends
            pinned.reverse().forEach(function (el) { p.insertBefore(el, p.firstChild); });
            // Add a group class to the last pinned so we get a divider under it
            p.querySelectorAll(":scope > .swift-pinned-group").forEach(function (n) {
                n.classList.remove("swift-pinned-group");
            });
            if (pinned.length) {
                pinned[0].classList.add("swift-pinned-group");
            }
        });
    }

    // ---------------- Observe sidebar mutations (v16 re-renders often) ----------------
    var observer = null;
    function startObserver() {
        if (observer) return;
        var target = document.querySelector(".body-sidebar-container, .layout-side-section, body");
        if (!target) return;
        observer = new MutationObserver(function () {
            // Debounce to avoid thrash on heavy re-renders
            clearTimeout(observer._t);
            observer._t = setTimeout(applyPinnedState, 120);
        });
        observer.observe(target, { childList: true, subtree: true });
    }

    // ---------------- Public API ----------------
    window.SwiftSidebar = {
        setOff: function (v) {
            setOff(!!v);
            if (v) {
                html.setAttribute("data-swift-sidebar", "off");
                ensureRestoreButton();
            } else {
                html.removeAttribute("data-swift-sidebar");
            }
        },
        toggleOff: function () { this.setOff(!getOff()); },
        isOff: getOff,
        pin: function (label) {
            if (!label) return;
            var pins = getPins();
            if (pins.indexOf(label) === -1) { pins.push(label); savePins(pins); }
            applyPinnedState();
        },
        unpin: function (label) {
            var pins = getPins().filter(function (x) { return x !== label; });
            savePins(pins);
            applyPinnedState();
        },
        togglePin: function (label) { togglePin(label); applyPinnedState(); },
        clearPins: function () { savePins([]); applyPinnedState(); },
        getPins: getPins,
        refresh: applyPinnedState,
    };

    // ---------------- Boot ----------------
    function boot() {
        if (getOff()) ensureRestoreButton();
        applyPinnedState();
        startObserver();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
    // Also re-decorate after Frappe finishes booting the desk
    document.addEventListener("app_ready", function () { setTimeout(applyPinnedState, 200); });
    if (window.frappe && frappe.after_ajax) {
        frappe.after_ajax(function () { setTimeout(applyPinnedState, 200); });
    }

    // ---------------- Keyboard shortcut: Alt+B toggles sidebar off ----------------
    document.addEventListener("keydown", function (e) {
        if (e.altKey && !e.ctrlKey && !e.metaKey && (e.key === "b" || e.key === "B")) {
            e.preventDefault();
            window.SwiftSidebar.toggleOff();
        }
    });
})();
