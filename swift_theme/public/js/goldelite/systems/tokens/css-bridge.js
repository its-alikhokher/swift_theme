/* GoldElite — design token CSS bridge (D-005).
   Infrastructure that can expose tokens as CSS custom properties.
   Never applied automatically — consumers opt in. No existing CSS is
   redesigned or replaced; this is pure infrastructure. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    var DEFAULT_PREFIX = "ge";

    function varName(name, prefix) {
        var p = prefix || DEFAULT_PREFIX;
        return "--" + p + "-" + String(name).split(".").join("-");
    }

    // { "--ge-color-surface-primary": "#fff", ... } for the given token names
    // (all resolvable tokens by default).
    function generate(list) {
        var resolved = GE.tokens.resolver.resolveMap(list);
        var out = {};
        Object.keys(resolved).forEach(function (name) {
            out[varName(name)] = String(resolved[name]);
        });
        return out;
    }

    // Writes resolved tokens as CSS custom properties onto a given scope.
    function apply(scope, list) {
        if (!scope || !scope.style || typeof scope.style.setProperty !== "function") {
            return false;
        }
        var props = generate(list);
        Object.keys(props).forEach(function (prop) {
            scope.style.setProperty(prop, props[prop]);
        });
        return true;
    }

    // Removes bridge-managed custom properties from a scope.
    function clear(scope, list) {
        if (!scope || !scope.style || typeof scope.style.removeProperty !== "function") {
            return false;
        }
        var names = list || GE.tokens.registry.list();
        names.forEach(function (name) {
            scope.style.removeProperty(varName(name));
        });
        return true;
    }

    GE.tokens = GE.tokens || {};
    GE.tokens.css = {
        varName: varName,
        generate: generate,
        apply: apply,
        clear: clear,
    };
})(typeof window !== "undefined" ? window : globalThis);
