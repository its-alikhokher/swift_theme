/* GoldElite — design token io (D-005).
   Schema versioning + migration registry, JSON import/export of token sets,
   and reset. Import validates schema/version, protects immutable tokens,
   and supports replace/merge modes. Future-ready for branded themes. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var SCHEMA = "goldelite.tokens";
    var SCHEMA_VERSION = 1;

    // fromVersion -> { to: fromVersion + 1, fn(payload) }
    var migrations = {};

    function version() {
        return SCHEMA_VERSION;
    }

    function registerMigration(from, to, fn) {
        if (typeof from !== "number" || typeof to !== "number" || to !== from + 1 || typeof fn !== "function") {
            throw new GE.error.Error(
                "Migration must define from, from+1, and a function",
                GE.error.codes.INVALID_ARGUMENT,
                { from: from, to: to }
            );
        }
        migrations[from] = { to: to, fn: fn };
        return true;
    }

    // Walks the payload version up to SCHEMA_VERSION using registered steps.
    function migrate(payload) {
        var current = SCHEMA_VERSION;
        var versionIn = payload.version === undefined ? current : payload.version;
        if (typeof versionIn !== "number" || !isFinite(versionIn)) {
            throw new GE.error.Error(
                "Token set version must be a number",
                GE.error.codes.INVALID_ARGUMENT,
                { version: payload.version }
            );
        }
        if (versionIn > current) {
            throw new GE.error.Error(
                "Token set version " + versionIn + " is newer than supported " + current,
                GE.error.codes.INVALID_ARGUMENT,
                { version: versionIn }
            );
        }
        var out = payload;
        var v = versionIn;
        while (v < current) {
            var step = migrations[v];
            if (!step || step.to !== v + 1) {
                throw new GE.error.Error(
                    "No migration path from token schema " + v + " to " + current,
                    GE.error.codes.INVALID_ARGUMENT,
                    { version: v }
                );
            }
            out = step.fn(util.clone(out)) || out;
            v += 1;
        }
        return out;
    }

    function normalizeTokens(tokens) {
        if (util.isPlainObject(tokens)) {
            var map = {};
            Object.keys(tokens).forEach(function (name) {
                map[name] = tokens[name];
            });
            return map;
        }
        if (util.isArray(tokens)) {
            var out = {};
            tokens.forEach(function (def) {
                if (util.isPlainObject(def) && typeof def.name === "string") {
                    out[def.name] = def;
                }
            });
            return out;
        }
        return null;
    }

    function exportSet(opts) {
        opts = opts || {};
        var defs = GE.tokens.registry.allDefinitions();
        var tokens = {};
        Object.keys(defs).forEach(function (name) {
            var def = defs[name];
            tokens[name] = {
                value: def.value,
                category: def.category,
                extends: def.extends || undefined,
                fallback: def.fallback || undefined,
                immutable: def.immutable || undefined,
                description: def.description || undefined,
            };
        });
        var payload = {
            schema: SCHEMA,
            version: SCHEMA_VERSION,
            generatedAt: new Date().toISOString(),
            tokens: tokens,
        };
        if (opts.resolved) {
            payload.values = GE.tokens.resolver.resolveMap();
        }
        return payload;
    }

    function exportJSON(opts) {
        return JSON.stringify(exportSet(opts), null, opts && opts.pretty === false ? undefined : 2);
    }

    function importSet(payload, opts) {
        opts = opts || {};
        if (!util.isPlainObject(payload)) {
            throw new GE.error.Error(
                "Token set must be an object",
                GE.error.codes.INVALID_ARGUMENT,
                { payload: payload }
            );
        }
        if (payload.schema !== undefined && payload.schema !== SCHEMA) {
            throw new GE.error.Error(
                "Unknown token schema: " + payload.schema,
                GE.error.codes.INVALID_ARGUMENT,
                { schema: payload.schema }
            );
        }
        var migrated = migrate(payload);
        var tokens = normalizeTokens(migrated.tokens);
        if (!tokens) {
            throw new GE.error.Error(
                "Token set must define a tokens map or array",
                GE.error.codes.INVALID_ARGUMENT,
                {}
            );
        }
        if (opts.mode === "replace") {
            GE.tokens.registry.clear(true); // keep immutable core tokens
            GE.tokens.registry.resetOverrides();
        }
        var imported = 0;
        var skipped = [];
        Object.keys(tokens).forEach(function (name) {
            var def = tokens[name];
            try {
                var existing = GE.tokens.registry.getDefinition(name);
                if (existing && existing.immutable) {
                    skipped.push({ name: name, reason: "immutable" });
                    return;
                }
                GE.tokens.registry.define(name, def, { force: true });
                imported += 1;
            } catch (err) {
                skipped.push({ name: name, reason: err.message || String(err) });
            }
        });
        return { imported: imported, skipped: skipped };
    }

    function importJSON(json, opts) {
        var parsed;
        try {
            parsed = JSON.parse(json);
        } catch (err) {
            throw new GE.error.Error(
                "Invalid token JSON: " + (err && err.message ? err.message : String(err)),
                GE.error.codes.INVALID_ARGUMENT,
                { error: err }
            );
        }
        return importSet(parsed, opts);
    }

    function reset() {
        var count = Object.keys(GE.tokens.registry.overrides()).length;
        GE.tokens.registry.resetOverrides();
        return { count: count };
    }

    GE.tokens = GE.tokens || {};
    GE.tokens.io = {
        version: version,
        registerMigration: registerMigration,
        migrate: migrate,
        export: exportSet,
        exportJSON: exportJSON,
        import: importSet,
        importJSON: importJSON,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
