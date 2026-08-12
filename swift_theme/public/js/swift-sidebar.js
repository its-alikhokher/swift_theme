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
        // Cached because once the ★ button is injected, el.textContent would
        // include it and the label would no longer match the stored pin.
        if (el._swiftLabel !== undefined) return el._swiftLabel;

        var lbl = el.querySelector(".sidebar-item-label, .list-link-label, .tag-label");
        var text;
        if (lbl) {
            text = lbl.textContent;
        } else {
            text = "";
            Array.prototype.forEach.call(el.childNodes, function (n) {
                if (n.nodeType === 1 && n.classList && n.classList.contains("swift-pin-btn")) return;
                text += n.textContent || "";
            });
        }
        el._swiftLabel = (text || "").trim();
        return el._swiftLabel;
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
        // Our own DOM edits below would otherwise be seen by the observer and
        // schedule another pass, looping forever every 120ms.
        withObserverPaused(function () {
            var pins = getPins();
            getSidebarItems().forEach(function (el) {
                decorateItem(el);
                var lbl = itemLabel(el);
                if (pins.indexOf(lbl) > -1) el.classList.add("swift-pinned");
                else                        el.classList.remove("swift-pinned");
            });
            reorderPinnedInParents();
        });
    }

    // Move pinned items to the top of their parent container, add a divider
    function reorderPinnedInParents() {
        var parents = new Set();
        document.querySelectorAll(".swift-pinned").forEach(function (n) {
            if (n.parentElement) parents.add(n.parentElement);
        });
        parents.forEach(function (p) {
            var pinned = Array.prototype.slice.call(p.querySelectorAll(":scope > .swift-pinned"));
            // Reverse so first-pinned ends up on top after successive prepends.
            // Skip elements already in place — moving a node to where it
            // already is still counts as a DOM mutation.
            pinned.slice().reverse().forEach(function (el) {
                if (p.firstChild !== el) p.insertBefore(el, p.firstChild);
            });
            // Add a group class to the last pinned so we get a divider under it
            p.querySelectorAll(":scope > .swift-pinned-group").forEach(function (n) {
                n.classList.remove("swift-pinned-group");
            });
            if (pinned.length) {
                // Divider belongs under the *last* pinned row, closing the
                // group — putting it on pinned[0] drew it after the first one.
                pinned[pinned.length - 1].classList.add("swift-pinned-group");
            }
        });
    }

    // ---------------- Observe sidebar mutations (v16 re-renders often) ----------------
    var observer = null;
    var observeTarget = null;
    var paused = 0;

    function observeNow() {
        if (observer && observeTarget) {
            observer.observe(observeTarget, { childList: true, subtree: true });
        }
    }

    // Suspends observation while we mutate the sidebar ourselves.
    function withObserverPaused(fn) {
        paused++;
        if (observer) observer.disconnect();
        try {
            fn();
        } finally {
            paused--;
            if (paused <= 0) {
                paused = 0;
                // Drain records caused by our own edits before re-arming.
                if (observer) observer.takeRecords();
                observeNow();
            }
        }
    }

    function startObserver() {
        if (observer) return;
        // Scoping to the sidebar matters — falling back to <body> meant
        // observing the whole desk and re-running on every unrelated render.
        observeTarget = document.querySelector(".body-sidebar-container, .layout-side-section, .body-sidebar");
        if (!observeTarget) return;
        observer = new MutationObserver(function () {
            if (paused) return;
            // Debounce to avoid thrash on heavy re-renders
            clearTimeout(observer._t);
            observer._t = setTimeout(applyPinnedState, 120);
        });
        observeNow();
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
                // Without this the floating restore button stayed on screen
                // permanently once the sidebar had been hidden even once.
                removeRestoreButton();
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
    // The sidebar mounts after the desk boots, so keep trying to attach the
    // observer — it now scopes to the sidebar and no longer falls back to body.
    document.addEventListener("app_ready", function () { setTimeout(boot, 200); });
    if (window.frappe && frappe.after_ajax) {
        frappe.after_ajax(function () { setTimeout(boot, 200); });
    }

    // ---------------- Keyboard shortcut: Alt+B toggles sidebar off ----------------
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
