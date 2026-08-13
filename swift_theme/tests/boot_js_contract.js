/* Executes swift-boot.js against a minimal DOM stub.

   The Python suite can only assert that the server sends the right values; it
   cannot see whether the browser does anything with them. This runs the real
   file and checks the two things the CSS depends on: the data-swift-* attributes
   on <html>, and the single theme <link> being swapped rather than stacked.

   Run directly with `node`, or via the Python test that shells out to it. */

const fs = require("fs");
const vm = require("vm");

function makeElement(tag) {
    return {
        tagName: (tag || "").toUpperCase(),
        id: "",
        rel: "",
        _attrs: {},
        style: {
            _props: {},
            setProperty(k, v) { this._props[k] = v; },
            removeProperty(k) { delete this._props[k]; },
            getPropertyValue(k) { return this._props[k]; },
        },
        setAttribute(k, v) { this._attrs[k] = String(v); if (k === "href") this.href = String(v); },
        getAttribute(k) { return k in this._attrs ? this._attrs[k] : null; },
        removeAttribute(k) { delete this._attrs[k]; },
        appendChild(c) { (this.children = this.children || []).push(c); return c; },
        remove() { removed.push(this); },
        addEventListener() {},
        querySelector() { return null; },
    };
}

let removed = [];
const html = makeElement("html");
const head = makeElement("head");
const body = makeElement("body");

const store = {};
const document = {
    documentElement: html,
    head,
    body,
    readyState: "complete",
    createElement: makeElement,
    getElementById(id) {
        return (head.children || []).find((c) => c.id === id && !removed.includes(c)) || null;
    },
    querySelector() { return null; },
    addEventListener() {},
    dispatchEvent() { return true; },
};

const sandbox = {
    document,
    window: { frappe: undefined },
    localStorage: {
        getItem: (k) => (k in store ? store[k] : null),
        setItem: (k, v) => { store[k] = String(v); },
        removeItem: (k) => { delete store[k]; },
    },
    CustomEvent: function (type, init) { return { type, detail: init && init.detail }; },
    console,
    setTimeout,
    Date,
};
sandbox.window.document = document;
sandbox.window.localStorage = sandbox.localStorage;
sandbox.globalThis = sandbox;

vm.createContext(sandbox);
const bootPath = process.argv[2] ||
    require("path").join(__dirname, "..", "public", "js", "swift-boot.js");
const src = fs.readFileSync(bootPath, "utf8");
vm.runInContext(src, sandbox);

const API = sandbox.window.SwiftTheme;
const themeLink = () => document.getElementById("swift-theme-css");
const linkCount = () => (head.children || []).filter(
    (c) => c.id === "swift-theme-css" && !removed.includes(c)).length;

let pass = 0, fail = 0;
function check(label, cond, detail) {
    if (cond) { pass++; console.log("  PASS  " + label); }
    else { fail++; console.log("  FAIL  " + label + (detail ? "  -> " + detail : "")); }
}

console.log("\n== 1. Apply a preset (what saving Settings triggers) ==");
API.applyPrefs({
    preset: "ocean-depth",
    primary: "#06b6d4",
    secondary: "#0891b2",
    theme_css: "/assets/swift_theme/css/themes/ocean-depth.css",
    density: "Comfortable",
});
check("data-swift-preset set on <html>",
    html.getAttribute("data-swift-preset") === "ocean-depth", html.getAttribute("data-swift-preset"));
check("data-swift-themed set (drives the shared desk CSS)",
    html.getAttribute("data-swift-themed") !== null);
check("stylesheet <link> created with the preset href",
    themeLink() && themeLink().getAttribute("href") === "/assets/swift_theme/css/themes/ocean-depth.css",
    themeLink() && themeLink().getAttribute("href"));
check("link rel is stylesheet", themeLink() && themeLink().rel === "stylesheet");

console.log("\n== 2. Switch to another preset ==");
API.applyPrefs({
    preset: "crimson-red",
    primary: "#ef4444",
    secondary: "#dc2626",
    theme_css: "/assets/swift_theme/css/themes/crimson-red.css",
});
check("href retargeted to the new preset",
    themeLink() && themeLink().getAttribute("href") === "/assets/swift_theme/css/themes/crimson-red.css",
    themeLink() && themeLink().getAttribute("href"));
check("still exactly ONE stylesheet link (no stacking)", linkCount() === 1, "count=" + linkCount());

console.log("\n== 3. Switch to Custom Colors ==");
API.applyPrefs({ preset: null, primary: "#7C3AED", secondary: "#DB2777", theme_css: null });
check("preset attribute cleared", html.getAttribute("data-swift-preset") === null);
check("preset stylesheet removed", themeLink() === null);
check("--swift-primary set inline", html.style.getPropertyValue("--swift-primary") === "#7C3AED");
check("--swift-secondary set inline", html.style.getPropertyValue("--swift-secondary") === "#DB2777");
check("--swift-accent aliased to primary",
    html.style.getPropertyValue("--swift-accent") === "#7C3AED");
check("data-swift-themed still set for custom mode",
    html.getAttribute("data-swift-themed") !== null);

console.log("\n== 4. Back to a preset: inline vars must not shadow the stylesheet ==");
API.applyPrefs({
    preset: "swift-blue", primary: "#0b84f3", secondary: "#0056b3",
    theme_css: "/assets/swift_theme/css/themes/swift-blue.css",
});
check("inline --swift-primary cleared",
    html.style.getPropertyValue("--swift-primary") === undefined);
check("inline --swift-accent cleared",
    html.style.getPropertyValue("--swift-accent") === undefined);
check("stylesheet back", themeLink() && themeLink().getAttribute("href").endsWith("swift-blue.css"));

console.log("\n== 5. Persistence for the next page load (no flash) ==");
check("preset stored in localStorage", store["swift_preset"] === "swift-blue", store["swift_preset"]);
check("theme css url stored", (store["swift_theme_css"] || "").endsWith("swift-blue.css"));

console.log("\n== 6. Other preferences still applied ==");
API.applyPrefs({ density: "Compact", radius: "Pill", pin_behavior: "Hover to Expand" });
check("density attribute", html.getAttribute("data-swift-density") === "Compact");
check("radius attribute", html.getAttribute("data-swift-radius") === "Pill");
check("pin behaviour mapped to its CSS token",
    html.getAttribute("data-swift-pin") === "hover", html.getAttribute("data-swift-pin"));

console.log("\n" + "=".repeat(46));
console.log(`  ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
