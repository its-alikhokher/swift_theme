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
        silenceFrappesOwnSounds();
    });

    /* Frappe plays its own audio for the same moments we do — form.js fires
       play_sound("click") on every save — so a save made two noises.

       Frappe's own audio yields per event, not wholesale. The app ships no
       sound files, so suppressing everything the moment Sounds was ticked made
       the desk fall completely silent — a switch that promises sound and
       delivers less than before it was touched.

       So: the theme wins an event only when it actually has a file for it.
       Anything it has nothing for still gets Frappe's own sound, and Sounds off
       hands the whole desk back.

       Read per call rather than once at startup, so toggling the setting or
       attaching a file takes effect without a reload. Frappe's own function is
       kept rather than overwritten, so nothing else that reaches for it breaks. */

    /* Frappe's sound names against ours. "click" is the one it plays on save,
       which is where the two engines collided. Anything unmapped is left to
       Frappe untouched. */
    var FRAPPE_SOUNDS = {
        click:  "save",
        submit: "submit",
        cancel: "cancel",
        delete: "delete",
        error:  "error",
    };
    function silenceFrappesOwnSounds() {
        var utils = frappe.utils;
        if (!utils || !utils.play_sound || utils.play_sound.__swiftWrapped) return;

        var original = utils.play_sound;
        var wrapped = function (name) {
            var cfg = config();
            var key = FRAPPE_SOUNDS[String(name || "").toLowerCase()];
            // Only stand aside where the theme genuinely has something to play.
            if (cfg && cfg.enabled && key && cfg.files && cfg.files[key]) return;
            return original.apply(this, arguments);
        };
        wrapped.__swiftWrapped = true;
        wrapped.__frappeOriginal = original;
        copyProps(original, wrapped);
        utils.play_sound = wrapped;
    }

    // Save / Submit / Cancel / Amend all funnel through frappe.ui.form.save,
    // whose signature is (frm, action, callback, btn).
    function hookFormActions() {
        var target = frappe.ui && frappe.ui.form;
        if (!target || typeof target.save !== "function" || target.save.__swiftWrapped) return;

        var original = target.save;
        var wrapped = function (frm, action, callback, btn) {
            var withSound = function (r) {
                // A fault in the sound layer must never stop a document from
                // saving, so the original callback runs no matter what.
                try {
                    play(r && r.exc ? "error" : actionToEvent(action));
                } catch (e) {
                    console.debug("Swift sound skipped:", e);
                }
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
                try { playForIndicator(message && message.indicator); } catch (e) {}
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
                try {
                    if (msg && typeof msg === "object") playForIndicator(msg.indicator);
                } catch (e) {}
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
