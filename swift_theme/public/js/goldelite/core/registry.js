/* GoldElite — registry primitives.
   GE.services is a registry instance with lazy singleton resolution and
   teardown support. The component manager lives in systems/components.js
   (GE.components is the full component runtime, not a raw registry). */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    function createRegistry(opts) {
        opts = opts || {};
        var kind = opts.kind || "item";
        var entries = {};

        function normalize(name, definition) {
            if (typeof definition === "function") {
                return {
                    name: name,
                    factory: definition,
                    deps: [],
                    singleton: true,
                    teardown: null,
                    built: false,
                    instance: null,
                };
            }
            if (!definition || typeof definition !== "object") {
                throw new GE.error.Error(
                    "Registry definition must be a function or an object",
                    GE.error.codes.INVALID_ARGUMENT,
                    { kind: kind, name: name }
                );
            }
            if (typeof definition.factory !== "function") {
                throw new GE.error.Error(
                    "Registry definition must provide a factory function",
                    GE.error.codes.INVALID_ARGUMENT,
                    { kind: kind, name: name }
                );
            }
            if (definition.deps !== undefined && !Array.isArray(definition.deps)) {
                throw new GE.error.Error(
                    "Registry deps must be an array",
                    GE.error.codes.INVALID_ARGUMENT,
                    { kind: kind, name: name }
                );
            }
            if (definition.destroy !== undefined && typeof definition.destroy !== "function") {
                throw new GE.error.Error(
                    "Registry destroy must be a function",
                    GE.error.codes.INVALID_ARGUMENT,
                    { kind: kind, name: name }
                );
            }
            return {
                name: name,
                factory: definition.factory,
                deps: definition.deps || [],
                singleton: definition.singleton !== false,
                teardown: definition.destroy || null,
                built: false,
                instance: null,
            };
        }

        function register(name, definition) {
            if (!name || typeof name !== "string") {
                throw new GE.error.Error(
                    "Registry name must be a non-empty string",
                    GE.error.codes.INVALID_ARGUMENT,
                    { kind: kind, name: name }
                );
            }
            if (entries[name]) {
                throw new GE.error.Error(
                    "Already registered: " + name,
                    GE.error.codes.ALREADY_REGISTERED,
                    { kind: kind, name: name }
                );
            }
            entries[name] = normalize(name, definition);
            return true;
        }

        function resolve(name) {
            var entry = entries[name];
            if (!entry) {
                throw new GE.error.Error(
                    "Not registered: " + name,
                    GE.error.codes.NOT_REGISTERED,
                    { kind: kind, name: name }
                );
            }
            if (entry.singleton && entry.built) {
                return entry.instance;
            }
            var deps = entry.deps.map(resolve);
            var instance = entry.factory({ GE: GE, name: name, kind: kind, deps: deps });
            if (entry.singleton) {
                entry.instance = instance;
                entry.built = true;
            }
            return instance;
        }

        function destroy(name) {
            var entry = entries[name];
            if (!entry) {
                return false;
            }
            if (entry.built && entry.teardown) {
                try {
                    entry.teardown(entry.instance, { GE: GE, name: name, kind: kind });
                } catch (err) {
                    GE.error.report(err, GE.error.codes.DESTROY_FAILED, { kind: kind, name: name });
                }
            }
            entry.instance = null;
            entry.built = false;
            return true;
        }

        function destroyAll() {
            Object.keys(entries).forEach(destroy);
            return true;
        }

        function has(name) {
            return !!entries[name];
        }

        function list() {
            return Object.keys(entries);
        }

        function size() {
            return Object.keys(entries).length;
        }

        function reset() {
            destroyAll();
            entries = {};
            return true;
        }

        return {
            register: register,
            resolve: resolve,
            destroy: destroy,
            destroyAll: destroyAll,
            has: has,
            list: list,
            size: size,
            reset: reset,
        };
    }

    GE.registry = {
        create: createRegistry,
    };

    GE.services = createRegistry({ kind: "service" });
    // GE.components is provided by systems/components.js (component runtime).
})(typeof window !== "undefined" ? window : globalThis);
