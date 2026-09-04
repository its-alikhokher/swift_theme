/* Swift Theme — desk scripts, bundled.
   =========================================================================
   Order matters as much as it does for the stylesheets: swift-boot.js has to
   run first and synchronously, because it writes the theme attributes onto
   <html> before Frappe paints. Everything after it builds on what it set up.

   Bundled for the same reason as the CSS: a raw /assets path carries no
   content hash, so the browser and nginx kept serving the previous release's
   scripts and a shipped fix never arrived. This name does get a hash.
   ========================================================================= */

import "./swift-boot.js";
import "./swift-mode-observer.js";
// The navbar chip and its palette are gone (Ali, 2026-08-28): theming is
// offered through Frappe's own Toggle Theme dialog, which swift-theme-dialog.js
// extends with the presets. Enable Theme Switcher still gates that section.
import "./swift-theme-dialog.js";
import "./swift-palette.js";
import "./swift-calendar.js";
import "./swift-orgchart.js";
import "./swift-sidebar.js";
import "./swift-focus.js";
import "./swift-perf.js";
import "./swift-sounds.js";
