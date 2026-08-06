/* GoldElite — feature flag engine (S14).
   Tiers: user (locally settable), tenant/global (server-controlled).
   Seeded with the approved starter catalog (ARCHITECTURE.md §5). */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    var definitions = {};
    var serverValues = {};
    var userValues = {};

    var hasOwn = Object.prototype.hasOwnProperty;

    var TIERS = {
        USER: "user",
        TENANT: "tenant",
        GLOBAL: "global",
    };

    var DEFAULT_FLAGS = [
        { id: "replace-chrome", tier: "user", default: false, system: true, description: "Replace Frappe navbar/sidebar chrome with the GoldElite shell" },
        { id: "floating-sidebar", tier: "user", default: false, system: true, description: "Render the navigation sidebar as a floating dock" },
        { id: "glass-mode", tier: "user", default: false, system: true, description: "Enable translucent glass surfaces" },
        { id: "animations", tier: "user", default: true, system: true, description: "Enable GoldElite motion" },
        { id: "workspace-home", tier: "user", default: true, system: true, description: "Use the GoldElite home dashboard" },
        { id: "command-palette", tier: "user", default: true, system: true, description: "Enable the command palette" },
        { id: "global-search", tier: "user", default: true, system: true, description: "Enable global search integration" },
        { id: "keyboard-shortcuts", tier: "user", default: true, system: true, description: "Enable GoldElite keyboard shortcuts" },
        { id: "custom-fonts", tier: "user", default: true, system: true, description: "Enable GoldElite font configuration" },
        { id: "custom-login", tier: "user", default: true, system: true, description: "Render the GoldElite login layout" },
        { id: "toast-centre", tier: "user", default: true, system: true, description: "Enable the GoldElite toast centre" },
        { id: "sound-effects", tier: "user", default: true, system: true, description: "Enable GoldElite sound effects" },
        { id: "desktop-notifications", tier: "user", default: false, system: true, description: "Enable browser desktop notifications" },
        { id: "compact-density", tier: "user", default: false, system: true, description: "Enable compact density" },
        { id: "developer-mode", tier: "user", default: false, system: true, description: "Enable the developer/debug panel" },
        { id: "window-management", tier: "user", default: false, system: true, description: "Enable detachable dockable windows" },
        { id: "detachable-views", tier: "user", default: false, system: true, description: "Enable detaching views into windows" },
        { id: "plugin-system", tier: "tenant", default: true, system: true, description: "Enable the plugin loader" },
        { id: "perf-layer", tier: "tenant", default: true, system: true, description: "Enable the performance layer" },
        { id: "lazy-loading", tier: "tenant", default: true, system: true, description: "Load systems on demand" },
        { id: "content-containment", tier: "tenant", default: true, system: true, description: "Apply CSS content containment" },
    ];

    function normalizeFlag(flag) {
        if (!flag || typeof flag !== "object" || typeof flag.id !== "string" || !flag.id) {
            throw new GE.error.Error(
                "Flag must define a non-empty id",
                GE.error.codes.INVALID_ARGUMENT,
                { flag: flag }
            );
        }
        var tier = flag.tier || TIERS.USER;
        if (tier !== TIERS.USER && tier !== TIERS.TENANT && tier !== TIERS.GLOBAL) {
            throw new GE.error.Error(
                "Unknown flag tier: " + tier,
                GE.error.codes.INVALID_ARGUMENT,
                { id: flag.id }
            );
        }
        return {
            id: flag.id,
            tier: tier,
            default: flag.default === true,
            system: flag.system === true,
            description: flag.description || "",
        };
    }

    function define(flag) {
        var normalized = normalizeFlag(flag);
        if (definitions[normalized.id]) {
            // Idempotent: existing definition wins; systems may re-assert their flags.
            return definitions[normalized.id];
        }
        definitions[normalized.id] = normalized;
        return normalized;
    }

    function isDefined(id) {
        return hasOwn.call(definitions, id);
    }

    function isEnabled(id) {
        var flag = definitions[id];
        if (!flag) {
            GE.log.ns("flags").warn("Unknown flag: " + id);
            return false;
        }
        if (flag.tier === TIERS.USER && hasOwn.call(userValues, id)) {
            return userValues[id] === true;
        }
        if (hasOwn.call(serverValues, id)) {
            return serverValues[id] === true;
        }
        return flag.default;
    }

    function set(id, value) {
        var flag = definitions[id];
        if (!flag) {
            throw new GE.error.Error(
                "Unknown flag: " + id,
                GE.error.codes.UNKNOWN_FLAG,
                { id: id }
            );
        }
        if (flag.tier !== TIERS.USER) {
            GE.error.report(
                new GE.error.Error(
                    "Cannot set " + flag.tier + "-tier flag locally: " + id,
                    GE.error.codes.INVALID_FLAG,
                    { id: id }
                ),
                GE.error.codes.INVALID_FLAG,
                { id: id }
            );
            return false;
        }
        var previous = isEnabled(id);
        var next = value === true;
        if (previous === next) {
            return true;
        }
        userValues[id] = next;
        GE.events.emit(GE.eventNames.FLAGS_CHANGED, {
            id: id,
            value: next,
            previous: previous,
            tier: flag.tier,
        });
        return true;
    }

    function enable(id) {
        return set(id, true);
    }

    function disable(id) {
        return set(id, false);
    }

    function applyServer(map) {
        if (!map || typeof map !== "object") {
            return false;
        }
        var changed = false;
        Object.keys(map).forEach(function (id) {
            var value = map[id] === true;
            var previous = isEnabled(id);
            serverValues[id] = value;
            if (previous !== value && definitions[id]) {
                changed = true;
                GE.events.emit(GE.eventNames.FLAGS_CHANGED, {
                    id: id,
                    value: value,
                    previous: previous,
                    tier: definitions[id].tier,
                    source: "server",
                });
            }
        });
        return changed;
    }

    function list() {
        return Object.keys(definitions).sort().map(function (id) {
            var flag = definitions[id];
            return {
                id: id,
                tier: flag.tier,
                default: flag.default,
                effective: isEnabled(id),
                system: flag.system,
                description: flag.description,
            };
        });
    }

    function count() {
        return Object.keys(definitions).length;
    }

    // Seed the approved starter set. Safe defaults: risky features off.
    DEFAULT_FLAGS.forEach(define);

    GE.flags = {
        define: define,
        isEnabled: isEnabled,
        isDefined: isDefined,
        enable: enable,
        disable: disable,
        set: set,
        applyServer: applyServer,
        list: list,
        count: count,
        Events: { CHANGED: GE.eventNames.FLAGS_CHANGED },
        init: function () {
            GE.log.ns("flags").debug(count() + " flags registered");
            return true;
        },
        destroy: function () {
            userValues = {};
            serverValues = {};
            return true;
        },
    };
})(typeof window !== "undefined" ? window : globalThis);
