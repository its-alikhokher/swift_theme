/* Swift Theme — more than one field on a calendar event.

   Frappe's calendar shows exactly one thing per record: the doctype's subject
   field, mapped to the event title. Everything else about the record - who it
   is for, what state it is in, what it is worth - means opening it.

   This adds the fields configured in Swift Theme Settings underneath that
   title. Two seams in frappe.views.Calendar are wrapped, and nothing else:

   * get_args, to ask get_events for the extra columns. The server fetches them
     through frappe.get_list, so permissions are applied there, not here: a
     field the reader cannot see never arrives, and this code never has to
     decide who may see what.
   * prepare_events, to append the values to the title, one per line. The title
     is rendered as text by FullCalendar, so the lines are made to show with
     `white-space: pre-line` rather than by injecting markup into an event.

   A doctype with a get_events method of its own - Event is one - returns a
   fixed set of columns and ignores the fields asked for. For those, whatever
   did not arrive is read afterwards with one get_list for the whole batch and
   written onto the rendered events. Permissions are still Frappe's either
   way: both get_events and get_list apply them.

   With nothing configured for a doctype, both wrappers hand straight back to
   Frappe's own code. */

frappe.provide("frappe.swift");

(function () {
	function configured(doctype) {
		const map =
			(frappe.boot && frappe.boot.swift_theme && frappe.boot.swift_theme.calendar_fields) || {};
		return map[doctype] || [];
	}

	function label_for(doctype, fieldname) {
		try {
			const df = frappe.meta.get_docfield(doctype, fieldname);
			return df && df.label ? __(df.label) : fieldname;
		} catch (e) {
			return fieldname;
		}
	}

	function format(doctype, fieldname, value) {
		if (value === null || value === undefined || value === "") return "";
		try {
			const df = frappe.meta.get_docfield(doctype, fieldname);
			if (df) return frappe.utils.html2text(frappe.format(value, df, { inline: true }) || "");
		} catch (e) {
			/* fall through to the raw value */
		}
		return String(value);
	}

	function patch() {
		const Cal = frappe.views && frappe.views.Calendar;
		if (!Cal || Cal.prototype.__swiftFields) return false;
		Cal.prototype.__swiftFields = true;

		const get_args = Cal.prototype.get_args;
		Cal.prototype.get_args = function (start, end) {
			const args = get_args.apply(this, arguments);
			const extra = configured(this.doctype);
			if (!extra.length) return args;

			// get_events defaults to [start, end, title, name] when no fields are
			// given, so the defaults have to be restated alongside the extras.
			const fm = this.field_map || {};
			const base = [fm.start, fm.end, fm.title, "name"].filter(Boolean);
			args.fields = JSON.stringify([...new Set([...base, ...extra])]);
			return args;
		};

		function lines_for(doctype, fields, row) {
			const lines = [];
			fields.forEach((f) => {
				const text = format(doctype, f, row[f]);
				if (text) lines.push(`${label_for(doctype, f)}: ${text}`);
			});
			return lines;
		}

		const prepare = Cal.prototype.prepare_events;
		Cal.prototype.prepare_events = function (events) {
			const extra = configured(this.doctype);
			if (!extra.length) return prepare.apply(this, arguments);

			// The record's own values, taken before Frappe's prepare runs: it
			// copies every field_map target over the row - title, status,
			// color - and a configured field can share a name with one. Event
			// maps status to event_type, so its `status` would otherwise read
			// back as "Public".
			const own = {};
			(events || []).forEach((d) => {
				own[d.name] = {};
				extra.forEach((f) => {
					if (f in d) own[d.name][f] = d[f];
				});
			});

			const prepared = prepare.apply(this, arguments);
			const doctype = this.doctype;
			const missing = [];
			prepared.forEach((d) => {
				const row = own[d.name] || {};
				const lines = lines_for(doctype, extra, row);
				if (lines.length) d.title = [d.title, ...lines].join("\n");
				if (extra.some((f) => !(f in row))) missing.push(d.name);
			});
			if (missing.length) fill_later(this, missing, extra);
			return prepared;
		};

		// Columns the doctype's own get_events did not return. FullCalendar
		// has the events by the time this answers, so they are updated in
		// place; the first line of the title is the subject and is kept.
		function fill_later(cal, names, extra) {
			const doctype = cal.doctype;
			frappe
				.xcall("frappe.client.get_list", {
					doctype: doctype,
					filters: [["name", "in", names]],
					fields: ["name", ...extra],
					limit_page_length: 0,
				})
				.then((rows) => {
					const fc = cal.fullCalendar;
					if (!fc || !fc.getEventById) return;
					(rows || []).forEach((row) => {
						const ev = fc.getEventById(row.name);
						if (!ev) return;
						const lines = lines_for(doctype, extra, row);
						if (!lines.length) return;
						const subject = (ev.title || "").split("\n")[0];
						ev.setProp("title", [subject, ...lines].join("\n"));
					});
				});
		}
		return true;
	}

	// The calendar view is loaded on demand, so the class may not exist yet.
	if (!patch()) {
		let tries = 40;
		const timer = setInterval(() => {
			if (patch() || --tries <= 0) clearInterval(timer);
		}, 500);
	}
})();
