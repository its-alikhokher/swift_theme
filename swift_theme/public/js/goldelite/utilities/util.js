/* GoldElite — shared utilities (DOM-free). */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var hasOwn = Object.prototype.hasOwnProperty;

    function isUndefined(value) { return typeof value === "undefined"; }
    function isNull(value) { return value === null; }
    function isNil(value) { return value === null || value === undefined; }
    function isString(value) { return typeof value === "string"; }
    function isNumber(value) { return typeof value === "number" && isFinite(value); }
    function isBoolean(value) { return typeof value === "boolean"; }
    function isFunction(value) { return typeof value === "function"; }
    function isArray(value) { return Array.isArray(value); }
    function isPlainObject(value) {
        if (!value || typeof value !== "object") return false;
        var proto = Object.getPrototypeOf(value);
        return proto === Object.prototype || proto === null;
    }
    function isObject(value) { return value !== null && typeof value === "object"; }

    function clone(value) {
        if (isArray(value)) {
            return value.map(clone);
        }
        if (isPlainObject(value)) {
            var out = {};
            for (var key in value) {
                if (hasOwn.call(value, key)) out[key] = clone(value[key]);
            }
            return out;
        }
        return value;
    }

    function merge(target) {
        var out = clone(target || {});
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i];
            if (!isPlainObject(source)) continue;
            for (var key in source) {
                if (!hasOwn.call(source, key)) continue;
                if (isPlainObject(source[key]) && isPlainObject(out[key])) {
                    out[key] = merge({}, out[key], source[key]);
                } else {
                    out[key] = clone(source[key]);
                }
            }
        }
        return out;
    }

    function assign(target) {
        for (var i = 1; i < arguments.length; i++) {
            var source = arguments[i];
            if (!source) continue;
            for (var key in source) {
                if (hasOwn.call(source, key)) target[key] = source[key];
            }
        }
        return target;
    }

    function pick(source, keys) {
        var out = {};
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            if (hasOwn.call(source, key)) out[key] = source[key];
        }
        return out;
    }

    function omit(source, keys) {
        var out = {};
        var skip = {};
        for (var i = 0; i < keys.length; i++) skip[keys[i]] = true;
        for (var key in source) {
            if (hasOwn.call(source, key) && !skip[key]) out[key] = source[key];
        }
        return out;
    }

    function getPath(root, path, fallback) {
        if (!root || !path) return fallback;
        var parts = String(path).split(".");
        var node = root;
        for (var i = 0; i < parts.length; i++) {
            if (node === null || node === undefined) return fallback;
            node = node[parts[i]];
        }
        return node === undefined ? fallback : node;
    }

    function setPath(root, path, value) {
        var parts = String(path).split(".");
        var node = root;
        for (var i = 0; i < parts.length - 1; i++) {
            var part = parts[i];
            if (node[part] === null || typeof node[part] !== "object") node[part] = {};
            node = node[part];
        }
        node[parts[parts.length - 1]] = value;
        return root;
    }

    function noop() {}

    function identity(value) {
        return value;
    }

    function clamp(value, min, max) {
        return value < min ? min : (value > max ? max : value);
    }

    function capitalize(value) {
        return value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
    }

    function guid(prefix) {
        var base = (prefix || "ge") + "-";
        if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
            return base + crypto.randomUUID();
        }
        return base + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
    }

    function defer(fn) {
        setTimeout(function () { fn(); }, 0);
    }

    function once(fn) {
        var called = false;
        return function () {
            if (called) return undefined;
            called = true;
            return fn.apply(this, arguments);
        };
    }

    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var args = arguments;
            var self = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(self, args); }, wait);
        };
    }

    function throttle(fn, wait) {
        var last = 0;
        var timer = null;
        return function () {
            var now = Date.now();
            var remaining = wait - (now - last);
            var args = arguments;
            var self = this;
            if (remaining <= 0) {
                clearTimeout(timer);
                timer = null;
                last = now;
                fn.apply(self, args);
            } else if (!timer) {
                timer = setTimeout(function () {
                    last = Date.now();
                    timer = null;
                    fn.apply(self, args);
                }, remaining);
            }
        };
    }

    function isEqual(a, b) {
        if (a === b) return true;
        if (typeof a !== typeof b) return false;
        if (isPlainObject(a) && isPlainObject(b)) {
            var ka = Object.keys(a);
            var kb = Object.keys(b);
            if (ka.length !== kb.length) return false;
            for (var i = 0; i < ka.length; i++) {
                var key = ka[i];
                if (!hasOwn.call(b, key) || !isEqual(a[key], b[key])) return false;
            }
            return true;
        }
        if (isArray(a) && isArray(b)) {
            if (a.length !== b.length) return false;
            for (var j = 0; j < a.length; j++) {
                if (!isEqual(a[j], b[j])) return false;
            }
            return true;
        }
        return false;
    }

    GE.util = {
        isUndefined: isUndefined,
        isNull: isNull,
        isNil: isNil,
        isString: isString,
        isNumber: isNumber,
        isBoolean: isBoolean,
        isFunction: isFunction,
        isArray: isArray,
        isPlainObject: isPlainObject,
        isObject: isObject,
        clone: clone,
        merge: merge,
        assign: assign,
        pick: pick,
        omit: omit,
        getPath: getPath,
        setPath: setPath,
        noop: noop,
        identity: identity,
        clamp: clamp,
        capitalize: capitalize,
        guid: guid,
        defer: defer,
        once: once,
        debounce: debounce,
        throttle: throttle,
        isEqual: isEqual,
    };
})(typeof window !== "undefined" ? window : globalThis);
