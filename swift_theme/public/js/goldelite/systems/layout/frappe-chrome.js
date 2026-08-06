/* GoldElite — Frappe chrome compatibility.
   Read-only probe + wrapper of the EXISTING Frappe layout. Never mutates,
   never re-parents, never hides elements. Wraps only. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var CHROME_SELECTORS = {
        navbar: "#navbar",
        sidebar: ".layout-side-section",
        content: ".main-section",
        body: "body",
    };

    function query(selector) {
        var doc = global.document;
        if (!doc || typeof doc.querySelector !== "function" || !selector) {
            return null;
        }
        return doc.querySelector(selector);
    }

    function rectOf(element) {
        if (!element || typeof element.getBoundingClientRect !== "function") {
            return null;
        }
        try {
            var rect = element.getBoundingClientRect();
            return {
                left: rect.left,
                top: rect.top,
                width: rect.width,
                height: rect.height,
            };
        } catch (err) {
            return null;
        }
    }

    function probe() {
        var found = {};
        Object.keys(CHROME_SELECTORS).forEach(function (name) {
            var element = query(CHROME_SELECTORS[name]);
            found[name] = element
                ? { present: true, rect: rectOf(element) }
                : { present: false, rect: null };
        });
        return found;
    }

    function describe() {
        var found = probe();
        var present = [];
        Object.keys(found).forEach(function (name) {
            if (found[name].present) {
                present.push(name);
            }
        });
        return {
            chrome: found,
            present: present,
            route: (global.document && global.document.body)
                ? global.document.body.getAttribute("data-route")
                : null,
        };
    }

    function wrap(selector) {
        if (!util.isString(selector) || !selector) {
            throw new GE.error.Error(
                "wrap() expects a selector",
                GE.error.codes.INVALID_ARGUMENT,
                { selector: selector }
            );
        }
        var element = query(selector);
        return {
            id: selector,
            element: element,
            present: !!element,
            rect: function () {
                return rectOf(this.element);
            },
            size: function () {
                var rect = rectOf(this.element);
                return rect ? { width: rect.width, height: rect.height } : null;
            },
            visible: function () {
                if (!this.element) {
                    return false;
                }
                var rect = rectOf(this.element);
                return !!rect && (rect.width > 0 || rect.height > 0);
            },
        };
    }

    GE.layout = GE.layout || {};
    GE.layout.chrome = {
        probe: probe,
        describe: describe,
        wrap: wrap,
    };
})(typeof window !== "undefined" ? window : globalThis);
