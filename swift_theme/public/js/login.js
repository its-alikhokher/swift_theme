/* Swift Theme Enterprise Login
   The page is themed server-side (see www/login.py) so it paints correctly on
   first load; this file handles authentication and the submit sound. */

(function () {
    var body = document.body;
    var CSRF_TOKEN = body.getAttribute("data-csrf-token") || "";
    var REDIRECT_TO = body.getAttribute("data-redirect-to") || "";
    var SOUNDS_ENABLED = body.getAttribute("data-sounds-enabled") === "1";

    document.addEventListener("DOMContentLoaded", setupLoginForm);

    function setupLoginForm() {
        var form = document.getElementById("login-form");
        if (!form) return;

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            submitLogin(form);
        });
    }

    async function submitLogin(form) {
        var usr = document.getElementById("usr").value.trim();
        var pwd = document.getElementById("pwd").value;
        var remember = document.getElementById("remember_me");

        if (!usr || !pwd) {
            showError("Please enter both your username and password.");
            return;
        }

        var btn = form.querySelector(".login-btn");
        var originalHTML = btn.innerHTML;
        setBusy(btn, true, "Signing In…");
        clearError();

        // Fire and forget — a missing sound must never delay or block login.
        playSound("submit");

        try {
            var body = new URLSearchParams({ usr: usr, pwd: pwd });
            if (remember && remember.checked) body.append("remember_me", "1");

            var response = await fetch("/api/method/login", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "X-Frappe-CSRF-Token": CSRF_TOKEN,
                },
                body: body.toString(),
            });

            var data = await response.json().catch(function () { return {}; });

            if (response.ok) {
                // Full page load so the desk boots with the new session.
                window.location.href = REDIRECT_TO || data.home_page || "/app";
                return;
            }

            setBusy(btn, false, null, originalHTML);
            showError(extractMessage(data, response.status));
        } catch (error) {
            setBusy(btn, false, null, originalHTML);
            showError("Could not reach the server. Check your connection and try again.");
            console.error("Login request failed:", error);
        }
    }

    // Frappe reports auth failures via _server_messages (a JSON-encoded list
    // of JSON strings) rather than a plain field.
    function extractMessage(data, status) {
        try {
            var messages = JSON.parse(data._server_messages || "[]");
            for (var i = 0; i < messages.length; i++) {
                var parsed = JSON.parse(messages[i]);
                var text = stripHtml(parsed.message || "");
                if (text) return text;
            }
        } catch (e) { /* fall through to the generic message */ }

        if (data.message && typeof data.message === "string") return stripHtml(data.message);
        if (status === 401) return "Invalid login credentials.";
        if (status === 417) return "Too many failed attempts. Please try again later.";
        return "Login failed. Please try again.";
    }

    function stripHtml(html) {
        var tmp = document.createElement("div");
        tmp.innerHTML = html;
        return (tmp.textContent || "").trim();
    }

    function setBusy(btn, busy, label, originalHTML) {
        btn.disabled = busy;
        if (busy) {
            btn.innerHTML = "<span>" + label + "</span>";
        } else if (originalHTML) {
            btn.innerHTML = originalHTML;
        }
    }

    function showError(message) {
        var box = document.getElementById("login-error");
        if (!box) return;
        box.textContent = message;
        box.hidden = false;
    }

    function clearError() {
        var box = document.getElementById("login-error");
        if (!box) return;
        box.textContent = "";
        box.hidden = true;
    }

    async function playSound(eventName) {
        if (!SOUNDS_ENABLED) return;
        try {
            var response = await fetch(
                "/api/method/swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings.play_sound",
                {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Frappe-CSRF-Token": CSRF_TOKEN,
                    },
                    body: JSON.stringify({ event_name: eventName }),
                }
            );
            if (!response.ok) return;

            var data = await response.json();
            var sound = data && data.message;
            if (!sound || !sound.enabled || !sound.sound_file) return;

            var audio = new Audio(sound.sound_file);
            audio.volume = sound.volume;   // already 0–1 from the server
            await audio.play();
        } catch (error) {
            // Autoplay policies and missing files are non-fatal.
            console.debug("Sound playback skipped:", error);
        }
    }

    // Ctrl+Enter submits from anywhere on the page.
    document.addEventListener("keydown", function (e) {
        if (e.ctrlKey && e.key === "Enter") {
            var form = document.getElementById("login-form");
            if (form) form.requestSubmit();
        }
    });
})();
