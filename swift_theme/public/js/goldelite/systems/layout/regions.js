/* GoldElite — layout region registry.
   Standard regions tracked as state (element binding is optional and never
   mutated here). Emits region-added / region-removed events. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var regions = {};

    var STANDARD_REGIONS = [
        "header",
        "sidebar",
        "content",
        "footer",
        "right-panel",
        "overlay",
        "command-palette",
        "notification-area",
    ];

    function registerDefaults() {
        STANDARD_REGIONS.forEach(function (name) {
            register(name, {});
        });
        return true;
    }

    function normalizeDescriptor(descriptor) {
        descriptor = descriptor || {};
        if (!util.isPlainObject(descriptor)) {
            throw new GE.error.Error(
                "Region descriptor must be an object",
                GE.error.codes.INVALID_ARGUMENT,
                { descriptor: descriptor }
            );
        }
        if (descriptor.layer !== undefined && !GE.layout.layers.exists(descriptor.layer)) {
            throw new GE.error.Error(
                "Region references unknown layer: " + descriptor.layer,
                GE.error.codes.INVALID_ARGUMENT,
                { layer: descriptor.layer }
            );
        }
        if (descriptor.element !== undefined && !util.isObject(descriptor.element)) {
            throw new GE.error.Error(
                "Region element must be an object (DOM node)",
                GE.error.codes.INVALID_ARGUMENT,
                { element: descriptor.element }
            );
        }
        return {
            layer: descriptor.layer || null,
            element: descriptor.element || null,
            visible: descriptor.visible !== false,
            order: util.isNumber(descriptor.order) ? descriptor.order : 0,
        };
    }

    function register(name, descriptor) {
        if (!util.isString(name) || !name) {
            throw new GE.error.Error(
                "Region name must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (regions[name]) {
            throw new GE.error.Error(
                "Region already registered: " + name,
                GE.error.codes.ALREADY_REGISTERED,
                { name: name }
            );
        }
        regions[name] = normalizeDescriptor(descriptor);
        GE.events.emit(GE.layout.Events.REGION_ADDED, { name: name, region: get(name) });
        return true;
    }

    function has(name) {
        return !!regions[name];
    }

    function get(name) {
        var region = regions[name];
        if (!region) {
            return null;
        }
        return util.clone(region);
    }

    function setVisibility(name, visible) {
        var region = regions[name];
        if (!region) {
            return false;
        }
        region.visible = !!visible;
        GE.events.emit(GE.layout.Events.CHANGED, { reason: "region-visibility", name: name });
        return true;
    }

    function remove(name) {
        var region = regions[name];
        if (!region) {
            return false;
        }
        delete regions[name];
        GE.events.emit(GE.layout.Events.REGION_REMOVED, { name: name });
        return true;
    }

    function list() {
        return Object.keys(regions).sort();
    }

    function reset() {
        regions = {};
        return true;
    }

    GE.layout = GE.layout || {};
    GE.layout.regions = {
        register: register,
        registerDefaults: registerDefaults,
        has: has,
        get: get,
        setVisibility: setVisibility,
        remove: remove,
        list: list,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
