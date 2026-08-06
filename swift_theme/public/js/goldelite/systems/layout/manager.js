/* GoldElite — layout manager.
   Central registry of layouts with activate/deactivate/destroy semantics.
   No DOM work; a layout descriptor may carry its own lifecycle callbacks. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var layouts = {};
    var active = null;

    function normalizeDescriptor(name, descriptor) {
        if (util.isFunction(descriptor)) {
            return { name: name, activate: descriptor, deactivate: null, destroy: null };
        }
        if (!descriptor || typeof descriptor !== "object") {
            throw new GE.error.Error(
                "Layout descriptor must be an object or function",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name, descriptor: descriptor }
            );
        }
        ["activate", "deactivate", "destroy"].forEach(function (key) {
            if (descriptor[key] !== undefined && !util.isFunction(descriptor[key])) {
                throw new GE.error.Error(
                    "Layout " + key + " must be a function",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, key: key }
                );
            }
        });
        return {
            name: name,
            activate: descriptor.activate || null,
            deactivate: descriptor.deactivate || null,
            destroy: descriptor.destroy || null,
        };
    }

    function registerLayout(name, descriptor) {
        if (!util.isString(name) || !name) {
            throw new GE.error.Error(
                "Layout name must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (layouts[name]) {
            throw new GE.error.Error(
                "Layout already registered: " + name,
                GE.error.codes.ALREADY_REGISTERED,
                { name: name }
            );
        }
        layouts[name] = normalizeDescriptor(name, descriptor);
        return true;
    }

    function runCallback(layout, phase) {
        if (!layout || !layout[phase]) {
            return;
        }
        try {
            layout[phase]({ GE: GE, layout: layout.name });
        } catch (err) {
            GE.error.report(err, GE.error.codes.DESTROY_FAILED, { layout: layout.name, phase: phase });
        }
    }

    function activateLayout(name) {
        var layout = layouts[name];
        if (!layout) {
            throw new GE.error.Error(
                "Unknown layout: " + name,
                GE.error.codes.NOT_REGISTERED,
                { name: name }
            );
        }
        if (active === name) {
            return false;
        }
        var previous = active;
        if (previous && layouts[previous]) {
            runCallback(layouts[previous], "deactivate");
        }
        active = name;
        runCallback(layout, "activate");
        GE.events.emit(GE.layout.Events.CHANGED, {
            reason: "layout",
            active: name,
            previous: previous,
        });
        return true;
    }

    function deactivateLayout(name) {
        if (name !== undefined && name !== null && name !== active) {
            return false;
        }
        if (!active) {
            return false;
        }
        runCallback(layouts[active], "deactivate");
        active = null;
        GE.events.emit(GE.layout.Events.CHANGED, { reason: "layout", active: null, previous: name });
        return true;
    }

    function destroyLayout(name) {
        var layout = layouts[name];
        if (!layout) {
            return false;
        }
        if (active === name) {
            deactivateLayout(name);
        }
        runCallback(layout, "destroy");
        delete layouts[name];
        return true;
    }

    function activeLayout() {
        return active;
    }

    function isActive(name) {
        return active === name;
    }

    function list() {
        return Object.keys(layouts).sort();
    }

    function has(name) {
        return !!layouts[name];
    }

    function reset() {
        list().forEach(destroyLayout);
        active = null;
        return true;
    }

    GE.layout = GE.layout || {};
    GE.layout.manager = {
        registerLayout: registerLayout,
        activateLayout: activateLayout,
        deactivateLayout: deactivateLayout,
        destroyLayout: destroyLayout,
        active: activeLayout,
        isActive: isActive,
        has: has,
        list: list,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
