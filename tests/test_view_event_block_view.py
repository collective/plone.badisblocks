"""Tests for EventBlockView view."""

from datetime import datetime

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewEventBlockView:
    """Test EventBlockView view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.event = api.content.create(
            container=self.portal,
            type="Event",
            id="test-event",
            title="Test Event",
            start=datetime(2026, 6, 1, 10, 0),
            end=datetime(2026, 6, 1, 12, 0),
            location="Karlsruhe",
            event_url="https://example.org/event",
            contact_name="Jane Doe",
            contact_email="jane@example.org",
            contact_phone="+49 123",
        )
        self.document = api.content.create(
            container=self.portal,
            type="Document",
            id="test-document",
            title="Test Document",
        )

    def _view(self, context):
        return getMultiAdapter((context, TestRequest()), name="block-eventMetadata")

    def test_view_registered(self):
        """Test view is registered."""
        view = self._view(self.event)
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        view = self._view(self.event)
        assert view.__name__ == "block-eventMetadata"

    def test_reads_event_fields(self):
        view = self._view(self.event)
        assert view.available is True
        assert view.location == "Karlsruhe"
        assert view.event_url == "https://example.org/event"
        assert view.contact_name == "Jane Doe"
        assert view.contact_email == "jane@example.org"
        assert view.contact_phone == "+49 123"
        assert view.has_contact is True

    def test_start_and_end_formatted(self):
        view = self._view(self.event)
        assert view.start
        assert view.show_end is True
        assert view.end

    def test_ics_url(self):
        view = self._view(self.event)
        assert view.ics_url.endswith("/test-event/ics_view")

    def test_open_end_hides_end(self):
        self.event.open_end = True
        view = self._view(self.event)
        assert view.show_end is False

    def test_renders_html_for_event(self):
        view = self._view(self.event)
        html = view()
        assert "block eventMetadata" in html
        assert "Karlsruhe" in html
        assert "ics_view" in html
        assert "mailto:jane@example.org" in html

    def test_renders_empty_on_non_event(self):
        view = self._view(self.document)
        assert view.available is False
        assert view() == ""
