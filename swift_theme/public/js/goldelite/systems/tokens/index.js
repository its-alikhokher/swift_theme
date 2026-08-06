/* GoldElite — design token engine façade (D-005).
   Assembles GE.tokens: registry/resolver/io/css sub-systems, the public
   token API, runtime updates with events, validation, and lifecycle
   integration. Adopts an optional boot token payload from
   frappe.boot.swift_theme.tokens (forward-compatible; theme values live
   elsewhere, not in the engine). No visual changes. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;
    var log = GE.log.ns("tokens");

    var EVENTS = {
        LOADED: GE.eventNames.TOKENS_LOADED,
        CHANGED: GE.eventNames.TOKENS_CHANGED,
        RESET: GE.eventNames.TOKENS_RESET,
        VALIDATED: GE.eventNames.TOKENS_VALIDATED,
    };

    var initialized = false;

    // ------------------------------------------------------------------
    // Runtime updates (safe, evented, atomic)
    // ------------------------------------------------------------------

    function set(name, value) {
        var result;
        try {
            result = GE.tokens.registry.setValue(name, value);
        } catch (err) {
            GE.error.report(err, err.code || GE.error.codes.UNKNOWN, { name: name, value: value });
            return false;
        }
        var values = {};
        values[name] = value;
        GE.events.emit(EVENTS.CHANGED, {
            names: [name],
            values: values,
            previous: result.previous,
        });
        return true;
    }

    function setMany(map) {
        if (!util.isPlainObject(map)) {
            return false;
        }
        var plan = [];
        try {
            Object.keys(map).forEach(function (name) {
                var def = GE.tokens.registry.getDefinition(name);
                if (!def) {
                    throw new GE.error.Error(
                        "Unknown token: " + name,
                        GE.error.codes.UNKNOWN_TOKEN,
                        { name: name }
                    );
                }
                if (def.immutable) {
                    throw new GE.error.Error(
                        "Cannot set immutable token: " + name,
                        GE.error.codes.IMMUTABLE_TOKEN,
                        { name: name }
                    );
                }
                var problem = GE.tokens.registry.validateValue(def, map[name]);
                if (problem) {
                    throw new GE.error.Error(
                        "Invalid value for " + name + ": " + problem,
                        GE.error.codes.INVALID_TOKEN,
                        { name: name, value: map[name] }
                    );
                }
                plan.push(name);
            });
        } catch (err) {
            GE.error.report(err, err.code || GE.error.codes.UNKNOWN, { map: map });
            return false;
        }
        var names = [];
        var values = {};
        plan.forEach(function (name) {
            GE.tokens.registry.setValue(name, map[name]);
            names.push(name);
            values[name] = map[name];
        });
        GE.events.emit(EVENTS.CHANGED, { names: names, values: values });
        return true;
    }

    function reset() {
        var result = GE.tokens.io.reset();
        GE.events.emit(EVENTS.RESET, { count: result.count });
        return true;
    }

    // ------------------------------------------------------------------
    // Import / export (evented)
    // ------------------------------------------------------------------

    function emitLoaded(result) {
        validateAll();
        GE.events.emit(EVENTS.LOADED, {
            count: GE.tokens.registry.count(),
            imported: result.imported,
            skipped: result.skipped,
        });
        if (result.imported > 0) {
            GE.events.emit(EVENTS.CHANGED, {
                names: GE.tokens.registry.list(),
                values: GE.tokens.resolver.resolveMap(),
            });
        }
        return result;
    }

    function importSet(payload, opts) {
        return emitLoaded(GE.tokens.io.import(payload, opts));
    }

    function importJSON(json, opts) {
        return emitLoaded(GE.tokens.io.importJSON(json, opts));
    }

    // ------------------------------------------------------------------
    // Inspection
    // ------------------------------------------------------------------

    function all() {
        return GE.tokens.resolver.resolveMap();
    }

    function describe(name) {
        var def = GE.tokens.registry.getDefinition(name);
        if (!def) {
            return null;
        }
        var resolved;
        try {
            resolved = GE.tokens.resolver.resolve(name);
        } catch (ignored) {
            resolved = undefined;
        }
        return {
            name: name,
            category: def.category,
            value: def.value,
            resolved: resolved,
            extends: def.extends,
            fallback: def.fallback,
            immutable: def.immutable,
            description: def.description,
        };
    }

    function validateAll() {
        var issues = [];
        GE.tokens.registry.list().forEach(function (name) {
            issues = issues.concat(GE.tokens.registry.validate(name));
            try {
                GE.tokens.resolver.resolve(name);
            } catch (err) {
                issues.push(name + ": " + err.message);
            }
        });
        var ok = issues.length === 0;
        GE.events.emit(EVENTS.VALIDATED, {
            ok: ok,
            issues: issues.slice(),
            count: GE.tokens.registry.count(),
        });
        if (issues.length) {
            log.warn("validation issues: " + issues.length);
        }
        return issues;
    }

    // ------------------------------------------------------------------
    // Lifecycle integration
    // ------------------------------------------------------------------

    function init() {
        if (initialized) {
            return false;
        }
        var boot = null;
        if (global.frappe && global.frappe.boot && global.frappe.boot.swift_theme) {
            boot = global.frappe.boot.swift_theme.tokens;
        }
        if (util.isPlainObject(boot)) {
            try {
                GE.tokens.io.import(boot, { mode: "merge" });
            } catch (err) {
                GE.error.report(err, GE.error.codes.INIT_FAILED, { phase: "tokens-boot" });
            }
        }
        validateAll();
        initialized = true;
        log.debug("token engine ready — schema v" + GE.tokens.io.version() + ", " +
            GE.tokens.registry.count() + " tokens");
        GE.events.emit(EVENTS.LOADED, {
            count: GE.tokens.registry.count(),
            version: GE.tokens.io.version(),
            source: boot ? "boot" : "empty",
        });
        return true;
    }

    function destroy() {
        if (!initialized) {
            return false;
        }
        GE.tokens.registry.clear(true); // drop non-immutable definitions
        GE.tokens.registry.resetOverrides();
        initialized = false;
        return true;
    }

    // ------------------------------------------------------------------
    // Façade
    // ------------------------------------------------------------------

    GE.tokens = GE.tokens || {};
    GE.tokens.Events = EVENTS;
    GE.tokens.define = function (name, def) {
        return GE.tokens.registry.define(name, def);
    };
    GE.tokens.has = GE.tokens.registry.has;
    GE.tokens.get = GE.tokens.resolver.get;
    GE.tokens.resolve = GE.tokens.resolver.resolve;
    GE.tokens.set = set;
    GE.tokens.setMany = setMany;
    GE.tokens.reset = reset;
    GE.tokens.import = importSet;
    GE.tokens.importJSON = importJSON;
    GE.tokens.export = function (opts) {
        return GE.tokens.io.export(opts);
    };
    GE.tokens.exportJSON = function (opts) {
        return GE.tokens.io.exportJSON(opts);
    };
    GE.tokens.schemaVersion = GE.tokens.io.version;
    GE.tokens.registerMigration = GE.tokens.io.registerMigration;
    GE.tokens.list = GE.tokens.registry.list;
    GE.tokens.count = GE.tokens.registry.count;
    GE.tokens.categories = GE.tokens.registry.categories;
    GE.tokens.all = all;
    GE.tokens.describe = describe;
    GE.tokens.validate = validateAll;
    GE.tokens.init = init;
    GE.tokens.destroy = destroy;
})(typeof window !== "undefined" ? window : globalThis);
