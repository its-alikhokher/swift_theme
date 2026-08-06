/* GoldElite — namespaced logging. Levels: debug < info < warn < error < silent. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var LEVEL_ORDER = {
        debug: 0,
        info: 1,
        warn: 2,
        error: 3,
        silent: 4,
    };

    var CONSOLE_METHODS = {
        debug: "log",
        info: "info",
        warn: "warn",
        error: "error",
    };

    var DEFAULT_LEVEL = "warn";
    var currentLevel = DEFAULT_LEVEL;

    function write(level, namespace, args) {
        if (LEVEL_ORDER[level] < LEVEL_ORDER[currentLevel]) return;
        var prefix = "[GoldElite" + (namespace ? ":" + namespace : "") + "]";
        var method = CONSOLE_METHODS[level] || "log";
        if (typeof console !== "undefined" && console && typeof console[method] === "function") {
            var collected = Array.prototype.slice.call(args);
            console[method](prefix, collected);
        }
    }

    function setLevel(level) {
        if (!LEVEL_ORDER.hasOwnProperty(level)) {
            if (typeof console !== "undefined" && console && typeof console.warn === "function") {
                console.warn("[GoldElite:log] Unknown log level ignored: " + level);
            }
            return false;
        }
        currentLevel = level;
        return true;
    }

    function getLevel() {
        return currentLevel;
    }

    function isEnabled(level) {
        return LEVEL_ORDER[level] !== undefined && LEVEL_ORDER[level] >= LEVEL_ORDER[currentLevel];
    }

    function makeLogger(namespace) {
        return {
            debug: function () { write("debug", namespace, arguments); },
            info: function () { write("info", namespace, arguments); },
            warn: function () { write("warn", namespace, arguments); },
            error: function () { write("error", namespace, arguments); },
        };
    }

    GE.log = {
        levels: LEVEL_ORDER,
        debug: function () { write("debug", null, arguments); },
        info: function () { write("info", null, arguments); },
        warn: function () { write("warn", null, arguments); },
        error: function () { write("error", null, arguments); },
        ns: makeLogger,
        setLevel: setLevel,
        getLevel: getLevel,
        isEnabled: isEnabled,
    };
})(typeof window !== "undefined" ? window : globalThis);
