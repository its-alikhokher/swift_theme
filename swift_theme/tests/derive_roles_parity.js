/* Runs the JS derivation and prints its output as JSON.

   The same maths exists in Python (scripts/colour.derive_roles) and in
   swift-boot.js, because the Settings preview must react to a colour picker
   without a round trip. Duplicated logic drifts, so a Python test runs this
   file over the same inputs and compares hex for hex.

   Usage:  node derive_roles_parity.js '<json array of [primary,secondary,mode,strength]>'
*/

const fs = require("fs");
const path = require("path");
const vm = require("vm");

function stubDom() {
    const el = {
        _attrs: {},
        style: {
            _p: {},
            setProperty(k, v) { this._p[k] = v; },
            removeProperty(k) { delete this._p[k]; },
            getPropertyValue(k) { return this._p[k]; },
        },
        setAttribute(k, v) { this._attrs[k] = String(v); },
        getAttribute(k) { return k in this._attrs ? this._attrs[k] : null; },
        removeAttribute(k) { delete this._attrs[k]; },
        appendChild(c) { return c; },
        remove() {},
        addEventListener() {},
    };
    return {
        documentElement: el,
        head: el,
        body: el,
        readyState: "complete",
        createElement: () => Object.assign({}, el, { style: { _p: {}, setProperty() {}, removeProperty() {} } }),
        getElementById: () => null,
        querySelector: () => null,
        addEventListener() {},
        dispatchEvent: () => true,
    };
}

const store = {};
const sandbox = {
    document: stubDom(),
    window: {},
    localStorage: {
        getItem: (k) => (k in store ? store[k] : null),
        setItem: (k, v) => { store[k] = String(v); },
        removeItem: (k) => { delete store[k]; },
    },
    CustomEvent: function (t, i) { return { type: t, detail: i && i.detail }; },
    console, setTimeout, Date,
};
sandbox.window.document = sandbox.document;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

const boot = path.join(__dirname, "..", "public", "js", "swift-boot.js");
vm.runInContext(fs.readFileSync(boot, "utf8"), sandbox);

const cases = JSON.parse(process.argv[2] || "[]");
const out = cases.map(([primary, secondary, mode, strength]) =>
    sandbox.window.SwiftTheme.deriveRoles(primary, secondary, mode, strength));
process.stdout.write(JSON.stringify(out));
