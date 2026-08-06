/* GoldElite — responsive service.
   Breakpoint detection with a stable API. No CSS implementation, no DOM writes. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var DEFAULT_BREAKPOINTS = {
        mobile: { max: 767 },
        tablet: { min: 768, max: 1023 },
        desktop: { min: 1024 },
    };

    var breakpoints = util.clone(DEFAULT_BREAKPOINTS);

    function registerDefaults() {
        breakpoints = util.clone(DEFAULT_BREAKPOINTS);
        return true;
    }

    function define(map) {
        if (!util.isPlainObject(map)) {
            throw new GE.error.Error(
                "Breakpoints must be an object of name -> {min,max}",
                GE.error.codes.INVALID_ARGUMENT,
                { breakpoints: map }
            );
        }
        var normalized = {};
        Object.keys(map).forEach(function (name) {
            var spec = map[name];
            if (!util.isPlainObject(spec)) {
                throw new GE.error.Error(
                    "Breakpoint spec must be an object",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, spec: spec }
                );
            }
            if (spec.min !== undefined && !util.isNumber(spec.min)) {
                throw new GE.error.Error(
                    "Breakpoint min must be a number",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, min: spec.min }
                );
            }
            if (spec.max !== undefined && !util.isNumber(spec.max)) {
                throw new GE.error.Error(
                    "Breakpoint max must be a number",
                    GE.error.codes.INVALID_ARGUMENT,
                    { name: name, max: spec.max }
                );
            }
            normalized[name] = { min: spec.min, max: spec.max };
        });
        breakpoints = normalized;
        return true;
    }

    function match(width) {
        if (!util.isNumber(width)) {
            throw new GE.error.Error(
                "match() expects a width in pixels",
                GE.error.codes.INVALID_ARGUMENT,
                { width: width }
            );
        }
        var matched = null;
        Object.keys(breakpoints).forEach(function (name) {
            var spec = breakpoints[name];
            var withinMin = spec.min === undefined || width >= spec.min;
            var withinMax = spec.max === undefined || width <= spec.max;
            if (withinMin && withinMax) {
                matched = name;
            }
        });
        return matched || "desktop";
    }

    function current() {
        var width = GE.layout && GE.layout.context
            ? GE.layout.context.get("viewport.width")
            : null;
        if (!util.isNumber(width)) {
            width = global.innerWidth;
        }
        if (!util.isNumber(width)) {
            width = 0;
        }
        return match(width);
    }

    function isBreakpoint(name) {
        return current() === name;
    }

    function isMobile() {
        return isBreakpoint("mobile");
    }

    function isTablet() {
        return isBreakpoint("tablet");
    }

    function isDesktop() {
        return isBreakpoint("desktop");
    }

    function isMax(name) {
        return !!breakpoints[name];
    }

    function list() {
        return Object.keys(breakpoints).sort();
    }

    GE.layout = GE.layout || {};
    GE.layout.responsive = {
        registerDefaults: registerDefaults,
        define: define,
        match: match,
        current: current,
        isBreakpoint: isBreakpoint,
        isMobile: isMobile,
        isTablet: isTablet,
        isDesktop: isDesktop,
        list: list,
    };
})(typeof window !== "undefined" ? window : globalThis);
