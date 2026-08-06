/* GoldElite — layout layer system.
   Logical layer registry ONLY (naming + stacking order). No styling, no DOM. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var order = [];

    var DEFAULT_LAYERS = [
        "background",
        "content",
        "floating",
        "overlay",
        "modal",
        "toast",
        "tooltip",
    ];

    function registerDefaults() {
        DEFAULT_LAYERS.forEach(function (name) {
            register(name);
        });
        return true;
    }

    function register(name, index) {
        if (!util.isString(name) || !name) {
            throw new GE.error.Error(
                "Layer name must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (order.indexOf(name) >= 0) {
            throw new GE.error.Error(
                "Layer already registered: " + name,
                GE.error.codes.ALREADY_REGISTERED,
                { name: name }
            );
        }
        if (index === undefined) {
            order.push(name);
            return true;
        }
        if (!util.isNumber(index) || index < 0 || index > order.length) {
            throw new GE.error.Error(
                "Layer index must be within 0.." + order.length,
                GE.error.codes.INVALID_ARGUMENT,
                { name: name, index: index }
            );
        }
        order.splice(index, 0, name);
        return true;
    }

    function unregister(name) {
        var index = order.indexOf(name);
        if (index < 0) {
            return false;
        }
        order.splice(index, 1);
        return true;
    }

    function exists(name) {
        return order.indexOf(name) >= 0;
    }

    function index(name) {
        var index = order.indexOf(name);
        if (index < 0) {
            return -1;
        }
        return index;
    }

    function list() {
        return order.slice();
    }

    function above(name) {
        var position = index(name);
        if (position < 0) {
            return null;
        }
        return position + 1 < order.length ? order[position + 1] : null;
    }

    function below(name) {
        var position = index(name);
        if (position < 0) {
            return null;
        }
        return position > 0 ? order[position - 1] : null;
    }

    function reset() {
        order = [];
        return true;
    }

    GE.layout = GE.layout || {};
    GE.layout.layers = {
        register: register,
        unregister: unregister,
        registerDefaults: registerDefaults,
        exists: exists,
        index: index,
        above: above,
        below: below,
        list: list,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
