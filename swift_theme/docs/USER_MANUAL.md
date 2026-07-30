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

1. **Login** with your credentials (auto-fill enabled)
2. Go to **Swift Theme Settings** from the search bar
3. Select a **Preset Theme** or use **Gradient Mode**

### 3. Color Modes

#### Preset Mode (Recommended)
- Choose from 12 premium themes
- Auto dark/light mode detection
- Complete color palette included

#### Gradient Mode
- Select 2 colors (Start + End)
- System auto-detects if gradient is dark or light
- Applies to all views automatically

#### Manual Mode
- Set Primary and Secondary colors individually
- Full control over color scheme

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
- Sounds play on: Save, Submit, Cancel, Error, Login, Notification

### 6. UI Preferences

- **Density**: Compact, Comfortable, Spacious
- **Corner Radius**: None, Small, Medium, Large, Full
- **Font Scale**: 80% to 120%
- **Performance Mode**: Disables animations for speed

### 7. Views Coverage

All views are styled:
- ✅ List View (rows, filters, status pills)
- ✅ Report View (headers, zebra stripes, sticky columns)
- ✅ Kanban (columns, cards, drag preview)
- ✅ Dashboard (widgets, number cards, charts)
- ✅ Login Page (gradient background, glassmorphism)

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
