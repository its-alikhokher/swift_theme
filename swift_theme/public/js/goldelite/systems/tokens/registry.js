/* GoldElite — design token registry (D-005).
   Stores token definitions (theme-independent) and enforces the category
   taxonomy. Validates names/values, protects immutable tokens, tracks
   runtime overrides separately from declared values. No theme values live
   here — themes define/import/override tokens later. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var hasOwn = Object.prototype.hasOwnProperty;

    var SEMANTIC = "semantic";

    // Category taxonomy (deliverable list). valueType drives validation:
    //   string | number | length | opacity | zindex | timing
    var CATEGORY_TYPES = {
        color: "string",
        typography: "string",
        spacing: "length",
        radius: "length",
        border: "string",
        elevation: "length",
        opacity: "opacity",
        motion: "string",
        breakpoint: "length",
        layout: "length",
        icon: "string",
        shadow: "string",
        "z-index": "zindex",
        timing: "timing",
    };

    var CATEGORY_LABELS = {
        color: "Colors",
        typography: "Typography",
        spacing: "Spacing",
        radius: "Radius",
        border: "Borders",
        elevation: "Elevation",
        opacity: "Opacity",
        motion: "Motion",
        breakpoint: "Breakpoints",
        layout: "Layout",
        icon: "Icons",
        shadow: "Shadows",
        "z-index": "Z-Index",
        timing: "Timing",
    };

    var NAME_SEGMENT = "[a-z][a-z0-9-]*";
    var NAME_REGEX = new RegExp("^" + NAME_SEGMENT + "(?:\\." + NAME_SEGMENT + ")*$");
    var ALIAS_REGEX = new RegExp("^\\{" + NAME_SEGMENT + "(?:\\." + NAME_SEGMENT + ")*\\}$");

    var definitions = {};
    var overrideValues = {};

    function isName(value) {
        return typeof value === "string" && NAME_REGEX.test(value);
    }

    function parseAlias(value) {
        if (typeof value === "string" && ALIAS_REGEX.test(value)) {
            return value.slice(1, -1);
        }
        return null;
    }

    function isLength(value) {
        if (typeof value === "number" && isFinite(value)) {
            return true;
        }
        if (typeof value !== "string") {
            return false;
        }
        return /^-?\d+(\.\d+)?(px|rem|em|%|vh|vw|ch|ex|fr)?$/.test(value);
    }

    function categoryOf(name) {
        var first = String(name).split(".")[0];
        return hasOwn.call(CATEGORY_TYPES, first) ? first : SEMANTIC;
    }

    function validateValue(def, value) {
        if (parseAlias(value)) {
            return null; // alias targets are checked during resolution
        }
        var kind = CATEGORY_TYPES[def.category];
        if (def.category === SEMANTIC || !kind) {
            if (typeof value !== "string" && typeof value !== "number" && typeof value !== "boolean") {
                return "must be a string, number or boolean";
            }
            return null;
        }
        switch (kind) {
            case "string":
                return typeof value === "string" ? null : "must be a string";
            case "number":
                return typeof value === "number" && isFinite(value) ? null : "must be a finite number";
            case "zindex":
                return typeof value === "number" && isFinite(value) && Math.floor(value) === value
                    ? null : "must be an integer";
            case "opacity":
                return typeof value === "number" && value >= 0 && value <= 1
                    ? null : "must be a number between 0 and 1";
            case "timing":
                return (typeof value === "number" && isFinite(value)) || isLength(value)
                    ? null : "must be a number or length";
            case "length":
                return isLength(value) ? null : "must be a number or length";
        }
        return null;
    }

    function normalizeDefinition(name, def) {
        if (!util.isPlainObject(def)) {
            throw new GE.error.Error(
                "Token definition must be an object",
                GE.error.codes.INVALID_TOKEN,
                { name: name, definition: def }
            );
        }
        if (def.value !== undefined && def.value !== null) {
            var vt = typeof def.value;
            if (vt !== "string" && vt !== "number" && vt !== "boolean") {
                throw new GE.error.Error(
                    "Token value must be a string, number or boolean",
                    GE.error.codes.INVALID_TOKEN,
                    { name: name, value: def.value }
                );
            }
        }
        if (def.extends !== undefined && def.extends !== null && !isName(def.extends)) {
            throw new GE.error.Error(
                "Token extends must be a valid token name",
                GE.error.codes.INVALID_TOKEN,
                { name: name, extends: def.extends }
            );
        }
        if (def.fallback !== undefined && def.fallback !== null && !isName(def.fallback)) {
            throw new GE.error.Error(
                "Token fallback must be a valid token name",
                GE.error.codes.INVALID_TOKEN,
                { name: name, fallback: def.fallback }
            );
        }
        if (def.immutable !== undefined && typeof def.immutable !== "boolean") {
            throw new GE.error.Error(
                "Token immutable must be a boolean",
                GE.error.codes.INVALID_TOKEN,
                { name: name, immutable: def.immutable }
            );
        }
        var category = def.category === undefined ? categoryOf(name) : def.category;
        if (category !== SEMANTIC && !hasOwn.call(CATEGORY_TYPES, category)) {
            throw new GE.error.Error(
                "Unknown token category: " + category,
                GE.error.codes.INVALID_TOKEN,
                { name: name, category: category }
            );
        }
        var normalized = {
            name: name,
            category: category,
            value: def.value !== undefined && def.value !== null ? def.value : undefined,
            extends: def.extends || null,
            fallback: def.fallback || null,
            immutable: def.immutable === true,
            description: def.description || "",
        };
        if (normalized.value === undefined && !normalized.extends) {
            throw new GE.error.Error(
                "Token must define a value or extends",
                GE.error.codes.INVALID_TOKEN,
                { name: name }
            );
        }
        if (normalized.value !== undefined) {
            var problem = validateValue(normalized, normalized.value);
            if (problem) {
                throw new GE.error.Error(
                    "Invalid value for " + name + ": " + problem,
                    GE.error.codes.INVALID_TOKEN,
                    { name: name, value: normalized.value }
                );
            }
        }
        return normalized;
    }

    function define(name, definition, opts) {
        opts = opts || {};
        if (!isName(name)) {
            throw new GE.error.Error(
                "Token name must be a valid dotted path",
                GE.error.codes.INVALID_TOKEN,
                { name: name }
            );
        }
        var normalized = normalizeDefinition(name, definition);
        var existing = definitions[name];
        if (existing && !opts.force) {
            return existing; // idempotent: existing definition wins
        }
        if (existing && existing.immutable) {
            throw new GE.error.Error(
                "Cannot override immutable token: " + name,
                GE.error.codes.IMMUTABLE_TOKEN,
                { name: name }
            );
        }
        definitions[name] = normalized;
        return normalized;
    }

    function getDefinition(name) {
        return definitions[name] || null;
    }

    function has(name) {
        return hasOwn.call(definitions, name);
    }

    function list() {
        return Object.keys(definitions);
    }

    function count() {
        return Object.keys(definitions).length;
    }

    function allDefinitions() {
        return util.clone(definitions);
    }

    function valueOf(name) {
        if (hasOwn.call(overrideValues, name)) {
            return overrideValues[name];
        }
        var def = definitions[name];
        return def ? def.value : undefined;
    }

    function setValue(name, value) {
        var def = definitions[name];
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
        var problem = validateValue(def, value);
        if (problem) {
            throw new GE.error.Error(
                "Invalid value for " + name + ": " + problem,
                GE.error.codes.INVALID_TOKEN,
                { name: name, value: value }
            );
        }
        var previous = valueOf(name);
        overrideValues[name] = value;
        return { name: name, previous: previous, value: value };
    }

    function overrides() {
        return util.clone(overrideValues);
    }

    function clearOverride(name) {
        if (hasOwn.call(overrideValues, name)) {
            delete overrideValues[name];
            return true;
        }
        return false;
    }

    function resetOverrides() {
        overrideValues = {};
        return true;
    }

    function clear(preserveImmutable) {
        Object.keys(definitions).forEach(function (name) {
            if (preserveImmutable && definitions[name].immutable) {
                return;
            }
            delete definitions[name];
            delete overrideValues[name];
        });
        return true;
    }

    function validate(name) {
        var def = definitions[name];
        if (!def) {
            return ["unknown token: " + name];
        }
        var issues = [];
        if (def.value !== undefined) {
            var problem = validateValue(def, def.value);
            if (problem) {
                issues.push(name + ": " + problem);
            }
        }
        if (def.extends && !definitions[def.extends]) {
            issues.push(name + ": extends target missing: " + def.extends);
        }
        if (def.fallback && !definitions[def.fallback]) {
            issues.push(name + ": fallback target missing: " + def.fallback);
        }
        return issues;
    }

    function categories() {
        var out = {};
        Object.keys(CATEGORY_TYPES).forEach(function (key) {
            out[key] = {
                key: key,
                label: CATEGORY_LABELS[key],
                valueType: CATEGORY_TYPES[key],
            };
        });
        return out;
    }

    GE.tokens = GE.tokens || {};
    GE.tokens.registry = {
        define: define,
        getDefinition: getDefinition,
        has: has,
        list: list,
        count: count,
        allDefinitions: allDefinitions,
        categoryOf: categoryOf,
        parseAlias: parseAlias,
        validateValue: validateValue,
        validate: validate,
        valueOf: valueOf,
        setValue: setValue,
        overrides: overrides,
        clearOverride: clearOverride,
        resetOverrides: resetOverrides,
        clear: clear,
        categories: categories,
    };
})(typeof window !== "undefined" ? window : globalThis);
