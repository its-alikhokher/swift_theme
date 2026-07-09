# Swift Theme for Frappe v16

A fast, modern, multi-scheme theme app for **Frappe / ERPNext v16**.
Covers the **Desk**, **public website / portal**, and **login page**.

## Features

- 7 color schemes — Swift Light, Swift Dark, Ocean Blue, Nord, Dracula, Solarized, Forest
- Per-user theme selector (added on the standard User form)
- Navbar theme switcher chip with palette popover
- Global CSS variables map to Frappe v16 tokens (no widget-by-widget overrides)
- Custom fonts: Inter, Poppins, Manrope, Roboto, System
- Performance mode: `content-visibility`, font preload, lazy images, reduced motion
- Sidebar collapse mode + splash screen for portal
- Custom login page with gradient hero background

## Requirements

- Frappe framework v16.x
- Python 3.10+
- A running bench

## Install

```bash
# Move into your bench
cd /path/to/frappe-bench

# 1. Copy or unzip this app into apps/
unzip swift_theme.zip -d apps/

# 2. Register the app with your bench
bench --site your-site.local install-app swift_theme

# 3. Build assets and restart
bench build --app swift_theme
bench --site your-site.local migrate
bench restart
```

## Usage

1. Log in as **System Manager**.
2. Open **Swift Theme Settings** to set the default scheme, font, and performance options.
3. Each user can pick their own scheme from:
   - Navbar chip (top-right) — instant switch.
   - Their **User** form (field: *Swift Theme*).

Preference precedence: **User** > **Swift Theme Settings default** > `swift-light`.

## Color schemes

| Key            | Type  | Primary   |
|----------------|-------|-----------|
| `swift-light`  | Light | `#4f46e5` |
| `swift-dark`   | Dark  | `#7c7cff` |
| `ocean-blue`   | Light | `#0369a1` |
| `nord`         | Dark  | `#88c0d0` |
| `dracula`      | Dark  | `#bd93f9` |
| `solarized`    | Light | `#268bd2` |
| `forest`       | Light | `#2f7d3a` |

Add your own by extending `swift_theme/public/css/swift-core.css` and appending
the key to `Swift Theme Settings > default_scheme` options and
`swift_theme/api/boot.py::_list_schemes`.

## Performance mode

When enabled (default), Swift Theme:

- Sets `content-visibility: auto` on list rows and cards for cheaper rendering
- Preloads Inter variable font
- Adds `loading="lazy"` and `decoding="async"` on images
- Promotes scrollable panels to their own compositor layer
- Honors `prefers-reduced-motion`

Toggle off from **Swift Theme Settings > Enable Performance Mode** or via the
navbar palette.

## Uninstall

```bash
bench --site your-site.local uninstall-app swift_theme
bench --site your-site.local migrate
```

## License

MIT — © MuleRun
