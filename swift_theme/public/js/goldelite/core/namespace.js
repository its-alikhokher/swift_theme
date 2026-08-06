/* GoldElite — core namespace.
   Creates the ONLY global: window.GoldElite. All subsystems attach here. */

(function (global) {
    "use strict";

    var STATES = {
        UNINITIALIZED: "uninitialized",
        INITIALIZING: "initializing",
        READY: "ready",
        DESTROYED: "destroyed",
    };

    var EVENT_NAMES = {
        LIFECYCLE_INIT: "ge:lifecycle:init",
        LIFECYCLE_READY: "ge:lifecycle:ready",
        LIFECYCLE_DESTROY: "ge:lifecycle:destroy",
        SETTINGS_CHANGED: "ge:settings:changed",
        FLAGS_CHANGED: "ge:flags:changed",
        ERROR_REPORTED: "ge:error:reported",
        LAYOUT_READY: "ge:layout:ready",
        LAYOUT_RESIZE: "ge:layout:resize",
        LAYOUT_REGION_ADDED: "ge:layout:region-added",
        LAYOUT_REGION_REMOVED: "ge:layout:region-removed",
        LAYOUT_CHANGED: "ge:layout:changed",
        COMPONENT_CREATED: "ge:component:created",
        COMPONENT_MOUNTED: "ge:component:mounted",
        COMPONENT_ENABLED: "ge:component:enabled",
        COMPONENT_DISABLED: "ge:component:disabled",
        COMPONENT_DESTROYED: "ge:component:destroyed",
        TOKENS_LOADED: "ge:tokens:loaded",
        TOKENS_CHANGED: "ge:tokens:changed",
        TOKENS_RESET: "ge:tokens:reset",
        TOKENS_VALIDATED: "ge:tokens:validated",
    };

    // Safe against duplicate inclusion: never re-create the namespace.
    if (global.GoldElite && global.GoldElite.version) {
        return;
    }

    var GE = global.GoldElite = {
        version: "0.1.0",
        states: STATES,
        eventNames: EVENT_NAMES,
        state: STATES.UNINITIALIZED,
    };

    Object.freeze(GE.states);
    Object.freeze(GE.eventNames);
})(typeof window !== "undefined" ? window : globalThis);
