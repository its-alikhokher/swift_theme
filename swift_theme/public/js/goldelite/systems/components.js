/* GoldElite — component runtime (D-004).
   Single lifecycle manager for every GoldElite UI module.
   State machine: created -> mounted -> enabled <-> disabled, terminal destroyed.
   Idempotent operations, lazy creation, dependency-first resolution with
   circular rejection, shared context, typed events, error isolation, dev tools.
   No DOM work, no rendering. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;
    var log = GE.log.ns("components");

    var CREATED = "created";
    var MOUNTED = "mounted";
    var ENABLED = "enabled";
    var DISABLED = "disabled";
    var DESTROYED = "destroyed";

    var entries = {};
    var creationOrder = [];
    var initialized = false;
    var cycleStack = [];

    var EVENT = {
        CREATED: "ge:component:created",
        MOUNTED: "ge:component:mounted",
        ENABLED: "ge:component:enabled",
        DISABLED: "ge:component:disabled",
        DESTROYED: "ge:component:destroyed",
    };

    // Operation table: from-state -> next-state + which event to emit.
    // Idempotent states are safe no-ops; anything else is an invalid transition.
    var OP = {
        mount:   { from: [CREATED], next: MOUNTED,  emit: "mounted",  idempotentFrom: [MOUNTED, ENABLED, DISABLED] },
        unmount: { from: [MOUNTED, ENABLED, DISABLED], next: CREATED, emit: null, idempotentFrom: [CREATED] },
        enable:  { from: [MOUNTED, DISABLED], next: ENABLED, emit: "enabled", idempotentFrom: [ENABLED] },
        disable: { from: [ENABLED], next: DISABLED, emit: "disabled", idempotentFrom: [DISABLED] },
        update:  { from: [MOUNTED, ENABLED, DISABLED], next: null, emit: null, idempotentFrom: [] },
        destroy: { from: [CREATED, MOUNTED, ENABLED, DISABLED], next: DESTROYED, emit: "destroyed", idempotentFrom: [DESTROYED] },
    };

    // ------------------------------------------------------------------
    // Registration / definition
    // ------------------------------------------------------------------

    function normalizeDefinition(name, definition) {
        if (util.isFunction(definition)) {
            return { deps: [], create: definition, methods: {}, instance: null };
        }
        if (!util.isPlainObject(definition)) {
            throw new GE.error.Error(
                "Component definition must be a function or an object",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name, definition: definition }
            );
        }
        if (definition.deps !== undefined) {
            if (!util.isArray(definition.deps) || !definition.deps.every(util.isString)) {
                throw new GE.error.Error(
                    "Component deps must be an array of names",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, deps: definition.deps }
                );
            }
        }
        var hasFactory = typeof definition.create === "function";
        var hasInstanceLifecycle = ["mount", "update", "enable", "disable", "destroy"]
            .some(function (method) { return typeof definition[method] === "function"; });
        if (!hasFactory && !hasInstanceLifecycle) {
            throw new GE.error.Error(
                "Component must define create() or a lifecycle method",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        var methods = {};
        ["mount", "update", "enable", "disable", "destroy"].forEach(function (method) {
            if (definition[method] !== undefined && typeof definition[method] !== "function") {
                throw new GE.error.Error(
                    "Component " + method + " must be a function",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, method: method }
                );
            }
            methods[method] = definition[method] || null;
        });
        return {
            deps: (definition.deps || []).slice(),
            create: hasFactory ? definition.create : null,
            methods: methods,
            // pre-built instance registered directly (definition IS the instance)
            instance: hasFactory ? null : definition,
        };
    }

    function register(name, definition) {
        if (!util.isString(name) || !name) {
            throw new GE.error.Error(
                "Component name must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (entries[name]) {
            throw new GE.error.Error(
                "Component already registered: " + name,
                GE.error.codes.ALREADY_REGISTERED,
                { name: name }
            );
        }
        var normalized = normalizeDefinition(name, definition);
        entries[name] = {
            name: name,
            deps: normalized.deps,
            create: normalized.create,
            methods: normalized.methods,
            instance: normalized.instance,
            state: CREATED,
            ctx: null,
            failed: false,
            lastError: null,
            created: false,
        };
        log.debug("registered " + name);
        return true;
    }

    // ------------------------------------------------------------------
    // Shared context
    // ------------------------------------------------------------------

    function makeContext(name) {
        return {
            GE: GE,
            name: name,
            settings: GE.settings,
            layout: GE.layout,
            events: GE.events,
            flags: GE.flags,
            registry: GE.registry,
            services: GE.services,
            compat: GE.compat,
            tokens: GE.tokens,
            log: GE.log.ns("component:" + name),
        };
    }

    // ------------------------------------------------------------------
    // Lazy creation
    // ------------------------------------------------------------------

    function createEntry(entry) {
        if (entry.failed) {
            return null;
        }
        if (!entry.ctx) {
            entry.ctx = makeContext(entry.name);
        }
        if (entry.created) {
            return entry.instance;
        }
        if (!entry.create) {
            entry.created = true;
            entry.state = CREATED;
            creationOrder.push(entry.name);
            GE.events.emit(EVENT.CREATED, { name: entry.name, state: CREATED });
            return entry.instance;
        }
        try {
            var instance = entry.create(entry.ctx);
            if (!instance || typeof instance !== "object") {
                throw new GE.error.Error(
                    "Component create() must return an instance object",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: entry.name }
                );
            }
            entry.instance = instance;
            entry.created = true;
            entry.state = CREATED;
            creationOrder.push(entry.name);
            log.debug("created " + entry.name);
            GE.events.emit(EVENT.CREATED, { name: entry.name, state: CREATED });
            return instance;
        } catch (err) {
            entry.failed = true;
            entry.lastError = err;
            GE.error.report(err, GE.error.codes.INIT_FAILED, { component: entry.name, phase: "create" });
            return null;
        }
    }

    // ------------------------------------------------------------------
    // Dependency resolution (init-first, circular rejection)
    // ------------------------------------------------------------------

    function resolveName(entry, stack) {
        var name = entry.name;
        if (entry.created) {
            return true;
        }
        if (stack.indexOf(name) >= 0) {
            var cycle = stack.slice(stack.indexOf(name)).concat(name).join(" -> ");
            var err = new GE.error.Error(
                "Circular dependency detected: " + cycle,
                GE.error.codes.CIRCULAR_DEPENDENCY,
                { name: name, cycle: cycle }
            );
            GE.error.report(err, GE.error.codes.CIRCULAR_DEPENDENCY, { name: name });
            throw err;
        }
        stack.push(name);
        for (var i = 0; i < entry.deps.length; i++) {
            var dep = entries[entry.deps[i]];
            if (!dep) {
                var missing = new GE.error.Error(
                    "Unknown dependency: " + entry.deps[i],
                    GE.error.codes.NOT_REGISTERED,
                    { name: name, dep: entry.deps[i] }
                );
                GE.error.report(missing, GE.error.codes.NOT_REGISTERED, { name: name });
                throw missing;
            }
            resolveName(dep, stack);
        }
        stack.pop();
        return true;
    }

    function resolve(name) {
        var entry = entryOrThrow(name);
        resolveName(entry, []);
        createEntry(entry);
        return entry.instance || null;
    }

    // ------------------------------------------------------------------
    // Hook runner (error isolation)
    // ------------------------------------------------------------------

    function invoke(entry, phase, payload) {
        var fn = entry.methods[phase];
        if (typeof fn !== "function" || !entry.instance) {
            return true;
        }
        try {
            fn.call(entry.instance, entry.ctx, payload);
        } catch (err) {
            entry.failed = true;
            entry.lastError = err;
            GE.error.report(err, GE.error.codes.UNKNOWN, { component: entry.name, phase: phase });
            return false;
        }
        return true;
    }

    function emitLifecycle(entry, stateName) {
        var eventKey = {
            created: EVENT.CREATED,
            mounted: EVENT.MOUNTED,
            enabled: EVENT.ENABLED,
            disabled: EVENT.DISABLED,
            destroyed: EVENT.DESTROYED,
        }[stateName];
        if (eventKey) {
            GE.events.emit(eventKey, { name: entry.name, state: stateName });
        }
    }

    function runDeps(entry, phase) {
        for (var i = 0; i < entry.deps.length; i++) {
            var dep = entries[entry.deps[i]];
            if (!dep) {
                return false;
            }
            if (runOperation(dep, phase) !== true) {
                return false;
            }
        }
        return true;
    }

    // ------------------------------------------------------------------
    // State machine (idempotent, invalid transitions rejected)
    // ------------------------------------------------------------------

    function runOperation(entry, phase, payload) {
        var spec = OP[phase];
        if (spec.idempotentFrom.indexOf(entry.state) >= 0) {
            return true; // safe no-op
        }
        if (spec.from.indexOf(entry.state) < 0) {
            return false; // invalid transition rejected
        }
        // Dependencies initialize first (mount/enable propagate to deps).
        if (phase === "mount" || phase === "enable") {
            if (cycleStack.indexOf(entry.name) >= 0) {
                var cycle = cycleStack.slice(cycleStack.indexOf(entry.name)).concat(entry.name).join(" -> ");
                var err = new GE.error.Error(
                    "Circular dependency detected: " + cycle,
                    GE.error.codes.CIRCULAR_DEPENDENCY,
                    { name: entry.name, cycle: cycle }
                );
                GE.error.report(err, GE.error.codes.CIRCULAR_DEPENDENCY, { name: entry.name });
                return false;
            }
            cycleStack.push(entry.name);
            var ok = runDeps(entry, phase);
            cycleStack.pop();
            if (!ok) {
                return false;
            }
        }
        // Lazy instantiation on mount.
        if (phase === "mount" && !createEntry(entry)) {
            return false;
        }
        if (!invoke(entry, phase, payload)) {
            return false;
        }
        if (spec.next) {
            setState(entry, spec.next);
            emitLifecycle(entry, spec.emit);
        }
        log.debug(entry.name + " -> " + entry.state);
        return true;
    }

    function setState(entry, state) {
        entry.state = state;
    }

    function entryOrThrow(name) {
        var entry = entries[name];
        if (!entry) {
            throw new GE.error.Error(
                "Unknown component: " + name,
                GE.error.codes.NOT_REGISTERED,
                { name: name }
            );
        }
        return entry;
    }

    // ------------------------------------------------------------------
    // Manager API
    // ------------------------------------------------------------------

    function mount(name) {
        return runOperation(entryOrThrow(name), "mount") === true;
    }

    function unmount(name) {
        return runOperation(entryOrThrow(name), "unmount") === true;
    }

    function enable(name) {
        return runOperation(entryOrThrow(name), "enable") === true;
    }

    function disable(name) {
        return runOperation(entryOrThrow(name), "disable") === true;
    }

    function update(name, payload) {
        return runOperation(entryOrThrow(name), "update", payload) === true;
    }

    function destroy(name) {
        return runOperation(entryOrThrow(name), "destroy") === true;
    }

    function destroyAll() {
        Object.keys(entries).forEach(destroy);
        return true;
    }

    function unregister(name) {
        var entry = entries[name];
        if (!entry) {
            return false;
        }
        destroy(name);
        delete entries[name];
        return true;
    }

    function has(name) {
        return !!entries[name];
    }

    function get(name) {
        var entry = entries[name];
        return entry ? entry.instance : null;
    }

    function state(name) {
        var entry = entries[name];
        return entry ? entry.state : null;
    }

    function list() {
        return Object.keys(entries).sort();
    }

    function size() {
        return Object.keys(entries).length;
    }

    // ------------------------------------------------------------------
    // Dev tools
    // ------------------------------------------------------------------

    function inspect(name) {
        var entry = entries[name];
        if (!entry) {
            return null;
        }
        var mountedState = entry.state === MOUNTED || entry.state === ENABLED || entry.state === DISABLED;
        return {
            name: entry.name,
            deps: entry.deps.slice(),
            state: entry.state,
            mounted: mountedState,
            enabled: entry.state === ENABLED,
            instance: !!entry.instance,
            created: entry.created,
            failed: entry.failed,
            lastError: entry.lastError ? entry.lastError.message : null,
            createdIndex: entry.created ? creationOrder.indexOf(entry.name) : -1,
        };
    }

    function health() {
        var names = Object.keys(entries);
        var report = names.map(function (name) {
            return inspect(name);
        });
        report.ok = report.every(function (item) { return !item.failed; });
        return report;
    }

    function order() {
        return creationOrder.slice();
    }

    // ------------------------------------------------------------------
    // Lifecycle integration
    // ------------------------------------------------------------------

    function init() {
        if (initialized) {
            return false;
        }
        initialized = true;
        log.debug("component runtime ready");
        return true;
    }

    function destroyRuntime() {
        if (!initialized) {
            return false;
        }
        destroyAll();
        creationOrder = [];
        entries = {};
        initialized = false;
        return true;
    }

    GE.components = {
        register: register,
        unregister: unregister,
        resolve: resolve,
        get: get,
        has: has,
        mount: mount,
        unmount: unmount,
        enable: enable,
        disable: disable,
        update: update,
        destroy: destroy,
        destroyAll: destroyAll,
        shutdown: destroyRuntime,
        state: state,
        list: list,
        size: size,
        inspect: inspect,
        health: health,
        order: order,
        Events: EVENT,
        init: init,
    };
})(typeof window !== "undefined" ? window : globalThis);
