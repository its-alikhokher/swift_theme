/* Swift Theme — two small repairs to Frappe HR's organisational chart.

   Both are things CSS cannot do, and neither touches how the chart works:

   * An employee with no photo leaves `.avatar-frame` empty, so every node
     showed a blank grey disc. Their initials go in instead - the same thing
     Frappe's own avatars do everywhere else.
   * A leaf node prints "0 Connections", which is noise on exactly the nodes
     with nothing to report. It is removed; anything above zero is kept and
     styled as a badge.

   The chart redraws on expand, collapse and company change without an event
   to hang this on, so it is done with a MutationObserver over the container -
   cheap, and it cannot miss a node that appears later. */

frappe.provide("frappe.swift");

(function () {
	function initials(name) {
		const parts = (name || "").trim().split(/\s+/).filter(Boolean);
		if (!parts.length) return "";
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	/* ---- the extra fields a site wants on each card ----

	   HR's get_children returns a fixed set - name, title, image, connections -
	   and it is whitelisted, so widening it is not ours to do. The configured
	   fields are read separately with frappe.client.get_list, which means the
	   viewer's own permissions decide what comes back: a field they cannot see
	   on the Employee record does not reach the card either.

	   Fetched once per set of ids and cached, so expanding a branch asks only
	   for the nodes it just added. */
	const cache = {};
	let pending = false;

	function wanted() {
		return (
			(frappe.boot && frappe.boot.swift_theme && frappe.boot.swift_theme.orgchart_fields) || []
		);
	}

	function fetch_extra(ids) {
		const fields = wanted();
		if (!fields.length || pending) return;
		const missing = ids.filter((id) => !(id in cache));
		if (!missing.length) return;

		pending = true;
		frappe
			.xcall("frappe.client.get_list", {
				doctype: "Employee",
				filters: [["name", "in", missing]],
				fields: ["name", ...fields],
				limit_page_length: 0,
			})
			.then((rows) => {
				// Mark every id asked for, so one that came back empty - filtered
				// out by permissions, say - is not asked for again on each tick.
				missing.forEach((id) => (cache[id] = cache[id] || null));
				(rows || []).forEach((row) => (cache[row.name] = row));
			})
			.finally(() => {
				pending = false;
			});
	}

	function render_extra(card) {
		const fields = wanted();
		if (!fields.length) return;
		const row = cache[card.id];
		if (!row || card.dataset.swiftExtra) return;

		const info = card.querySelector(".node-info");
		if (!info) return;

		const lines = [];
		fields.forEach((f) => {
			const value = row[f];
			if (value === null || value === undefined || value === "") return;
			let text = value;
			try {
				const df = frappe.meta.get_docfield("Employee", f);
				if (df) text = frappe.utils.html2text(frappe.format(value, df, { inline: true }) || "");
			} catch (e) {
				/* the raw value will do */
			}
			lines.push(text);
		});
		if (!lines.length) return;

		card.dataset.swiftExtra = "1";
		const el = document.createElement("div");
		el.className = "node-extra";
		el.textContent = lines.join(" · ");
		info.appendChild(el);
	}

	/* A url in the field is not the same as an image on disk: files get deleted
	   from under the record, and a private one the viewer cannot read answers
	   403. A background-image that fails leaves no trace in the DOM, so it is
	   probed once per url and the initials come back if it did not load. */
	const photos = {};

	function photo_loads(url) {
		if (url in photos) return photos[url];
		photos[url] = new Promise((resolve) => {
			const probe = new Image();
			probe.onload = () => resolve(true);
			probe.onerror = () => resolve(false);
			probe.src = url;
		});
		return photos[url];
	}

	function dress(root) {
		(root.querySelectorAll ? root.querySelectorAll(".node-card") : []).forEach((card) => {
			const image = card.querySelector(".node-image");
			const frame = card.querySelector(".node-image .avatar-frame");
			if (frame && !frame.dataset.swiftDone) {
				frame.dataset.swiftDone = "1";
				// The name is on .node-image, not on the frame itself; the
				// card's own heading is the fallback.
				const name =
					(image && image.getAttribute("title")) ||
					(card.querySelector(".node-name") || {}).textContent ||
					"";
				const fallback = () => {
					frame.style.backgroundImage = "none";
					frame.classList.remove("has-photo");
					frame.textContent = initials(name);
				};
				// The template always sets a background-image, even when the
				// employee has no photo - so "has a photo" means a real url.
				const bg = frame.style.backgroundImage || "";
				const url = (bg.match(/url\(["']?(.*?)["']?\)$/) || [])[1];
				if (!url || /^(undefined|null)$/.test(url)) {
					fallback();
				} else {
					frame.classList.add("has-photo");
					photo_loads(url).then((ok) => ok || fallback());
				}
			}

			// The template prints the title as "Job Title&nbsp;&middot;&nbsp;",
			// a separator that only made sense when the count sat on the same
			// line. On its own line it is a stray dot.
			const title = card.querySelector(".node-title");
			if (title && !title.dataset.swiftDone) {
				title.dataset.swiftDone = "1";
				title.textContent = title.textContent
					.replace(/[\u00a0\s]*[·\u00b7][\u00a0\s]*$/, "")
					.trim();
			}

			render_extra(card);

			const conn = card.querySelector(".node-connections");
			if (conn && !conn.dataset.swiftDone) {
				conn.dataset.swiftDone = "1";
				const n = parseInt((conn.textContent.match(/\d+/) || ["0"])[0], 10);
				if (!n) conn.remove();
				else conn.textContent = conn.textContent.replace(/[·\u00b7]/g, "").trim();
			}
		});
	}

	/* ---- top to bottom, and connectors that survive a resize ----

	   HR lays the chart out left to right: `ul.hierarchy` is a row of levels,
	   so a deep organisation runs off the right edge and reads sideways. Ali
	   asked for it the way an org chart is normally drawn - the root on top,
	   each level below the last. That is a CSS change, and deliberately only a
	   CSS change: the DOM stays exactly as HR builds it, so expand, collapse
	   and the active-path logic - all of which walk that structure by index -
	   keep working untouched.

	   The connectors then have to be redrawn, because HR joins the RIGHT edge
	   of a parent to the LEFT edge of a child. Two problems come with them:

	   * they are computed from offsetLeft/offsetTop at the moment a node is
	     added, and never again - so any reflow (a resized window, a zoom, a
	     card that grew because its title wrapped) leaves every line pointing
	     at where the nodes used to be.
	   * the geometry itself is horizontal.

	   So add_connector is replaced with a vertical one, and a redraw is bound
	   to resize. Only the drawing is ours; which nodes connect to which is
	   still HR's answer, read back off the paths it already tagged. */

	/* Measured against the SVG the lines are drawn into, not against
	   offsetParent.

	   HR uses offsetLeft/offsetTop, which are relative to whichever ancestor
	   happens to be positioned - and in this tree that is a different element
	   for different nodes, so the moment the layout changes the numbers stop
	   describing the same space as the SVG. getBoundingClientRect is in screen
	   space for every element alike; subtracting the SVG's own rect puts them
	   all in its coordinates. That is also what makes the lines survive a
	   zoom: both rects scale together, so the difference stays correct. */
	function frame() {
		const svg = document.getElementById("arrows");
		return svg ? svg.getBoundingClientRect() : null;
	}

	function centre_bottom(el, f) {
		const r = el.getBoundingClientRect();
		return { x: r.left - f.left + r.width / 2, y: r.bottom - f.top };
	}

	function centre_top(el, f) {
		const r = el.getBoundingClientRect();
		return { x: r.left - f.left + r.width / 2, y: r.top - f.top };
	}

	function vertical_path(from, to) {
		// Down out of the parent, across at the midpoint, then down into the
		// child - with a small radius on the two turns so it does not read as
		// a hard staircase.
		const midY = from.y + Math.max(16, (to.y - from.y) / 2);
		if (Math.abs(from.x - to.x) < 2) {
			return `M${from.x},${from.y} L${to.x},${to.y}`;
		}
		const r = 10;
		const dir = to.x > from.x ? 1 : -1;
		const sweep1 = dir > 0 ? 0 : 1;
		const sweep2 = dir > 0 ? 1 : 0;
		return [
			`M${from.x},${from.y}`,
			`L${from.x},${midY - r}`,
			`a${r},${r} 0 0 ${sweep1} ${r * dir},${r}`,
			`L${to.x - r * dir},${midY}`,
			`a${r},${r} 0 0 ${sweep2} ${r * dir},${r}`,
			`L${to.x},${to.y}`,
		].join(" ");
	}

	function patch_chart() {
		const Chart = window.hrms && hrms.HierarchyChart;
		if (!Chart || Chart.prototype.__swiftVertical) return false;
		Chart.prototype.__swiftVertical = true;

		Chart.prototype.add_connector = function (parent_id, child_id) {
			const parent_node = document.getElementById(`${parent_id}`);
			const child_node = document.getElementById(`${child_id}`);
			if (!parent_node || !child_node) return;

			const f = frame();
			if (!f) return;
			const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
			path.setAttribute(
				"d",
				vertical_path(centre_bottom(parent_node, f), centre_top(child_node, f))
			);
			this.set_path_attributes(path, parent_id, child_id);
			const host = document.getElementById("connectors");
			if (host) host.appendChild(path);
		};
		return true;
	}

	/* Every existing line, recomputed from where the nodes are now. HR tagged
	   each path with the pair it joins, so nothing has to be remembered. */
	function redraw_connectors() {
		const host = document.getElementById("connectors");
		const f = frame();
		if (!host || !f) return;
		host.querySelectorAll("path[data-parent][data-child]").forEach((path) => {
			const parent_node = document.getElementById(path.getAttribute("data-parent"));
			const child_node = document.getElementById(path.getAttribute("data-child"));
			if (!parent_node || !child_node) return;
			path.setAttribute(
				"d",
				vertical_path(centre_bottom(parent_node, f), centre_top(child_node, f))
			);
		});
	}

	/* A ticker, not a MutationObserver.

	   The observer was watching `.hierarchy`, and "Expand All" replaces that
	   container outright - so every node added afterwards arrived in a host
	   nothing was listening to, and the expanded half of the chart went
	   undressed. Re-attaching on every redraw is more machinery than this
	   needs: the nodes carry a `swiftDone` flag, so a sweep costs one
	   querySelectorAll over a few dozen elements and does nothing on the
	   second pass. The ticker stops the moment the route leaves the chart. */
	let ticker = null;
	let sized = null;

	function stop() {
		if (ticker) {
			clearInterval(ticker);
			ticker = null;
		}
		if (sized) {
			window.removeEventListener("resize", sized);
			sized = null;
		}
	}

	function start() {
		const route = (frappe.get_route() || []).join("/");
		if (!/organizational-chart/i.test(route)) {
			stop();
			return;
		}
		patch_chart();
		if (ticker) return;
		dress(document);
		sized = () => redraw_connectors();
		window.addEventListener("resize", sized);
		ticker = setInterval(() => {
			const here = (frappe.get_route() || []).join("/");
			if (!/organizational-chart/i.test(here)) {
				stop();
				return;
			}
			patch_chart();
			fetch_extra([...document.querySelectorAll(".node-card")].map((c) => c.id).filter(Boolean));
			dress(document);
			redraw_connectors();
		}, 400);
	}

	if (frappe.router && frappe.router.on) frappe.router.on("change", start);
	if (frappe.after_ajax) frappe.after_ajax(() => setTimeout(start, 400));
})();
