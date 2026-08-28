# Copyright (c) 2026, Ali Raza and contributors
# For license information, please see license.txt

"""Data for the Swift home page.

Nothing here decides what a user may see. The apps come from Frappe's own
`desktop_icons`, which already filters by app permission, by whether the
workspace has any item this user can open, and by any roles set on the icon.
The figures come from Number Cards, which carry their own `has_permission` and
count through `frappe.get_list` - so a User Permission on Company or Territory
narrows the number without anything here knowing that it exists.

Re-implementing either check would mean maintaining a second, quietly different
answer to "what is this user allowed to see".
"""

import json

import frappe
from frappe import _
from frappe.desk.doctype.number_card.number_card import (
	get_percentage_difference,
	get_result,
)
from frappe.permissions import has_permission
from frappe.utils import flt

# What Frappe itself calls the window a card's percentage is measured over.
STATS_QUALIFIER = {
	"Daily": "since yesterday",
	"Weekly": "since last week",
	"Monthly": "since last month",
	"Yearly": "since last year",
}


def _settings():
	return frappe.get_cached_doc("Swift Theme Settings")


def _card_type(card) -> str:
	# older cards predate the field and are Document Type by construction -
	# the dashboard widget applies the same default
	return card.get("type") or "Document Type"


def _card_value(card):
	"""The card's figure, by the same three paths the dashboard widget takes.

	Document Type counts through frappe.get_list, Report runs the report
	through frappe.desk.query_report.run (which enforces the report's own
	permissions), Custom calls the card's whitelisted method. Feeding every
	card through the Document Type evaluator, as this did at first, sent a
	Report card's empty document_type into frappe.get_list - "DocType None
	not found"."""
	kind = _card_type(card)

	if kind == "Document Type":
		return get_result(card, card.filters_json)

	if kind == "Report":
		from frappe.desk.query_report import run

		res = run(card.report_name, filters=card.filters_json, ignore_prepared_report=True)
		field = card.get("report_field")
		values = [flt(row.get(field)) for row in res.get("result") or [] if isinstance(row, dict) and row.get(field) is not None]
		if not values:
			return 0
		fn = card.get("report_function")
		if fn == "Sum":
			return sum(values)
		if fn == "Average":
			return sum(values) / len(values)
		if fn == "Minimum":
			return min(values)
		if fn == "Maximum":
			return max(values)
		return values[0]

	if kind == "Custom":
		method = frappe.get_attr(card.method)
		# the same guard xcall applies when the widget calls it
		frappe.is_whitelisted(method)
		# through frappe.call, not directly: these methods disagree about their
		# arguments (get_upcoming_holidays() takes none at all), and frappe.call
		# passes each function only the kwargs it accepts - the same courtesy
		# xcall's HTTP path extends to them
		res = frappe.call(method, filters=card.filters_json)
		if isinstance(res, dict):
			res = res.get("value")
		# the widget reads only .value / a number; anything else renders N/A
		# there, and here it renders nothing
		return flt(res) if isinstance(res, int | float) else None

	return None


def _card_route(card):
	kind = _card_type(card)
	if kind == "Report" and card.get("report_name"):
		return "/app/query-report/" + card.report_name
	if card.get("document_type"):
		return f"/app/{frappe.scrub(card.document_type).replace('_', '-')}"
	return None


@frappe.whitelist()
def get_home_cards() -> list[dict]:
	"""The configured Number Cards this user may read, with their figures."""
	s = _settings()
	if not int(s.get("enable_home_page") or 0):
		return []

	names = [row.number_card for row in (s.get("home_cards") or []) if row.number_card]
	if not names:
		return []

	# A message queued while building this list has nowhere useful to go: the
	# page draws figures, and anything a skipped card had to say would arrive
	# as a dialog with no context. Anything genuinely wrong is in the error log.
	before = len(frappe.get_message_log())

	out = []
	for name in names:
		# One broken card must not take the row down, and must not leak either:
		# a frappe.throw inside a caught exception still queues its message,
		# which then rides out in _server_messages - "DocType None not found"
		# appeared on an otherwise successful response exactly that way, from a
		# Report card fed into the Document Type evaluator.
		try:
			card = frappe.get_doc("Number Card", name)

			# Number Card's own has_permission: a Document Type card needs read
			# on the doctype it counts, a Report card needs the report, a
			# Custom card its doctype. This is what keeps a card off the page
			# for a user who cannot open what stands behind it.
			#
			# print_logs=False because a refusal is the normal case here, not an
			# error to report: the answer to "may this user see this card" is
			# often no, and we simply leave the card out. Left on - it defaults
			# to True - each refusal queued a msgprint that rode out in
			# _server_messages and opened an empty dialog at the end of every
			# desk load, for every user who lacked read on one configured card.
			if not has_permission(
				"Number Card", ptype="read", doc=card, print_logs=False
			):
				continue

			value = _card_value(card)
		except Exception:
			frappe.log_error(title=f"Swift home card failed: {name}")
			frappe.clear_last_message()
			continue

		if value is None:
			continue

		# The trend beside the figure, when the card is set up to show one.
		# Frappe's own function, so the comparison window and the query behind
		# the earlier figure are the ones the card would use on a dashboard -
		# and it re-fetches the card server-side, so it cannot be talked into
		# reporting on a card this user could not read. Document Type cards
		# only: the dashboard widget applies the same guard, because the
		# comparison re-queries by document_type, which the other kinds may not
		# have - get_percentage_difference alone does not check.
		delta = None
		if _card_type(card) == "Document Type" and int(card.get("show_percentage_stats") or 0):
			try:
				pct = get_percentage_difference(card.as_dict(), card.filters_json, value)
				if pct is not None:
					delta = {
						"percent": round(float(pct), 1),
						"since": _(STATS_QUALIFIER.get(card.get("stats_time_interval"), "")),
					}
			except Exception:
				frappe.log_error(title=f"Swift home card trend failed: {name}")
				frappe.clear_last_message()

		out.append(
			{
				"name": card.name,
				"delta": delta,
				"label": _(card.label),
				"doctype": card.document_type,
				"function": card.function,
				"value": value,
				"currency": card.get("currency"),
				"show_full_number": int(card.get("show_full_number") or 0),
				# where the tile goes when clicked - the list it counts, or
				# the report it reads
				"route": _card_route(card),
			}
		)

	# belt and braces: whatever any of the above queued, drop it. Only the
	# messages this function added - anything the request already carried is
	# left alone.
	log = frappe.get_message_log()
	if len(log) > before:
		frappe.local.message_log = log[:before]

	return out


def _saved_layout():
	"""The user's own saved icon layout - the same Desktop Layout document
	Frappe's launcher writes, so an order saved on either page holds on both.
	Only ever the session user's own document, which is also all its own page
	reads."""
	raw = frappe.db.get_value("Desktop Layout", frappe.session.user, "layout")
	if not raw:
		return None
	try:
		layout = json.loads(raw)
	except ValueError:
		return None
	return layout if isinstance(layout, list) and layout else None


@frappe.whitelist()
def get_home_config() -> dict:
	"""What the page should draw. The apps are read from boot on the client."""
	s = _settings()
	on = int(s.get("enable_home_page") or 0)
	return {
		"layout": _saved_layout(),
		"enabled": on,
		"greeting": on and int(s.get("home_greeting") or 0),
		"shortcuts": on and int(s.get("home_shortcuts") or 0),
		"full_name": frappe.utils.get_fullname(frappe.session.user),
		# The designs with a top bar of their own draw the site's brand in it,
		# the same name and logo the sidebar header uses.
		"brand_name": s.get("brand_name") or frappe.get_website_settings("app_name") or "Frappe",
		"brand_logo": s.get("brand_logo") or None,
	}
