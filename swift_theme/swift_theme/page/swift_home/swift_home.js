// Copyright (c) 2026, Ali Raza and contributors
// For license information, please see license.txt

/**
 * Swift home — the desk landing page.
 *
 * The apps grid is drawn from `frappe.boot.desktop_icons`, which Frappe has
 * already filtered three ways: by app permission, by whether the workspace
 * behind the icon has any item this user can open, and by any roles set on the
 * icon itself. The figures come from Number Cards, whose values are counted
 * through `frappe.get_list`, so a User Permission on Company narrows them
 * without this page knowing such a thing exists.
 *
 * Nothing here decides what a user may see. Anything that appears is something
 * they could already reach from the sidebar.
 */

frappe.pages["swift-home"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Home"),
		single_column: true,
	});
	// Handed to the page object so the rendering can be driven from a test:
	// the trend beside a figure only appears when a card has a previous period
	// to compare against, which a fresh site does not.
	frappe.pages["swift-home"].__swift = new SwiftHome(page);
};

/* The landing page stands on its own: the grid is the navigation, so the
   sidebar beside it would be the same destinations twice. The top bar stays
   exactly as it is, and every page reached from a tile opens the ordinary way,
   sidebar and all - only this one page goes without.

   It is done with a body class rather than by touching the sidebar itself. The
   sidebar is global and shared, so anything done to it here would have to be
   undone on every route out of this page; a class is one flag, and the router
   clears it. */
frappe.pages["swift-home"].on_page_show = function () {
	document.body.classList.add("swift-home-open");
};

if (frappe.router && frappe.router.on && !frappe.router.__swift_home_hook) {
	frappe.router.__swift_home_hook = true;
	frappe.router.on("change", () => {
		const route = frappe.get_route() || [];
		// The landing carries an EMPTY route segment - [""] - not the page name,
		// because Frappe resolves "" through boot.home_page. Matching on the
		// name alone stripped the class the moment the router announced the very
		// route that had just shown the page. And the empty route only counts as
		// home when home is actually ours: with the setting off it means the
		// workspace, and the sidebar has to stay.
		const first = (route[0] || "").trim();
		const is_home =
			(!first && frappe.boot && frappe.boot.home_page === "swift-home") ||
			first === "swift-home";
		document.body.classList.toggle("swift-home-open", is_home);
	});
}

/* The hues the mock-ups use across the grid, in their order. Chips are picked
   from here rather than from the theme accent so the grid reads as a set of
   distinct apps, which is the whole point of the picture. */
const TILE_COLORS = [
	"#4b5563", "#ec4899", "#0ea5e9", "#4f46e5", "#f59e0b", "#3b82f6",
	"#2563eb", "#8b5cf6", "#10b981", "#6366f1", "#0891b2", "#14b8a6",
];

class SwiftHome {
	constructor(page) {
		this.page = page;
		this.$body = $('<div class="swift-home">').appendTo(page.main);
		this.render_shell();
		this.load();
	}

	/* One shell for every design.
	   The eight designs differ in what they show and where it sits, not in what
	   the page is made of - so the markup is built once and CSS decides which
	   blocks appear and how they are laid out. A design cannot therefore reach a
	   state another design cannot render, and switching one is a repaint rather
	   than a rebuild. */
	render_shell() {
		this.$body.html(`
			<div class="swift-home-topbar">
				<div class="swift-home-brand"></div>
				<button class="swift-home-search" type="button">
					${frappe.utils.icon("search", "sm")}
					<span class="swift-home-search-text">${__("Search or type a command")}</span>
					<span class="swift-home-kbd">${frappe.utils.is_mac() ? "⌘K" : "Ctrl + K"}</span>
				</button>
				<div class="swift-home-topbar-actions"></div>
			</div>
			<div class="swift-home-hero"></div>
			<div class="swift-home-head">
				<div class="swift-home-greet"></div>
				<div class="swift-home-shortcuts"></div>
			</div>
			<div class="swift-home-cards"></div>
			<div class="swift-home-section"></div>
			<div class="swift-home-apps"></div>
		`);
		this.$topbar = this.$body.find(".swift-home-topbar");
		this.$hero = this.$body.find(".swift-home-hero");
		this.$greet = this.$body.find(".swift-home-greet");
		this.$shortcuts = this.$body.find(".swift-home-shortcuts");
		this.$cards = this.$body.find(".swift-home-cards");
		this.$section = this.$body.find(".swift-home-section");
		this.$apps = this.$body.find(".swift-home-apps");
	}

	/* The top bar the mock-ups draw.
	   Every control on it is the desk's own, reached the way the desk reaches
	   it - nothing here is a second implementation of search, notifications or
	   the user menu, because a second implementation is a second set of
	   permission rules to keep in step.

	   The sidebar is hidden on this page but still in the DOM and still wired,
	   and the search it owns opens a modal attached to <body>. So the search box
	   here forwards the click to that button and Frappe's own command palette
	   opens, with its own results and its own permission filtering. */
	render_topbar() {
		const brand = frappe.utils.escape_html(this.cfg.brand_name || "");
		const logo = this.cfg.brand_logo;
		this.$body.find(".swift-home-brand").html(
			(logo
				? `<img class="swift-home-brand-logo" src="${frappe.utils.escape_html(logo)}" alt="">`
				: `<span class="swift-home-brand-mark">${frappe.utils.escape_html(
						(brand || "F").charAt(0).toUpperCase()
				  )}</span>`) + `<span class="swift-home-brand-name">${brand}</span>`
		);

		this.$body.find(".swift-home-search").on("click", () => this.open_search());

		const $actions = this.$body.find(".swift-home-topbar-actions");

		this.render_desk_actions($actions);

		// The bell IS the sidebar's bell. Not a copy of it, and not the same
		// panel moved somewhere else either: clicking here forwards the click
		// to Frappe's own `.sidebar-notification` button, so Frappe opens,
		// fills and closes its panel exactly as it does everywhere else.
		//
		// Moving the panel under our bell was tried and it fought the desk:
		// Frappe's own document handler closes the panel for any click that is
		// not inside `.standard-items-sections .sidebar-notification`, which a
		// borrowed panel and a foreign bell never are - it opened and shut in
		// the same gesture, and its contents never built. Only the panel's
		// position is ours now; see swift-home.css.
		const $bell = $(`
			<button class="swift-home-icon-btn swift-home-bell" type="button" aria-label="${__(
				"Notifications"
			)}">
				${frappe.utils.icon("notification", "md")}
				<span class="swift-home-bell-count"></span>
			</button>
		`).appendTo($actions);
		$bell.on("click", (e) => {
			// Our click must not reach the document: Frappe closes the panel
			// for any document click whose target is not its own bell, so the
			// forwarded click would open it and this one would shut it again in
			// the same gesture. The synthetic click below does reach it, with
			// Frappe's own button as the target, which is what it looks for.
			e.stopPropagation();
			const own = document.querySelector(".body-sidebar .sidebar-notification");
			if (own) own.click();
			else frappe.set_route("List", "Notification Log");
		});
		this.paint_unread();
		frappe.realtime.on("notification", () => this.paint_unread());

		const $avatar = $(
			`<button class="swift-home-avatar" type="button" aria-label="${__("User Menu")}"></button>`
		).appendTo($actions);
		$avatar.html(frappe.avatar(frappe.session.user, "avatar-medium"));
		this.setup_user_menu($avatar);
	}

	/* The user menu Frappe's own launcher hangs on its avatar - profile,
	   theme, about, support, logout - built with the same frappe.ui.create_menu
	   and the same items, so the avatar behaves here as it does there. A plain
	   route to the profile, which this button did at first, dropped everything
	   else that menu offers. */
	setup_user_menu($avatar) {
		const is_dark = document.documentElement.getAttribute("data-theme") === "dark";
		const items = [
			{
				icon: "edit",
				label: __("Edit Profile"),
				url: `/desk/user/${frappe.session.user}`,
			},
			{
				icon: is_dark ? "sun" : "moon",
				label: __("Toggle Theme"),
				onClick: () => new frappe.ui.ThemeSwitcher().show(),
			},
			{
				icon: "info",
				label: __("About"),
				onClick: () => frappe.ui.toolbar.show_about(),
			},
			...(this.can_customize()
				? [
						{
							icon: "rotate-ccw",
							label: __("Reset Layout"),
							onClick: () => this.reset_layout(),
						},
				  ]
				: []),
			{
				icon: "log-out",
				label: __("Logout"),
				onClick: () => frappe.app.logout(),
			},
		];
		frappe.ui.create_menu({
			parent: $avatar,
			menu_items: items,
			open_on_left: !frappe.utils.is_rtl(),
		});
	}

	/* Edit Layout, Reset Layout and Refresh - the desk's own.

	   The grid here is `frappe.boot.desktop_icons`, the very list Frappe's own
	   launcher edits, so these are that launcher's two actions rather than
	   anything of ours. Reset is a plain server call and runs from here.
	   Editing is not: it drags Frappe's own `.desktop-icon` elements around, so
	   it needs that page - the button opens it and starts edit mode there. */
	/* Arranging the grid is a System Manager's job on this site - Ali's call
	   (2026-08-28), after Customize Workspace turned up for a user without it.
	   One answer, asked in every place that offers it, so they can never
	   disagree: the pencil, the reset beside it, the hero button, the section
	   button and the reset in the user menu.

	   Note this is stricter than Frappe, whose own launcher lets any user
	   rearrange their own tiles - the layout is saved per user either way. */
	can_customize() {
		return frappe.user_roles.includes("System Manager");
	}

	render_desk_actions($actions) {
		const add = (icon, label, fn) => {
			const $b = $(
				`<button class="swift-home-icon-btn" type="button" aria-label="${label}" title="${label}">
					${frappe.utils.icon(icon, "md")}
				</button>`
			).appendTo($actions);
			$b.on("click", fn);
			return $b;
		};

		if (this.can_customize()) {
			add("edit", __("Edit Layout"), () => this.start_edit());
			// rotate-ccw, the icon Frappe's own Reset Layout menu uses -
			// "rotate-left" is in no shipped sprite, so the button drew empty
			add("rotate-ccw", __("Reset Layout"), () => this.reset_layout());
		}
		add("refresh", __("Refresh"), () => this.refresh());

		// Save and Discard live in the bar too, shown only while editing, so
		// the whole flow happens here in the same design.
		this.$edit_controls = $(`
			<span class="swift-home-edit-controls">
				<button class="swift-home-edit-btn is-discard" type="button">${__("Discard")}</button>
				<button class="swift-home-edit-btn is-save" type="button">${__("Save")}</button>
			</span>
		`).appendTo($actions);
		this.$edit_controls.find(".is-save").on("click", () => this.stop_edit(true));
		this.$edit_controls.find(".is-discard").on("click", () => this.stop_edit(false));
	}

	/* Editing happens right here, on this grid.

	   The mechanics are the launcher's: drag to reorder (the same Sortable the
	   launcher uses), hide a tile, bring a hidden one back - and Save writes
	   the same Desktop Layout document through the same whitelisted method, so
	   a layout arranged here is the layout Frappe's own launcher shows, and
	   the other way round. Only the rendering is this page's own, which is
	   what keeps the design. */
	start_edit() {
		if (this.edit_mode) return;
		this.edit_mode = true;
		this.draft = JSON.parse(JSON.stringify(this.all_icons()));
		document.body.classList.add("swift-home-edit");
		this.render_apps();
	}

	stop_edit(save) {
		if (!this.edit_mode) return;
		const draft = this.draft;
		this.edit_mode = false;
		this.draft = null;
		document.body.classList.remove("swift-home-edit");
		if (this.sortable) {
			this.sortable.destroy();
			this.sortable = null;
		}
		if (!save) {
			this.render_apps();
			return;
		}
		this._icons = draft;
		this.render_apps();
		frappe.call({
			method: "frappe.desk.doctype.desktop_layout.desktop_layout.save_layout",
			args: { user: frappe.session.user, layout: JSON.stringify(draft) },
			callback: () => {
				// the launcher's local mirror, kept in step so its own next
				// load agrees with what was just saved here
				try {
					localStorage.setItem(`${frappe.session.user}:desktop`, JSON.stringify(draft));
				} catch (e) {
					// storage full or blocked - the server copy is the truth
				}
				frappe.show_alert({ message: __("Layout saved"), indicator: "green" }, 3);
			},
		});
	}

	/* Reordering the visible tiles reorders the draft. The grid shows a
	   filtered view (children promoted, hidden dropped), so the move is
	   replayed onto the full array by label rather than by index. */
	apply_order($grid) {
		const shown = [...$grid.children(".swift-home-app")].map((el) => el.dataset.label);
		const rank = new Map(shown.map((l, i) => [l, i]));
		this.draft.sort((a, b) => {
			const ra = rank.has(a.label) ? rank.get(a.label) : Infinity;
			const rb = rank.has(b.label) ? rank.get(b.label) : Infinity;
			return ra - rb;
		});
	}

	set_hidden(label, hidden) {
		const icon = this.draft.find((i) => i.label === label);
		if (icon) icon.hidden = hidden ? 1 : 0;
		this.render_apps();
	}

	/* Frappe's own reset: drop the saved layout, then clear the cache so the
	   icons come back from the defaults. Same two steps its menu takes. */
	reset_layout() {
		frappe.confirm(__("Reset the app layout to its defaults?"), () => {
			frappe.call({
				method: "frappe.desk.doctype.desktop_layout.desktop_layout.delete_layout",
				callback: () => frappe.ui.toolbar.clear_cache(),
			});
		});
	}

	/* A refresh of what this page shows: the figures are re-counted and the
	   grid is redrawn from boot. It does not reload the app - clearing the
	   whole cache to refresh four numbers is a heavier hammer than the button
	   promises. */
	async refresh() {
		this.render_apps();
		await this.load_cards(true);
		frappe.show_alert({ message: __("Refreshed"), indicator: "green" }, 3);
	}

	paint_unread() {
		const n = cint(frappe.boot.notification_unread_count || 0);
		const $c = this.$body.find(".swift-home-bell-count");
		$c.text(n > 99 ? "99+" : n).toggleClass("is-on", n > 0);
	}

	/* Frappe has no standalone "new document" dialog in v16 - creating from
	   nothing goes through the command palette, which lists exactly the
	   doctypes this user may create (`get_creatables`). So Create New opens
	   that, already typed. `frappe.new_doc()` with no argument, which this used
	   to call, asked the server for the meta of an undefined doctype and threw
	   `getdoctype() missing 1 required positional argument`. */
	open_search(prefill) {
		const btn = document.querySelector("#navbar-modal-search");
		if (!btn) {
			frappe.set_route("List", "Notification Log");
			return;
		}
		btn.click();
		if (!prefill) return;
		setTimeout(() => {
			const input = document.querySelector("#navbar-search");
			if (!input) return;
			input.value = prefill;
			$(input).trigger("input").trigger("keyup");
		}, 80);
	}

	/* Everything the page needs to draw came in on boot, so the first paint is
	   the whole page - no request, no await, and nothing pops in after the
	   fact. The one thing boot cannot carry is the figures, because counting
	   them costs queries the desk boot should not pay on every page; those
	   render instantly from the last visit's snapshot and are re-counted with
	   a single call only once the snapshot has gone stale. */
	load() {
		const boot = (frappe.boot.swift_theme && frappe.boot.swift_theme.home) || null;
		this.cfg = boot || { enabled: 1, greeting: 1, shortcuts: 1, has_cards: 1 };
		this.cfg.full_name =
			(frappe.boot.user && frappe.boot.user.full_name) || frappe.session.user_fullname || "";

		this.render_topbar();
		this.render_hero();
		if (this.cfg.greeting) this.render_greeting();
		if (this.cfg.shortcuts) this.render_shortcuts();
		this.render_section();
		this.render_apps();
		this.load_cards();
	}

	cards_cache_key() {
		return "swift:home_cards:" + frappe.session.user;
	}

	read_cards_cache() {
		try {
			const raw = sessionStorage.getItem(this.cards_cache_key());
			return raw ? JSON.parse(raw) : null;
		} catch (e) {
			return null;
		}
	}

	load_cards(force) {
		if (!this.cfg.has_cards) {
			this.render_cards([]);
			return Promise.resolve();
		}
		const cached = this.read_cards_cache();
		if (cached) this.render_cards(cached.cards || []);

		const STALE = 60 * 1000;
		if (!force && cached && Date.now() - cached.t < STALE) return Promise.resolve();

		return frappe.xcall("swift_theme.api.home.get_home_cards").then((cards) => {
			this.render_cards(cards || []);
			try {
				sessionStorage.setItem(
					this.cards_cache_key(),
					JSON.stringify({ t: Date.now(), cards: cards || [] })
				);
			} catch (e) {
				// storage full or blocked - the render already happened
			}
		});
	}

	greeting_for(hour) {
		if (hour < 12) return __("Good morning");
		if (hour < 17) return __("Good afternoon");
		return __("Good evening");
	}

	/* The screens do not all say the same thing: two of them greet with
	   "Welcome back" and a different line underneath. Every wording is rendered
	   and CSS picks one, the same way the blocks are chosen - so switching a
	   design never leaves last design's copy on the page waiting for a reload. */
	render_greeting() {
		const name = frappe.utils.escape_html(
			(this.cfg.full_name || "").split(" ")[0] || this.cfg.full_name || ""
		);
		const suffix = (name ? ", " + name : "") + ' <span aria-hidden="true">👋</span>';
		this.$greet.html(`
			<h1>
				<span class="swift-home-hi-time">${this.greeting_for(new Date().getHours())}${suffix}</span>
				<span class="swift-home-hi-back">${__("Welcome back")}${suffix}</span>
			</h1>
			<p>
				<span class="swift-home-sub-work">${__(
					"Here's what's happening in your workspace today."
				)}</span>
				<span class="swift-home-sub-productive">${__("Let's make today productive.")}</span>
				<span class="swift-home-sub-overview">${__("Here's an overview of your business.")}</span>
			</p>
		`);
	}

	/* Only one design shows this, but it is drawn for all of them so the choice
	   stays a matter of CSS. */
	render_hero() {
		this.$hero.html(`
			<h2 class="swift-home-hero-title">${__("All your business in {0}one{1} place", [
				'<em>',
				'</em>',
			])}</h2>
			<p class="swift-home-hero-text">${__(
				"Access all modules, manage operations and grow your business efficiently."
			)}</p>
		`);
		// The mock-up's button, wired to the desk's own act of arranging: it
		// starts the in-place layout edit, the same thing the pencil does - and
		// so it is offered to the same people.
		if (!this.can_customize()) return;
		const $b = $(
			`<button class="swift-home-hero-btn" type="button">${__("Customize Workspace")}</button>`
		).appendTo(this.$hero);
		$b.on("click", () => this.start_edit());
	}

	/* The heading, and - for a System Manager only - the Customize button
	   into Swift Theme Settings. Everyone else gets just the heading: the
	   settings doctype is System Manager territory anyway, so for anyone else
	   the button could only open a permission error. The role check here is
	   presentation; the doctype's own permissions remain the real gate. */
	render_section() {
		this.$section.html(
			`<span class="swift-home-section-title">${__("Your Apps")}</span>`
		);
		if (!this.can_customize()) return;
		const $b = $(
			`<button class="swift-home-section-action" type="button">${__("Customize")}</button>`
		).appendTo(this.$section);
		$b.on("click", () => frappe.set_route("Form", "Swift Theme Settings"));
	}

	render_shortcuts() {
		const items = [
			{ label: __("Create New"), icon: "add", onclick: () => this.open_search("new ") },
			{ label: __("Reports"), icon: "small-file", route: "/app/report" },
			{
				label: __("Notifications"),
				icon: "notification",
				badge: () => cint(frappe.boot.notification_unread_count || 0),
				onclick: () => frappe.set_route("List", "Notification Log"),
			},
		];
		const $wrap = $('<div class="swift-home-shortcut-box"></div>').appendTo(this.$shortcuts);
		$wrap.append(`<div class="swift-home-shortcut-title">${__("Shortcuts")}</div>`);
		const $row = $('<div class="swift-home-shortcut-row"></div>').appendTo($wrap);

		items.forEach((it) => {
			const count = it.badge ? it.badge() : 0;
			const $b = $(`
				<button class="swift-home-shortcut" type="button">
					${frappe.utils.icon(it.icon, "sm")}<span>${it.label}</span>
					${count ? `<span class="swift-home-shortcut-badge">${count}</span>` : ""}
				</button>
			`).appendTo($row);
			$b.on("click", () => (it.route ? frappe.set_route(it.route) : it.onclick()));
		});
	}

	/**
	 * What belongs on the grid.
	 *
	 * Not simply "icons with no parent". Frappe hides the icon for the app the
	 * desk itself belongs to - on an ERPNext site the `ERPNext` icon is
	 * hidden=1 - and hangs Selling, Stock, Buying and the rest underneath it.
	 * Taking only top-level icons therefore dropped most of the modules while
	 * keeping the few ERPNext leaves that happen to sit at the root.
	 *
	 * So: skip anything hidden, and lift a child up when its parent is hidden.
	 * Its parent is not reachable, so the child is a destination in its own
	 * right - which is exactly how the sidebar treats it too.
	 */
	/* The saved layout is the whole icons array with the user's order and
	   hidden flags - the same document Frappe's launcher edits. It is merged
	   against boot rather than used raw: boot is the permission filter, so an
	   entry whose label boot no longer offers is dropped, and anything boot
	   gained since the layout was saved (a newly installed app) is appended. */
	all_icons() {
		if (this.edit_mode && this.draft) return this.draft;
		if (this._icons) return this._icons;
		const boot = (frappe.boot && frappe.boot.desktop_icons) || [];
		const layout = this.cfg && this.cfg.layout;
		if (!layout || !layout.length) return (this._icons = boot);
		const by_label = new Map(boot.map((i) => [i.label, i]));
		const seen = new Set();
		const merged = [];
		layout.forEach((saved) => {
			const live = by_label.get(saved.label);
			if (!live || seen.has(saved.label)) return;
			seen.add(saved.label);
			// the saved entry carries the user's choices; everything else -
			// links, icons, permissions - comes fresh from boot
			merged.push(Object.assign({}, live, { hidden: cint(saved.hidden) }));
		});
		boot.forEach((i) => {
			if (!seen.has(i.label)) merged.push(i);
		});
		return (this._icons = merged);
	}

	children_of(label) {
		return this.all_icons().filter((i) => i.parent_icon === label && !cint(i.hidden));
	}

	top_level() {
		const icons = this.all_icons();
		const hidden_labels = new Set(icons.filter((i) => cint(i.hidden)).map((i) => i.label));
		return icons.filter(
			(i) => !cint(i.hidden) && (!i.parent_icon || hidden_labels.has(i.parent_icon))
		);
	}

	render_apps(parent_label) {
		// editing always edits the top level - a drill-down inside a draft
		// would mean two levels of unsaved state
		if (this.edit_mode) parent_label = null;
		const items = parent_label ? this.children_of(parent_label) : this.top_level();
		this.$apps.empty();

		if (parent_label) {
			const $back = $(`
				<button class="swift-home-back" type="button">
					${frappe.utils.icon("left", "sm")}
					<span>${frappe.utils.escape_html(__(parent_label))}</span>
				</button>
			`).appendTo(this.$apps);
			$back.on("click", () => this.render_apps(null));
		}

		if (!items.length) {
			this.$apps.append(`<div class="swift-home-empty">${__("Nothing here yet.")}</div>`);
			return;
		}

		const $grid = $('<div class="swift-home-grid"></div>').appendTo(this.$apps);
		items.forEach((icon) => {
			const label = frappe.utils.escape_html(icon.label || "");
			// A Folder has no destination of its own - Accounting, for one, has
			// no link and no link_to, only nine children. Sending it through
			// route_for() landed on /app and the click did nothing. It opens
			// its own contents instead, the way the sidebar expands it.
			const has_logo = !!(icon.icon_image || icon.logo_url);
			const kids = this.children_of(icon.label);
			// Children make a group, whatever else the icon carries. Frappe HR
			// ships link=/desk/people - a workspace this site does not have -
			// while holding nine perfectly good children; the launcher shows
			// them as a group, and following the broken link was a Not Found.
			const is_folder = icon.icon_type === "Folder" || kids.length > 0;

			const $a = $(`
				<a class="swift-home-app${is_folder ? " is-folder" : ""}${has_logo ? " has-logo" : ""}"
				   href="${is_folder ? "#" : frappe.utils.escape_html(this.route_for(icon))}">
					<span class="swift-home-app-icon"${
						has_logo ? "" : ` style="--swift-tile: ${this.tile_color(icon)}"`
					}>${this.icon_html(icon)}</span>
					<span class="swift-home-app-label">${label}</span>
					${
						is_folder
							? `<span class="swift-home-app-count">${kids.length}</span>`
							: ""
					}
				</a>
			`).appendTo($grid);
			$a.attr("title", label);

			$a.attr("data-label", icon.label || "");

			if (this.edit_mode) {
				// a tile in edit mode is a thing being arranged, not a link
				$a.on("click", (e) => e.preventDefault());
				const $x = $(
					`<button class="swift-home-app-hide" type="button" title="${__("Hide")}">×</button>`
				).appendTo($a);
				$x.on("click", (e) => {
					e.preventDefault();
					e.stopPropagation();
					this.set_hidden(icon.label, true);
				});
			} else if (is_folder) {
				$a.on("click", (e) => {
					e.preventDefault();
					this.render_apps(icon.label);
				});
			}
		});

		if (this.edit_mode) {
			this.setup_edit_grid($grid);
		}
	}

	setup_edit_grid($grid) {
		if (this.sortable) this.sortable.destroy();
		this.sortable = new Sortable($grid.get(0), {
			animation: 150,
			onEnd: () => this.apply_order($grid),
		});

		// what has been hidden, offered back - the launcher's IconsPane, drawn
		// this page's way
		const hidden = this.draft.filter((i) => cint(i.hidden));
		if (!hidden.length) return;
		const $strip = $(`
			<div class="swift-home-hidden-strip">
				<span class="swift-home-hidden-title">${__("Hidden")}</span>
			</div>
		`).appendTo(this.$apps);
		hidden.forEach((icon) => {
			const $b = $(`
				<button class="swift-home-hidden-item" type="button">
					<span class="swift-home-app-icon" style="--swift-tile: ${this.tile_color(icon)}">
						${this.icon_html(icon)}
					</span>
					<span>${frappe.utils.escape_html(icon.label || "")}</span>
				</button>
			`).appendTo($strip);
			$b.on("click", () => this.set_hidden(icon.label, false));
		});
	}

	/* The mock-ups give every tile its own coloured chip, and the desk does not
	   hand us one: `bg_color` exists on a Desktop Icon but is unset on a stock
	   site, and most icons are a monochrome sprite glyph. App icons that ship
	   their own logo (Frappe CRM, Frappe HR, the Framework mark) are already
	   coloured and are left alone.

	   So where the site has not chosen a colour, one is derived from the label.
	   A hash rather than a position, because position changes the moment an app
	   is installed or a permission changes the list - and a tile that changes
	   colour between two visits reads as a different tile. */
	tile_color(icon) {
		if (icon.bg_color) return icon.bg_color;
		const label = icon.label || "";
		let h = 0;
		for (let i = 0; i < label.length; i++) h = (h * 31 + label.charCodeAt(i)) >>> 0;
		return TILE_COLORS[h % TILE_COLORS.length];
	}

	/* The destination of a tile, resolved the way Frappe's own launcher
	   resolves it (its get_route): an External icon goes to its link, and a
	   Workspace Sidebar icon goes wherever the FIRST link of its sidebar
	   leads, built with frappe.utils.generate_route - the same call every
	   sidebar item uses. Slugging link_to by hand, which this did at first,
	   invented workspace routes that do not exist: Organization has no
	   workspace of its own, only a sidebar whose first entry is a doctype
	   list, and /app/organization was a Page Not Found. */
	route_for(icon) {
		if (icon.link_type === "External" && icon.link) return icon.link;

		const sidebar =
			frappe.boot.workspace_sidebar_item &&
			frappe.boot.workspace_sidebar_item[(icon.label || "").toLowerCase()];
		if (sidebar) {
			const first = (sidebar.items || []).find((i) => i.type === "Link");
			if (first) return this.route_for_sidebar_link(first, icon.label) || "#";
		}

		if (icon.link) return icon.link;
		if (icon.link_to) return "/app/" + frappe.router.slug(icon.link_to);
		return "#";
	}

	route_for_sidebar_link(first, sidebar_label) {
		if (first.link_type === "Report") {
			const args = { type: first.link_type, name: first.link_to };
			if (first.report) {
				args.is_query_report =
					first.report.report_type === "Query Report" ||
					first.report.report_type === "Script Report";
				args.report_ref_doctype = first.report.ref_doctype;
			}
			return frappe.utils.generate_route(args);
		}
		if (first.link_type === "Workspace") {
			const ws = frappe.workspaces[frappe.router.slug(first.link_to)];
			if (!ws) return null;
			return frappe.utils.generate_route({
				type: "workspace",
				name: ws.title,
				public: ws.public ? 1 : 0,
				route_options: { sidebar: sidebar_label },
			});
		}
		if (first.link_type === "URL") return first.url;
		if (first.link_type === "Page" && first.route_options) {
			return frappe.utils.generate_route({
				type: first.link_type,
				name: first.link_to,
				route_options: JSON.parse(first.route_options),
			});
		}
		return frappe.utils.generate_route({
			type: first.link_type,
			name: first.link_to,
			tab: first.tab,
			route_options: { sidebar: sidebar_label },
		});
	}

	icon_html(icon) {
		if (icon.icon_image || icon.logo_url) {
			const src = frappe.utils.escape_html(icon.icon_image || icon.logo_url);
			return `<img src="${src}" alt="" loading="lazy">`;
		}
		if (icon.icon) return frappe.utils.icon(icon.icon, "md", "", "", "", true);
		return `<span class="swift-home-app-letter">${frappe.utils.escape_html(
			(icon.label || "?").charAt(0).toUpperCase()
		)}</span>`;
	}

	render_cards(cards) {
		if (!cards.length) {
			this.$cards.empty();
			return;
		}
		const $row = $('<div class="swift-home-card-row"></div>').appendTo(this.$cards.empty());
		cards.forEach((c) => {
			// Only cards set up to show a trend carry one, so the badge appears
			// exactly where a dashboard would show it and nowhere else.
			const d = c.delta;
			const up = d && d.percent > 0;
			const flat = d && d.percent === 0;
			const trend = d
				? `<span class="swift-home-card-delta ${
						flat ? "is-flat" : up ? "is-up" : "is-down"
				  }">${up ? "+" : ""}${d.percent}%</span>`
				: "";
			const $c = $(`
				<a class="swift-home-card" href="${frappe.utils.escape_html(c.route || "#")}">
					<span class="swift-home-card-label">${frappe.utils.escape_html(c.label)}</span>
					<span class="swift-home-card-value">${this.format(c)}${trend}</span>
					<span class="swift-home-card-doctype">${frappe.utils.escape_html(
						d && d.since ? d.since : __(c.doctype || "")
					)}</span>
				</a>
			`).appendTo($row);
			$c.attr("title", c.label);
		});
	}

	format(card) {
		const v = card.value;
		if (v === null || v === undefined) return "—";
		if (card.function === "Count" || card.show_full_number) {
			return frappe.utils.escape_html(format_number(v, null, 0));
		}
		if (card.currency) return frappe.utils.escape_html(format_currency(v, card.currency));
		return frappe.utils.escape_html(frappe.utils.shorten_number(v, null, 3));
	}
}
