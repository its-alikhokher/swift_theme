/* GoldElite — layout context.
   Tracks viewport, desktop/mobile mode, sidebar/navbar/floating state and
   content bounds. Observes window resize (no CSS, no DOM writes). */

(function (global) {
    "use strict";

    var GE = global.GoldElite;
    var util = GE.util;

    var state = {
        viewport: { width: 0, height: 0 },
        mode: "desktop",
        sidebar: { visible: true, width: 0 },
        navbar: { visible: true, height: 0 },
        floating: [],
        content: { left: 0, top: 0, width: 0, height: 0 },
    };

    var observing = false;
    var removeResizeListener = null;

    function viewportSize() {
        var doc = global.document;
        var width = global.innerWidth;
        var height = global.innerHeight;
        if (!util.isNumber(width) && doc && doc.documentElement) {
            width = doc.documentElement.clientWidth;
        }
        if (!util.isNumber(height) && doc && doc.documentElement) {
            height = doc.documentElement.clientHeight;
        }
        return {
            width: util.isNumber(width) ? Math.round(width) : 0,
            height: util.isNumber(height) ? Math.round(height) : 0,
        };
    }

    function computeContent() {
        var sidebarWidth = state.sidebar.visible ? state.sidebar.width : 0;
        var navbarHeight = state.navbar.visible ? state.navbar.height : 0;
        return {
            left: sidebarWidth,
            top: navbarHeight,
            width: Math.max(0, state.viewport.width - sidebarWidth),
            height: Math.max(0, state.viewport.height - navbarHeight),
        };
    }

    function update() {
        var previousWidth = state.viewport.width;
        var previousHeight = state.viewport.height;
        state.viewport = viewportSize();
        state.mode = GE.layout.responsive.match(state.viewport.width);
        state.content = computeContent();
        var resized = previousWidth !== state.viewport.width
            || previousHeight !== state.viewport.height;
        if (resized) {
            GE.events.emit(GE.layout.Events.RESIZE, {
                viewport: util.clone(state.viewport),
                mode: state.mode,
            });
        }
        return true;
    }

    function onResize() {
        update();
        GE.events.emit(GE.layout.Events.CHANGED, { reason: "resize", state: get() });
    }

    var resizeHandler = util.debounce(onResize, 150);

    function observe() {
        if (observing) {
            return true;
        }
        if (!global.addEventListener) {
            return false;
        }
        global.addEventListener("resize", resizeHandler);
        removeResizeListener = function () {
            if (global.removeEventListener) {
                global.removeEventListener("resize", resizeHandler);
            }
        };
        observing = true;
        return true;
    }

    function stop() {
        if (!observing) {
            return false;
        }
        if (removeResizeListener) {
            removeResizeListener();
            removeResizeListener = null;
        }
        observing = false;
        return true;
    }

    function set(partial) {
        if (!util.isPlainObject(partial)) {
            throw new GE.error.Error(
                "Context set() expects an object",
                GE.error.codes.INVALID_ARGUMENT,
                { partial: partial }
            );
        }
        var previous = util.clone(state);
        util.assign(state.sidebar, partial.sidebar || {});
        util.assign(state.navbar, partial.navbar || {});
        if (partial.floating !== undefined) {
            if (!util.isArray(partial.floating)) {
                throw new GE.error.Error(
                    "Context floating must be an array",
                    GE.error.codes.INVALID_ARGUMENT,
                    { floating: partial.floating }
                );
            }
            state.floating = partial.floating.slice();
        }
        if (partial.viewport) {
            if (!util.isPlainObject(partial.viewport)) {
                throw new GE.error.Error(
                    "Context viewport must be an object",
                    GE.error.codes.INVALID_ARGUMENT,
                    { viewport: partial.viewport }
                );
            }
            util.assign(state.viewport, partial.viewport);
        }
        state.mode = GE.layout.responsive.match(state.viewport.width);
        state.content = computeContent();
        GE.events.emit(GE.layout.Events.CHANGED, { reason: "set", state: get() });
        return true;
    }

    function get(path) {
        if (path === undefined || path === null) {
            return util.clone(state);
        }
        var value = util.getPath(state, path, undefined);
        return value === undefined ? undefined : util.clone(value);
    }

    function reset() {
        state = {
            viewport: { width: 0, height: 0 },
            mode: "desktop",
            sidebar: { visible: true, width: 0 },
            navbar: { visible: true, height: 0 },
            floating: [],
            content: { left: 0, top: 0, width: 0, height: 0 },
        };
        return true;
    }

    GE.layout = GE.layout || {};
    GE.layout.context = {
        update: update,
        observe: observe,
        stop: stop,
        set: set,
        get: get,
        reset: reset,
    };
})(typeof window !== "undefined" ? window : globalThis);
