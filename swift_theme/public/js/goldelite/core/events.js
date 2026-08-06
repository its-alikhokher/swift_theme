/* GoldElite — typed event bus.
   Types are registered via define(); emit() rejects unknown types (typo safety).
   Handler errors never break the emit loop. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    var listeners = {};
    var defined = {};

    function define(type) {
        if (!type || typeof type !== "string") {
            throw new GE.error.Error(
                "Event type must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { type: type }
            );
        }
        if (defined[type]) {
            return false;
        }
        defined[type] = true;
        return true;
    }

    function assertDefined(type) {
        if (!defined[type]) {
            throw new GE.error.Error(
                "Event type is not defined: " + type,
                GE.error.codes.EVENT_UNDEFINED,
                { type: type }
            );
        }
    }

    function subscribe(type, handler, ctx, onceOnly) {
        if (typeof handler !== "function") {
            throw new GE.error.Error(
                "Event handler must be a function",
                GE.error.codes.INVALID_ARGUMENT,
                { type: type }
            );
        }
        if (!defined[type]) {
            define(type);
        }
        var list = listeners[type] || (listeners[type] = []);
        list.push({ handler: handler, ctx: ctx || null, once: !!onceOnly });
        return function unsubscribe() {
            off(type, handler);
        };
    }

    function on(type, handler, ctx) {
        return subscribe(type, handler, ctx, false);
    }

    function once(type, handler, ctx) {
        return subscribe(type, handler, ctx, true);
    }

    function off(type, handler) {
        var list = listeners[type];
        if (!list) {
            return false;
        }
        if (typeof handler !== "function") {
            delete listeners[type];
            return true;
        }
        var removed = false;
        for (var i = list.length - 1; i >= 0; i--) {
            if (list[i].handler === handler) {
                list.splice(i, 1);
                removed = true;
            }
        }
        return removed;
    }

    function emit(type, payload) {
        assertDefined(type);
        var list = listeners[type];
        if (!list || !list.length) {
            return false;
        }
        var snapshot = list.slice();
        for (var i = 0; i < snapshot.length; i++) {
            var entry = snapshot[i];
            try {
                entry.handler.call(entry.ctx || null, payload);
            } catch (err) {
                GE.error.report(err, GE.error.codes.UNKNOWN, { phase: "emit", type: type });
            }
            if (entry.once) {
                off(type, entry.handler);
            }
        }
        return true;
    }

    function hasListeners(type) {
        var list = listeners[type];
        return !!list && list.length > 0;
    }

    function types() {
        return Object.keys(defined);
    }

    // Clears listeners; the type registry persists so re-initialization stays valid.
    function destroy() {
        listeners = {};
    }

    // Full teardown: listeners AND the type registry.
    function reset() {
        listeners = {};
        defined = {};
    }

    // Register the foundation event names up-front (typed event system).
    Object.keys(GE.eventNames).forEach(function (key) {
        define(GE.eventNames[key]);
    });

    GE.events = {
        define: define,
        on: on,
        once: once,
        off: off,
        emit: emit,
        hasListeners: hasListeners,
        types: types,
        destroy: destroy,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
