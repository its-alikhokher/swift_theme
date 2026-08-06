/* GoldElite — compatibility layer (adapter architecture, Phase 2).
   Declares Frappe/ERPNext contracts as read-only probes. NO override
   implementations. Checks run on demand; nothing is modified. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var contracts = {};

    function defineContract(name, contract) {
        if (!name || typeof name !== "string") {
            throw new GE.error.Error(
                "Contract name must be a non-empty string",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (!contract || typeof contract !== "object") {
            throw new GE.error.Error(
                "Contract must be an object",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (contract.paths !== undefined && !Array.isArray(contract.paths)) {
            throw new GE.error.Error(
                "Contract paths must be an array",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        if (contract.probe !== undefined && typeof contract.probe !== "function") {
            throw new GE.error.Error(
                "Contract probe must be a function",
                GE.error.codes.INVALID_ARGUMENT,
                { name: name }
            );
        }
        contracts[name] = {
            name: name,
            paths: contract.paths || [],
            probe: contract.probe || null,
        };
        return true;
    }

    function checkOne(contract) {
        var missing = [];
        for (var i = 0; i < contract.paths.length; i++) {
            var path = contract.paths[i];
            if (util.getPath(global, path) === undefined) {
                missing.push(path);
            }
        }
        if (missing.length) {
            return { ok: false, missing: missing };
        }
        if (contract.probe) {
            var result;
            try {
                result = contract.probe();
            } catch (err) {
                return {
                    ok: false,
                    missing: missing,
                    detail: err && err.message ? err.message : String(err),
                };
            }
            if (result !== true) {
                return {
                    ok: false,
                    missing: missing,
                    detail: typeof result === "string" ? result : "probe returned a non-true value",
                };
            }
        }
        return { ok: true, missing: missing };
    }

    function check(name) {
        var contract = contracts[name];
        if (!contract) {
            return { ok: false, missing: [], detail: "unknown contract: " + name };
        }
        return checkOne(contract);
    }

    function isSupported(name) {
        return check(name).ok;
    }

    function require(names) {
        if (!Array.isArray(names)) {
            throw new GE.error.Error(
                "require() expects an array of contract names",
                GE.error.codes.INVALID_ARGUMENT,
                { names: names }
            );
        }
        var failed = [];
        for (var i = 0; i < names.length; i++) {
            if (!check(names[i]).ok) {
                failed.push(names[i]);
            }
        }
        return { ok: failed.length === 0, failed: failed };
    }

    function contractsList() {
        return Object.keys(contracts).sort();
    }

    function all() {
        return contractsList().map(function (name) {
            var result = check(name);
            return {
                name: name,
                ok: result.ok,
                missing: result.missing,
                detail: result.detail || null,
            };
        });
    }

    // Contract catalog (declarations only — no override implementations).
    defineContract("frappe.desktop", { paths: ["frappe", "frappe.boot", "frappe.app"] });
    defineContract("frappe.views", { paths: ["frappe.views", "frappe.views.Container"] });
    defineContract("frappe.keyboard", { paths: ["frappe.ui.keys", "frappe.ui.keys.add_shortcut"] });
    defineContract("frappe.form", { paths: ["frappe.ui.form", "frappe.ui.form.Form"] });
    defineContract("frappe.search", { paths: ["frappe.search"] });
    defineContract("erpnext.desktop", { paths: ["erpnext"] });

    GE.compat = {
        define: defineContract,
        check: check,
        isSupported: isSupported,
        require: require,
        contracts: contractsList,
        all: all,
        init: function () {
            GE.log.ns("compat").debug(contractsList().length + " contracts registered");
            return true;
        },
        destroy: function () {
            return true;
        },
    };
})(typeof window !== "undefined" ? window : globalThis);
