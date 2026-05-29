"""Tests for CarouselBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewCarouselBlockView:
    """Test CarouselBlockView view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.context = api.content.create(
            container=self.portal,
            type="Document",
            id="test-document",
            title="Test Document",
        )

    def _view(self, data):
        view = getMultiAdapter((self.context, TestRequest()), name="block-carousel")
        view.data = data
        return view

    def test_view_registered(self):
        """Test view is registered."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-carousel",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-carousel",
        )
        assert view.__name__ == "block-carousel"

    def test_items_to_show_defaults_and_coerces(self):
        assert self._view({"@type": "carousel"}).items_to_show == 3
        # Volto may store it as a string; coerce, and ignore non-positive values.
        assert self._view({"@type": "carousel", "items_to_show": "4"}).items_to_show == 4
        assert self._view({"@type": "carousel", "items_to_show": 0}).items_to_show == 3

    def test_track_style_carries_item_count(self):
        view = self._view({"@type": "carousel", "items_to_show": 4})
        assert view.track_style == "--bb-carousel-items: 4"

    def test_columns_without_ids_are_skipped(self):
        view = self._view({"@type": "carousel", "columns": [{"@type": "teaser"}]})
        assert view.columns == []
        assert view.column_count == 0

    def test_column_count_counts_only_columns_with_ids(self):
        view = self._view(
            {
                "@type": "carousel",
                "columns": [
                    {"@id": "u1", "@type": "teaser"},
                    {"@type": "teaser"},
                    {"@id": "u2", "@type": "teaser"},
                ],
            }
        )
        assert view.column_count == 2
