/* Swift Theme — Sound Engine

   Plays the sounds configured in Swift Theme Settings on desk events.
   Config arrives via bootinfo (swift_theme.sounds), so playback needs no
   server round trip. Events with no attached file stay silent. */

(function () {
    if (!window.frappe) return;

    var cache = {};        // url -> HTMLAudioElement, so each file decodes once
    var lastPlayed = 0;    // guards against bursts of near-identical events
    var MIN_GAP_MS = 120;

    function config() {
        var boot = frappe.boot && frappe.boot.swift_theme;
        return (boot && boot.sounds) || null;
    }

    function play(eventKey) {
        var cfg = config();
        if (!cfg || !cfg.enabled) return;

        var url = cfg.files && cfg.files[eventKey];
        if (!url) return;

        var now = Date.now();
        if (now - lastPlayed < MIN_GAP_MS) return;
        lastPlayed = now;

        try {
            var audio = cache[url] || (cache[url] = new Audio(url));
            audio.volume = cfg.volume;
            audio.currentTime = 0;
            var played = audio.play();
            // Browsers block autoplay until the user interacts with the page;
            // that rejection is expected and must stay silent.
            if (played && played.catch) played.catch(function () {});
        } catch (e) { /* a sound must never break the action that triggered it */ }
    }

    // Public hook so other Swift modules can trigger sounds.
    window.SwiftSounds = { play: play };

    frappe.after_ajax(function () {
        hookFormActions();
        hookFeedback();
        hookNotifications();
    });

    // Save / Submit / Cancel / Amend all funnel through frappe.ui.form.save,
    // whose signature is (frm, action, callback, btn).
    function hookFormActions() {
        var target = frappe.ui && frappe.ui.form;
        if (!target || typeof target.save !== "function" || target.save.__swiftWrapped) return;

        var original = target.save;
        var wrapped = function (frm, action, callback, btn) {
            var withSound = function (r) {
                if (!(r && r.exc)) play(actionToEvent(action));
                else play("error");
                if (callback) return callback.apply(this, arguments);
            };
            return original.call(this, frm, action, withSound, btn);
        };
        wrapped.__swiftWrapped = true;
        target.save = wrapped;
    }

    function actionToEvent(action) {
        switch (String(action || "").toLowerCase()) {
            case "submit": return "submit";
            case "cancel": return "cancel";
            default:       return "save";   // Save, Update, Amend
        }
    }

    // Toasts and message dialogs carry an indicator colour we can map to a sound.
    function hookFeedback() {
        if (typeof frappe.show_alert === "function" && !frappe.show_alert.__swiftWrapped) {
            var originalAlert = frappe.show_alert;
            var wrappedAlert = function (message) {
                playForIndicator(message && message.indicator);
                return originalAlert.apply(this, arguments);
            };
            copyProps(originalAlert, wrappedAlert);
            wrappedAlert.__swiftWrapped = true;
            frappe.show_alert = wrappedAlert;
            // frappe.toast is the same function under another name.
            frappe.toast = wrappedAlert;
        }

        if (typeof frappe.msgprint === "function" && !frappe.msgprint.__swiftWrapped) {
            var originalMsgprint = frappe.msgprint;
            var wrappedMsgprint = function (msg) {
                if (msg && typeof msg === "object") playForIndicator(msg.indicator);
                return originalMsgprint.apply(this, arguments);
            };
            copyProps(originalMsgprint, wrappedMsgprint);
            wrappedMsgprint.__swiftWrapped = true;
            frappe.msgprint = wrappedMsgprint;
        }
    }

    function playForIndicator(indicator) {
        if (indicator === "red") play("error");
        else if (indicator === "green") play("success");
    }

    function hookNotifications() {
        if (!frappe.realtime || typeof frappe.realtime.on !== "function") return;
        try {
            frappe.realtime.on("notification", function () { play("notification"); });
        } catch (e) {}
    }

    // Preserve helper properties hung off the original function.
    function copyProps(from, to) {
        Object.keys(from).forEach(function (key) { to[key] = from[key]; });
    }
})();
