/* GoldElite — lifecycle. Single init entry, single shutdown, multiple-init
   protection, initializer registry, automatic boot on DOM ready. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;
    var STATES = GE.states;
    var EVENT_NAMES = GE.eventNames;

    var initializers = [];
    var readyQueue = [];
    var initOptions = null;

    function registerInitializer(mod) {
        if (!mod || typeof mod !== "object" || typeof mod.name !== "string" || !mod.name) {
            throw new GE.error.Error(
                "Initializer must define a name",
                GE.error.codes.INVALID_ARGUMENT,
                { mod: mod }
            );
        }
        if (typeof mod.init !== "function" && typeof mod.destroy !== "function") {
            throw new GE.error.Error(
                "Initializer must define init() or destroy()",
                GE.error.codes.INVALID_ARGUMENT,
                { name: mod.name }
            );
        }
        initializers.push(mod);
        return mod;
    }

    function ordered() {
        return initializers.slice().sort(function (a, b) {
            return (a.order || 0) - (b.order || 0);
        });
    }

    function runInit(mod) {
        if (typeof mod.init !== "function") return;
        try {
            mod.init({ GE: GE, options: initOptions });
        } catch (err) {
            GE.error.report(err, GE.error.codes.INIT_FAILED, { module: mod.name });
        }
    }

    function runDestroy(mod) {
        if (typeof mod.destroy !== "function") return;
        try {
            mod.destroy({ GE: GE });
        } catch (err) {
            GE.error.report(err, GE.error.codes.DESTROY_FAILED, { module: mod.name });
        }
    }

    function init(options) {
        if (GE.state === STATES.INITIALIZING) {
            return false;
        }
        if (GE.state === STATES.READY) {
            GE.log.ns("lifecycle").warn("init() ignored — GoldElite is already ready");
            return true;
        }
        initOptions = options || null;
        GE.state = STATES.INITIALIZING;

        GE.events.emit(EVENT_NAMES.LIFECYCLE_INIT, { options: initOptions });

        ordered().forEach(runInit);

        GE.state = STATES.READY;
        GE.events.emit(EVENT_NAMES.LIFECYCLE_READY, { options: initOptions });

        var queue = readyQueue.splice(0, readyQueue.length);
        queue.forEach(util.defer);
        return true;
    }

    function destroy() {
        if (GE.state !== STATES.READY && GE.state !== STATES.INITIALIZING) {
            GE.log.ns("lifecycle").warn("destroy() ignored — GoldElite is not running");
            return false;
        }
        GE.events.emit(EVENT_NAMES.LIFECYCLE_DESTROY, {});
        ordered().slice().reverse().forEach(runDestroy);
        GE.events.destroy();
        GE.state = STATES.DESTROYED;
        return true;
    }

    function isReady() {
        return GE.state === STATES.READY;
    }

    function onReady(fn) {
        if (typeof fn !== "function") {
            throw new GE.error.Error(
                "onReady expects a function",
                GE.error.codes.INVALID_ARGUMENT
            );
        }
        if (GE.state === STATES.READY) {
            util.defer(fn);
            return;
        }
        readyQueue.push(fn);
    }

    GE.lifecycle = {
        init: init,
        destroy: destroy,
        isReady: isReady,
        state: function () { return GE.state; },
        registerInitializer: registerInitializer,
        onReady: onReady,
    };

    // Top-level entry points.
    GE.init = init;
    GE.destroy = destroy;
    GE.isReady = isReady;
    GE.onReady = onReady;

    // Wire the foundation systems into the lifecycle.
    registerInitializer({ name: "settings", order: 10, init: GE.settings.init, destroy: GE.settings.destroy });
    registerInitializer({ name: "flags", order: 20, init: GE.flags.init, destroy: GE.flags.destroy });
    registerInitializer({ name: "compat", order: 30, init: GE.compat.init, destroy: GE.compat.destroy });
    registerInitializer({ name: "tokens", order: 35, init: GE.tokens.init, destroy: GE.tokens.destroy });
    registerInitializer({ name: "layout", order: 40, init: GE.layout.init, destroy: GE.layout.destroy });
    registerInitializer({ name: "components", order: 45, init: GE.components.init, destroy: GE.components.shutdown });

    // Single automatic initialization entry (init() guards itself against repeats).
    function autoInit() {
        if (!global.document) {
            return;
        }
        if (global.document.readyState === "loading") {
            global.document.addEventListener("DOMContentLoaded", function () {
                init();
            });
        } else {
            util.defer(init);
        }
    }
    autoInit();
})(typeof window !== "undefined" ? window : globalThis);
