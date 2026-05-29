"""Tests for ButtonBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewButtonBlockView:
    """Test ButtonBlockView view."""

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
        view = getMultiAdapter((self.context, TestRequest()), name="block-__button")
        view.data = data
        return view

    def test_view_registered(self):
        """Test view is registered."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-__button",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-__button",
        )
        assert view.__name__ == "block-__button"

    def test_href_stripped_to_path(self):
        view = self._view(
            {
                "@type": "__button",
                "title": "Read more",
                "href": [{"@id": "http://nohost/plone/target-page"}],
            }
        )
        assert view.href == "/plone/target-page"
        assert view.text == "Read more"

    def test_no_href_is_empty(self):
        view = self._view({"@type": "__button", "title": "Read more"})
        assert view.href == ""

    def test_new_tab_sets_target_and_rel(self):
        view = self._view(
            {
                "@type": "__button",
                "title": "x",
                "href": [{"@id": "http://nohost/plone/t"}],
                "openLinkInNewTab": True,
            }
        )
        assert view.target == "_blank"
        assert view.rel == "noopener noreferrer"

    def test_align_prefers_styles_then_inneralign(self):
        assert self._view({"@type": "__button"}).align == "left"
        assert self._view({"@type": "__button", "inneralign": "right"}).align == "right"
        assert (
            self._view(
                {"@type": "__button", "inneralign": "right", "styles": {"align": "center"}}
            ).align
            == "center"
        )
