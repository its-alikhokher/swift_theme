# Swift Theme — Shortcuts Reference

Phase 1. Frappe v16 keyboard shortcuts (`frappe.public/js/frappe/ui/keyboard.js`).

## API

| Method | Notes |
|--------|-------|
| `frappe.ui.keys.add_shortcut({shortcut, description, action, page})` | register; `page` restricts scope |
| `frappe.ui.keys.on/off(shortcut, fn)` | bind/unbind handlers |
| `frappe.ui.keys.setup()` | binds document keydown → `handlers[key]` |
| `frappe.ui.keys.show_keyboard_shortcut_dialog()` | help dialog (Ctrl+F1) |
| `frappe.ui.keys.get_shortcuts(page)` | list for help dialog |
| `frappe.ui.keys.standard_shortcuts` | built-in list (registered at ~line 188-237) |

## Frappe standard shortcuts

`shift+ctrl+g` (theme switcher, desk.js:94), `shift+ctrl+p` (command palette / page search),
`ctrl+g` (goto search), `ctrl+shift+h`? (help), `ctrl+shift+i`? (page info / debugger),
`ctrl+shift+d` (developer tools), `alt+b`? (Swift sidebar toggle), `ctrl+f` (in list),
`ctrl+d` (duplicate in list), `enter` (open row), `escape` (close dialogs) — exact list from
`keyboard.js` `standard_shortcuts`.

## Swift shortcuts

Registered in `swift-shortcuts.js` with `frappe.ui.keys.add_shortcut` + documented in
`SHORTCUTS.md`? (current Swift uses own handler; MUST use `frappe.ui.keys.add_shortcut` for
global ones to appear in Ctrl+F1 dialog). Swift keys: `Alt+B` sidebar toggle, `Alt+P` palette,
`Alt+M` mode badge cycle, `Alt+Shift+?`? show Swift help.

## Notes / risks

- Use `frappe.ui.keys.add_shortcut` (registered dialog-visible) not raw keydown where possible.
- Shortcuts must not collide: check `keyboard.js::standard_shortcuts` before choosing.
- `page` scoping: list/form pages each add their own keys.
