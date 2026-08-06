/* GoldElite — settings engine (S7).
   Schema-driven access with memory cache, defaults and validation. No UI. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var schemas = {};
    var values = {};

    var TYPES = ["string", "number", "boolean", "array", "object"];

    function splitKey(key) {
        if (!key || typeof key !== "string" || key.indexOf(".") < 0) {
            throw new GE.error.Error(
                "Setting key must be 'namespace.key', got: " + key,
                GE.error.codes.INVALID_ARGUMENT,
                { key: key }
            );
        }
        var parts = key.split(".");
        if (parts.length !== 2) {
            throw new GE.error.Error(
                "Setting key must have exactly one '.': " + key,
                GE.error.codes.INVALID_ARGUMENT,
                { key: key }
            );
        }
        return parts;
    }

    function normalizeField(field, ns, key) {
        if (!field || typeof field !== "object") {
            throw new GE.error.Error(
                "Setting field must be an object",
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns, key: key }
            );
        }
        if (field.type !== undefined && TYPES.indexOf(field.type) < 0) {
            throw new GE.error.Error(
                "Unsupported setting type: " + field.type,
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns, key: key }
            );
        }
        if (field.enum !== undefined && !Array.isArray(field.enum)) {
            throw new GE.error.Error(
                "Setting enum must be an array",
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns, key: key }
            );
        }
        if (field.validate !== undefined && typeof field.validate !== "function") {
            throw new GE.error.Error(
                "Setting validate must be a function",
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns, key: key }
            );
        }
        return {
            default: field.default,
            type: field.type,
            enum: field.enum || null,
            validate: field.validate || null,
            description: field.description || "",
        };
    }

    function typeMatches(type, value) {
        if (type === "array") return Array.isArray(value);
        if (type === "object") return util.isPlainObject(value);
        if (type === "number") return typeof value === "number" && isFinite(value);
        return typeof value === type;
    }

    function validateValue(field, value) {
        if (field.type && !typeMatches(field.type, value)) {
            return "must be of type '" + field.type + "'";
        }
        if (field.enum && field.enum.indexOf(value) < 0) {
            return "must be one of: " + field.enum.join(", ");
        }
        if (field.validate) {
            var result = field.validate(value);
            if (result !== true) {
                return typeof result === "string" ? result : "failed custom validation";
            }
        }
        return null;
    }

    function getField(ns, key) {
        var schema = schemas[ns];
        if (!schema) return null;
        return hasOwn.call(schema, key) ? schema[key] : null;
    }

    var hasOwn = Object.prototype.hasOwnProperty;

    function defineSchema(ns, fields) {
        if (!ns || typeof ns !== "string") {
            throw new GE.error.Error(
                "Schema namespace must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns }
            );
        }
        if (!util.isPlainObject(fields)) {
            throw new GE.error.Error(
                "Schema fields must be an object",
                GE.error.codes.INVALID_ARGUMENT,
                { ns: ns }
            );
        }
        schemas[ns] = schemas[ns] || {};
        Object.keys(fields).forEach(function (key) {
            schemas[ns][key] = normalizeField(fields[key], ns, key);
        });
        return true;
    }

    function get(key) {
        var parts = splitKey(key);
        var field = getField(parts[0], parts[1]);
        if (!field) {
            throw new GE.error.Error(
                "Setting is not defined: " + key,
                GE.error.codes.UNKNOWN_SETTING,
                { key: key }
            );
        }
        var nsValues = values[parts[0]];
        if (nsValues && hasOwn.call(nsValues, parts[1])) {
            return util.clone(nsValues[parts[1]]);
        }
        return util.clone(field.default);
    }

    function set(key, value) {
        var parts = splitKey(key);
        var ns = parts[0];
        var k = parts[1];
        var field = getField(ns, k);
        if (!field) {
            throw new GE.error.Error(
                "Setting is not defined: " + key,
                GE.error.codes.UNKNOWN_SETTING,
                { key: key }
            );
        }
        var problem = validateValue(field, value);
        if (problem) {
            GE.error.report(
                new GE.error.Error(
                    "Invalid value for " + key + ": " + problem,
                    GE.error.codes.INVALID_SETTING,
                    { key: key, value: value }
                ),
                GE.error.codes.INVALID_SETTING,
                { key: key }
            );
            return false;
        }
        var previous = get(key);
        values[ns] = values[ns] || {};
        values[ns][k] = util.clone(value);
        GE.events.emit(GE.eventNames.SETTINGS_CHANGED, {
            key: key,
            value: util.clone(value),
            previous: previous,
        });
        return true;
    }

    function has(key) {
        var parts = splitKey(key);
        return !!getField(parts[0], parts[1]);
    }

    function getNamespace(ns) {
        var schema = schemas[ns];
        var out = {};
        if (schema) {
            Object.keys(schema).forEach(function (key) {
                out[key] = get(ns + "." + key);
            });
        }
        return out;
    }

    function all() {
        var out = {};
        Object.keys(schemas).forEach(function (ns) {
            out[ns] = getNamespace(ns);
        });
        return out;
    }

    function resetNamespace(ns) {
        if (schemas[ns]) {
            values[ns] = {};
        }
        return true;
    }

    function reset() {
        values = {};
        return true;
    }

    function applyBoot(map) {
        if (!util.isPlainObject(map)) {
            return false;
        }
        var changed = false;
        Object.keys(map).forEach(function (ns) {
            var payload = map[ns];
            if (!schemas[ns] || !util.isPlainObject(payload)) return;
            Object.keys(payload).forEach(function (key) {
                if (getField(ns, key) && set(ns + "." + key, payload[key])) {
                    changed = true;
                }
            });
        });
        return changed;
    }

    // Adopts the canonical boot payload (frappe.boot.swift_theme) as the
    // "swift" settings namespace. Every value is registered into the schema
    // with its type and stored verbatim — one stable API, regardless of
    // whether the server data originated from v1 or v2 storage.
    function adoptBoot(flat, ns) {
        ns = ns || "swift";
        if (!util.isPlainObject(flat)) return false;
        schemas[ns] = schemas[ns] || {};
        values[ns] = values[ns] || {};
        var count = 0;
        Object.keys(flat).forEach(function (key) {
            var value = flat[key];
            if (value === null || value === undefined) return;
            if (util.isPlainObject(value) || util.isArray(value)) return;
            var type = typeof value === "number" ? "number"
                : (typeof value === "boolean" ? "boolean" : "string");
            schemas[ns][key] = normalizeField({ type: type, default: value }, ns, key);
            values[ns][key] = util.clone(value);
            count += 1;
        });
        return count > 0;
    }

    function validateAll() {
        var issues = [];
        Object.keys(values).forEach(function (ns) {
            Object.keys(values[ns] || {}).forEach(function (key) {
                var field = getField(ns, key);
                if (!field) {
                    issues.push(ns + "." + key + " has no schema");
                    return;
                }
                var problem = validateValue(field, values[ns][key]);
                if (problem) {
                    issues.push(ns + "." + key + ": " + problem);
                }
            });
        });
        if (issues.length) {
            GE.log.ns("settings").warn("validation issues: " + issues.join("; "));
        }
        return issues;
    }

    GE.settings = {
        defineSchema: defineSchema,
        get: get,
        set: set,
        has: has,
        getNamespace: getNamespace,
        all: all,
        reset: reset,
        resetNamespace: resetNamespace,
        applyBoot: applyBoot,
        adoptBoot: adoptBoot,
        Events: { CHANGED: GE.eventNames.SETTINGS_CHANGED },
        init: function () {
            var boot = null;
            if (global && global.frappe && global.frappe.boot) {
                boot = global.frappe.boot.swift_theme;
            }
            if (util.isPlainObject(boot)) {
                adoptBoot(boot);
            }
            validateAll();
            return true;
        },
        destroy: function () {
            values = {};
            return true;
        },
    };
})(typeof window !== "undefined" ? window : globalThis);
