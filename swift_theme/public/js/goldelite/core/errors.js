/* GoldElite — central error handling. Typed codes, reporters, graceful failures. */

(function (global) {
    "use strict";

    var GE = global.GoldElite;

    var CODES = {
        UNKNOWN: "GE_ERR_UNKNOWN",
        INVALID_ARGUMENT: "GE_ERR_INVALID_ARGUMENT",
        INVALID_SETTING: "GE_ERR_INVALID_SETTING",
        UNKNOWN_SETTING: "GE_ERR_UNKNOWN_SETTING",
        INVALID_FLAG: "GE_ERR_INVALID_FLAG",
        UNKNOWN_FLAG: "GE_ERR_UNKNOWN_FLAG",
        ALREADY_REGISTERED: "GE_ERR_ALREADY_REGISTERED",
        NOT_REGISTERED: "GE_ERR_NOT_REGISTERED",
        EVENT_UNDEFINED: "GE_ERR_EVENT_UNDEFINED",
        NOT_FOUND: "GE_ERR_NOT_FOUND",
        CIRCULAR_DEPENDENCY: "GE_ERR_CIRCULAR_DEPENDENCY",
        INVALID_TOKEN: "GE_ERR_INVALID_TOKEN",
        UNKNOWN_TOKEN: "GE_ERR_UNKNOWN_TOKEN",
        IMMUTABLE_TOKEN: "GE_ERR_IMMUTABLE_TOKEN",
        TOKEN_CYCLE: "GE_ERR_TOKEN_CYCLE",
        CONTRACT_FAILED: "GE_ERR_CONTRACT_FAILED",
        INIT_FAILED: "GE_ERR_INIT_FAILED",
        DESTROY_FAILED: "GE_ERR_DESTROY_FAILED",
    };

    function GoldEliteError(message, code, context) {
        this.message = message || "Unknown GoldElite error";
        this.name = "GoldEliteError";
        this.code = code || CODES.UNKNOWN;
        this.context = context || null;
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, GoldEliteError);
        }
    }
    GoldEliteError.prototype = Object.create(Error.prototype);
    GoldEliteError.prototype.constructor = GoldEliteError;

    var reporters = [];

    function toError(input, code, context) {
        if (input instanceof GoldEliteError) {
            return input;
        }
        var wrapped = new GoldEliteError(
            input && input.message ? input.message : String(input),
            code || CODES.UNKNOWN,
            context
        );
        if (input instanceof Error) {
            wrapped.cause = input;
        }
        return wrapped;
    }

    function report(input, code, context) {
        var err = toError(input, code, context);
        GE.log.error(err.message + (err.code ? " [" + err.code + "]" : ""));
        if (GE.events && GE.events.emit) {
            try {
                GE.events.emit(GE.eventNames.ERROR_REPORTED, { error: err });
            } catch (ignored) {}
        }
        for (var i = 0; i < reporters.length; i++) {
            try {
                reporters[i](err);
            } catch (ignored) {}
        }
        return err;
    }

    function onReport(fn) {
        if (typeof fn !== "function") {
            throw new GoldEliteError("onReport expects a function", CODES.INVALID_ARGUMENT);
        }
        reporters.push(fn);
        return function remove() {
            var index = reporters.indexOf(fn);
            if (index > -1) {
                reporters.splice(index, 1);
            }
        };
    }

    function attempt(fn, fallback, context) {
        try {
            return fn();
        } catch (err) {
            report(err, CODES.UNKNOWN, context);
            return fallback;
        }
    }

    function guard(fn, context) {
        return function () {
            try {
                return fn.apply(this, arguments);
            } catch (err) {
                report(err, CODES.UNKNOWN, context);
            }
        };
    }

    GE.error = {
        Error: GoldEliteError,
        codes: CODES,
        report: report,
        onReport: onReport,
        try: attempt,
        guard: guard,
    };
})(typeof window !== "undefined" ? window : globalThis);
