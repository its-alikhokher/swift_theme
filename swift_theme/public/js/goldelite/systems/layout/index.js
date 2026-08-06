/* GoldElite — layout engine façade (D-003 foundation).
   Assembles GE.layout = { manager, context, layers, regions, responsive, chrome }.
   Emits typed layout events through the existing GE.events bus under both
   canonical (ge:layout:*) and short (layout:*) names. No visual changes. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;
    var log = GE.log.ns("layout");

    var SUFFIX_TO_KEY = {
        ready: "READY",
        resize: "RESIZE",
        "region-added": "REGION_ADDED",
        "region-removed": "REGION_REMOVED",
        changed: "CHANGED",
    };

    var EVENTS = {};
    Object.keys(SUFFIX_TO_KEY).forEach(function (suffix) {
        EVENTS[SUFFIX_TO_KEY[suffix]] = "ge:layout:" + suffix;
    });

    // Mirror canonical events onto the short names so the documented
    // contract (layout:ready, layout:resize, ...) also works.
    Object.keys(SUFFIX_TO_KEY).forEach(function (suffix) {
        GE.events.define("layout:" + suffix);
        GE.events.on("ge:layout:" + suffix, function (payload) {
            GE.events.emit("layout:" + suffix, payload);
        });
    });

    function normalizeEvent(event) {
        if (!util.isString(event) || !event) {
            return null;
        }
        var prefix = "ge:layout:";
        var short = "layout:";
        var suffix = null;
        if (event.indexOf(prefix) === 0) {
            suffix = event.slice(prefix.length);
        } else if (event.indexOf(short) === 0) {
            suffix = event.slice(short.length);
        }
        return SUFFIX_TO_KEY[suffix] ? prefix + suffix : null;
    }

    function on(event, handler, ctx) {
        var canonical = normalizeEvent(event);
        if (!canonical) {
            throw new GE.error.Error(
                "Unknown layout event: " + event,
                GE.error.codes.INVALID_ARGUMENT,
                { event: event }
            );
        }
        return GE.events.on(canonical, handler, ctx);
    }

    function snapshot() {
        return {
            activeLayout: GE.layout.manager.active(),
            mode: GE.layout.context.get("mode"),
            viewport: GE.layout.context.get("viewport"),
            regions: GE.layout.regions.list(),
            layers: GE.layout.layers.list(),
        };
    }

    var initialized = false;

    function init() {
        if (initialized) {
            return false;
        }
        GE.layout.layers.registerDefaults();
        GE.layout.regions.registerDefaults();
        GE.layout.manager.registerLayout("default", {});
        GE.layout.context.update();
        GE.layout.context.observe();
        GE.layout.chrome.describe(); // record baseline; read-only
        initialized = true;
        log.debug("layout engine ready");
        GE.events.emit(EVENTS.READY, snapshot());
        return true;
    }

    function destroy() {
        if (!initialized) {
            return false;
        }
        GE.layout.context.stop();
        GE.layout.manager.reset();
        GE.layout.regions.reset();
        GE.layout.layers.reset();
        initialized = false;
        return true;
    }

    GE.layout = GE.layout || {};
    GE.layout.Events = EVENTS;
    GE.layout.on = on;
    GE.layout.snapshot = snapshot;
    GE.layout.init = init;
    GE.layout.destroy = destroy;
})(typeof window !== "undefined" ? window : globalThis);
