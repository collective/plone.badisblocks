"""Tests for EventCalendarBlockView view."""

from datetime import datetime

import pytest
from zope.component import getMultiAdapter

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewEventCalendarBlockView:
    """Test EventCalendarBlockView view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        self.request = integration["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self._make_event("past-event", datetime(2026, 1, 10, 10, 0), datetime(2026, 1, 10, 12, 0))
        self._make_event("june-event", datetime(2026, 6, 15, 10, 0), datetime(2026, 6, 15, 12, 0))
        self._make_event("july-event", datetime(2026, 7, 20, 10, 0), datetime(2026, 7, 22, 12, 0))

    def _make_event(self, eid, start, end):
        return api.content.create(
            container=self.portal, type="Event", id=eid, title=eid, start=start, end=end
        )

    def _reset_form(self):
        # Reset any params left on the shared layer request between calls.
        for key in ("event_from", "event_to", "event_search", "block_id"):
            self.request.form.pop(key, None)

    def _view(self, form=None):
        self._reset_form()
        self.request.form.update(form or {})
        view = getMultiAdapter((self.portal, self.request), name="block-eventCalendar")
        view.data = {"@type": "eventCalendar", "headline": "Our Events"}
        return view

    def test_view_registered(self):
        assert self._view() is not None

    def test_view_name(self):
        assert self._view().__name__ == "block-eventCalendar"

    def test_lists_all_events_by_default(self):
        titles = {e["title"] for e in self._view().events}
        assert {"past-event", "june-event", "july-event"} <= titles

    def test_events_sorted_by_start(self):
        titles = [e["title"] for e in self._view().events]
        assert titles.index("past-event") < titles.index("june-event")
        assert titles.index("june-event") < titles.index("july-event")

    def test_filter_from_date(self):
        titles = {e["title"] for e in self._view({"event_from": "2026-06-01"}).events}
        assert "past-event" not in titles
        assert {"june-event", "july-event"} <= titles

    def test_filter_to_date(self):
        titles = {e["title"] for e in self._view({"event_to": "2026-06-30"}).events}
        assert "july-event" not in titles
        assert {"past-event", "june-event"} <= titles

    def test_filter_range(self):
        titles = {
            e["title"]
            for e in self._view({"event_from": "2026-06-01", "event_to": "2026-06-30"}).events
        }
        assert titles == {"june-event"}

    def test_search_text_filters(self):
        titles = {e["title"] for e in self._view({"event_search": "july-event"}).events}
        assert titles == {"july-event"}

    def test_has_filter_flag(self):
        assert self._view().has_filter is False
        assert self._view({"event_from": "2026-06-01"}).has_filter is True

    def test_multi_day_inset(self):
        july = next(e for e in self._view().events if e["title"] == "july-event")
        single = next(e for e in self._view().events if e["title"] == "june-event")
        assert july["multi_day"] is True
        assert july["end_day"] == "22"
        assert single["multi_day"] is False
        assert single["start_day"] == "15"

    def test_renders_html(self):
        html = self._view().index()
        assert "block eventCalendar" in html
        assert "Our Events" in html
        assert 'type="date"' in html
        assert "june-event" in html
        # AJAX hooks for the live-filter JS.
        assert "data-event-calendar" in html
        assert "data-block-url" in html
        assert 'class="event-calendar-results"' in html

    def test_block_url(self):
        assert self._view().block_url.endswith("/@@block-eventCalendar")

    def test_standalone_call_populates_data_from_block_id(self):
        # Simulates the AJAX fetch: the dispatcher hasn't set ``data``; the view
        # resolves its block from the context's blocks via the ``block_id`` param.
        doc = api.content.create(
            container=self.portal, type="Document", id="cal-page", title="Cal"
        )
        doc.blocks = {"abc": {"@type": "eventCalendar", "headline": "Standalone Events"}}
        self._reset_form()
        self.request.form["block_id"] = "abc"
        view = getMultiAdapter((doc, self.request), name="block-eventCalendar")
        assert view.data is None
        html = view()  # __call__ self-populates from block_id
        assert "Standalone Events" in html
        assert view.block_id == "abc"
        self._reset_form()

    def test_standalone_call_falls_back_to_first_event_calendar_block(self):
        doc = api.content.create(
            container=self.portal, type="Document", id="cal-page2", title="Cal2"
        )
        doc.blocks = {
            "t1": {"@type": "title"},
            "ec": {"@type": "eventCalendar", "headline": "Fallback Events"},
        }
        self._reset_form()
        view = getMultiAdapter((doc, self.request), name="block-eventCalendar")
        html = view()
        assert "Fallback Events" in html
        assert view.block_id == "ec"
        self._reset_form()
