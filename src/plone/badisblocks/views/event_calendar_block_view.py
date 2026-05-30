"""EventCalendarBlockView browser view.

Renders the ``eventCalendar`` block from volto-light-theme: a date-range filter,
a text search and a list of upcoming events. In Volto this is a faceted search
block that queries the ``@querystring-search`` endpoint client-side; here it
renders server-side and filters through a plain GET form, so it works without
JavaScript -- native ``<input type="date">`` fields provide the range picker and
submitting reloads the page with the filter applied.

The event query uses ``plone.app.event``'s ``get_events`` (events under the
navigation root, in the given timeframe, sorted by start), then serializes each
brain via ``ISerializeToJsonSummary`` -- the same path the listing block uses --
so each card can carry an ``image_scales``-derived preview just like Volto's
DefaultSummary. Results are rendered as calendar cards mirroring
@kitconcept/volto-light-theme's EventTemplate (a day/month "date inset" plus a
summary). Recurrence expansion is not done here (brains, not occurrences); it can
be added later with ``ret_mode``/``expand``.

Filter parameters are read from the request: ``event_from``/``event_to``
(``YYYY-MM-DD`` from the date inputs) and ``event_search`` (SearchableText). They
are intentionally plain names; a page is expected to carry a single event
calendar block.

Live filtering: badisblocks.js fetches this same view standalone
(``<context>/@@block-eventCalendar?block_id=...&event_from=...``) and swaps the
``.event-calendar-results`` fragment in place, so the date/search logic stays
server-side. When rendered standalone the dispatcher hasn't filled ``data``, so
``__call__`` self-populates it from the context's blocks using ``block_id``.
"""

from datetime import datetime
from datetime import time

from zope.component import getMultiAdapter
from zope.i18n import translate

from plone.app.event.base import default_timezone
from plone.app.event.base import get_events
from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.listing_block_view import _image_view_model
from plone.badisblocks.views.listing_block_view import _path
from plone.base.i18nl10n import monthname_english
from plone.base.i18nl10n import monthname_msgid_abbr
from plone.base.i18nl10n import ulocalized_time
from plone.restapi.interfaces import ISerializeToJsonSummary

import pytz


class EventCalendarBlockView(BaseBlockView):
    """Render the event calendar (event search) block."""

    default_limit = 50

    # -- block data -----------------------------------------------------------

    @property
    def headline(self):
        return (self.data or {}).get("headline") or ""

    @property
    def _limit(self):
        query = (self.data or {}).get("query") or {}
        for key in ("b_size", "limit"):
            try:
                return int(query.get(key))
            except (TypeError, ValueError):
                continue
        return self.default_limit

    # -- request-driven filter state -----------------------------------------

    def _param(self, name):
        value = self.request.form.get(name)
        return value.strip() if isinstance(value, str) else ""

    @property
    def from_value(self):
        return self._param("event_from")

    @property
    def to_value(self):
        return self._param("event_to")

    @property
    def search_text(self):
        return self._param("event_search")

    @property
    def has_filter(self):
        return bool(self.from_value or self.to_value or self.search_text)

    @property
    def form_action(self):
        return self.context.absolute_url()

    @property
    def block_url(self):
        """URL of this view for the AJAX live-filter fetch (JS appends params)."""
        return f"{self.context.absolute_url()}/@@block-eventCalendar"

    def _populate_from_request(self):
        """Fill ``data``/``block_id`` when rendered standalone (AJAX fetch).

        The block dispatcher normally sets these before rendering; on a direct
        request they are unset, so resolve the block from the context's blocks by
        ``block_id``, falling back to the first eventCalendar block on the page.
        """
        block_id = self.request.form.get("block_id") or ""
        blocks = getattr(self.context, "blocks", None) or {}
        data = blocks.get(block_id) if block_id else None
        if data is None:
            for bid, block in blocks.items():
                if isinstance(block, dict) and block.get("@type") == "eventCalendar":
                    block_id, data = bid, block
                    break
        self.block_id = block_id
        self.data = data or {}

    def __call__(self):
        if self.data is None:
            self._populate_from_request()
        return self.index()

    def _tz(self):
        try:
            return pytz.timezone(default_timezone(self.context) or "UTC")
        except Exception:
            return pytz.UTC

    def _parse_date(self, value, end_of_day=False):
        """Parse a ``YYYY-MM-DD`` form value into a tz-aware datetime, or None."""
        if not value:
            return None
        try:
            day = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
        moment = time(23, 59, 59) if end_of_day else time(0, 0, 0)
        return self._tz().localize(datetime.combine(day, moment))

    # -- query ----------------------------------------------------------------

    def _brains(self):
        start = self._parse_date(self.from_value)
        end = self._parse_date(self.to_value, end_of_day=True)
        kw = {}
        if self.search_text:
            kw["SearchableText"] = self.search_text
        return get_events(
            self.context,
            start=start,
            end=end,
            limit=self._limit,
            ret_mode=1,
            sort="start",
            **kw,
        )

    def _summaries(self):
        # The summary serializer reads requested metadata from the request form;
        # ask for ``_all`` so start/end/head_title/image_scales are included, then
        # restore the form so we don't leak state into the surrounding request.
        form = self.request.form
        saved = form.get("metadata_fields", None)
        form["metadata_fields"] = "_all"
        try:
            return [
                getMultiAdapter((brain, self.request), ISerializeToJsonSummary)()
                for brain in self._brains()
            ]
        finally:
            if saved is None:
                form.pop("metadata_fields", None)
            else:
                form["metadata_fields"] = saved

    # -- date helpers ---------------------------------------------------------

    @staticmethod
    def _parse_dt(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _month_abbr(self, month):
        msgid = monthname_msgid_abbr(month)
        text = translate(msgid, domain="plonelocales", context=self.request)
        if text == msgid:  # no translation registered -> English fallback
            text = monthname_english(month)[:3]
        return text

    def _localized_date(self, value):
        if value is None:
            return ""
        return ulocalized_time(
            value,
            long_format=False,
            context=self.context,
            request=self.request,
        )

    def _header_date(self, start, end):
        if start and end and start.date() != end.date():
            return f"{self._localized_date(start)} – {self._localized_date(end)}"
        return self._localized_date(start)

    # -- view model -----------------------------------------------------------

    def _event_model(self, item):
        start = self._parse_dt(item.get("start"))
        end = self._parse_dt(item.get("end"))
        multi_day = bool(start and end and start.date() != end.date())
        return {
            "url": _path(item.get("@id")),
            "title": item.get("title") or "",
            "description": item.get("description") or "",
            "head_title": item.get("head_title") or "",
            "header_date": self._header_date(start, end),
            "multi_day": multi_day,
            "start_day": f"{start.day:02d}" if start else "",
            "start_month": self._month_abbr(start.month) if start else "",
            "end_day": f"{end.day:02d}" if multi_day else "",
            "end_month": self._month_abbr(end.month) if multi_day else "",
            "image": _image_view_model(item),
        }

    @property
    def events(self):
        return [self._event_model(item) for item in self._summaries()]
