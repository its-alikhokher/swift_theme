# Swift Theme - User Manual

## Quick Start

### 1. Installation
```bash
bench get-app https://github.com/its-alikhokher/swift_theme
bench install-app swift_theme
bench migrate
bench build --app swift_theme
```

### 2. First Time Setup

1. **Login** with your credentials
2. Go to **Swift Theme Settings** from the search bar
3. Pick a **Theme Preset**, or choose **Custom Colors**

### 3. Color Modes

#### Theme Preset (Recommended)
- 12 presets named after Marvel characters — six light, six dark
- Each is a hand-tuned palette, not one colour tinting everything: the page,
  the cards and the accents are set separately
- Only the selected preset's stylesheet is loaded

#### Custom Colors
- Pick a **Primary** and a **Secondary** colour
- Choose **Custom Mode** — Light or Dark. Two hex codes cannot say which you
  want, and it used to be locked to dark
- Choose **Colour Strength** — *Subtle* keeps the cards neutral and puts the
  colour in the accents; *Bold* gives the cards the brand tone
- Everything else is worked out from your pair: canvas, cards, the text on each
  surface, muted text, borders and the accent states. If your colour is one
  where neither black nor white is quite legible on it, it is nudged a percent
  or two until it is

There is no third mode. A separate accent, a full-theme picker and a brand
override used to exist alongside these two and overlapped with them.

### 4. Sidebar Behavior

| Style | Description |
|-------|-------------|
| Floating | Sidebar with shadow, detached from edges |
| Attached | Traditional sidebar, flush with content |
| Minimal | Icon-only, expands on hover |

**Pin Behavior:**
- Click to Pin: Click pin icon to lock sidebar
- Hover to Expand: Sidebar opens on mouse hover
- Always Expanded: Sidebar stays open

### 5. Sound System

- Enable/Disable sounds globally
- Adjust volume (0-100%)
- Sounds play on: Save, Submit, Cancel, Error, Success, Notification

**The app ships no audio files.** Add a row to the **Sound Events** table for
each event you want, attach a file, and set its **Event Key** to one of:
`save`, `submit`, `cancel`, `delete`, `error`, `success`, `notification`,
`click`, `login`. Events with no file attached stay silent.

### 6. UI Preferences

- **Density**: Compact, Comfortable, Cozy
- **Corner Radius**: Sharp, Rounded, Pill
- **Font Scale**: S, M, L, XL
- **Performance Mode**: Disables animations for speed

### 7. Views Coverage

All views are styled:
- ✅ List View (rows, filters, status pills)
- ✅ Report View (headers, zebra stripes, sticky columns)
- ✅ Kanban (columns, cards, drag preview)
- ✅ Dashboard (widgets, number cards, charts)
- ✅ Login Page (themed from the active palette, three layouts)

### Troubleshooting

**Issue**: Migration error "Module import failed"
**Solution**: Run `bench clear-cache` then `bench migrate`

**Issue**: Sidebar dancing on hover
**Solution**: Already fixed in v2.0 - smooth transitions applied

**Issue**: Colors not applying
**Solution**: Clear browser cache, rebuild assets `bench build --app swift_theme`

---

**Author**: its-alikhokher  
**Email**: iamaliraza777@gmail.com  
**Version**: 2.0 (Frappe v16 Compatible)
