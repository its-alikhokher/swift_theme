/* GoldElite — design token resolution (D-005).
   Resolves token values with alias references ({path}), declared fallbacks,
   and extends-based inheritance. Cycle detection across the whole resolution
   chain. Strict resolve() throws; safe get() never does. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    function compute(def, state) {
        var name = def.name;
        if (state.visited[name]) {
            throw new GE.error.Error(
                "Token resolution cycle at: " + name,
                GE.error.codes.TOKEN_CYCLE,
                { name: name }
            );
        }
        state.visited[name] = true;

        var value = GE.tokens.registry.valueOf(name);
        var alias = GE.tokens.registry.parseAlias(value);
        if (alias) {
            var target = GE.tokens.registry.getDefinition(alias);
            if (!target) {
                return fallback(def, "alias target missing: " + alias);
            }
            return compute(target, state);
        }
        if (value === undefined) {
            if (def.extends) {
                var parent = GE.tokens.registry.getDefinition(def.extends);
                if (!parent) {
                    return fallback(def, "extends target missing: " + def.extends);
                }
                return compute(parent, state);
            }
            return fallback(def, "token has no value");
        }
        return value;
    }

    function fallback(def, reason) {
        if (def.fallback) {
            var fdef = GE.tokens.registry.getDefinition(def.fallback);
            if (fdef) {
                return compute(fdef, { visited: {} });
            }
        }
        throw new GE.error.Error(
            "Unresolvable token: " + def.name + " (" + reason + ")",
            GE.error.codes.UNKNOWN_TOKEN,
            { name: def.name, reason: reason }
        );
    }

    // Strict resolution: throws UNKNOWN_TOKEN (missing/unresolvable) or TOKEN_CYCLE.
    function resolve(name) {
        var def = GE.tokens.registry.getDefinition(name);
        if (!def) {
            throw new GE.error.Error(
                "Unknown token: " + name,
                GE.error.codes.UNKNOWN_TOKEN,
                { name: name }
            );
        }
        return compute(def, { visited: {} });
    }

    // Safe resolution: never throws; returns fallbackValue on any failure.
    function get(name, fallbackValue) {
        var def = GE.tokens.registry.getDefinition(name);
        if (!def) {
            return fallbackValue;
        }
        try {
            return resolve(name);
        } catch (err) {
            GE.error.report(err, err.code || GE.error.codes.UNKNOWN, { name: name });
            return fallbackValue;
        }
    }

    // Resolves a set of names (all by default) into { name: value }.
    // Unresolvable tokens are skipped silently (callers probe via resolve()).
    function resolveMap(names) {
        var out = {};
        var target = names || GE.tokens.registry.list();
        for (var i = 0; i < target.length; i++) {
            var name = target[i];
            var value;
            try {
                value = resolve(name);
            } catch (ignored) {
                value = undefined;
            }
            if (value !== undefined) {
                out[name] = value;
            }
        }
        return out;
    }

    GE.tokens = GE.tokens || {};
    GE.tokens.resolver = {
        resolve: resolve,
        get: get,
        resolveMap: resolveMap,
    };
})(typeof window !== "undefined" ? window : globalThis);
