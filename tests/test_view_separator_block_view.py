"""Tests for SeparatorBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewSeparatorBlockView:
    """Test SeparatorBlockView view."""

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
        view = getMultiAdapter((self.context, TestRequest()), name="block-separator")
        view.data = data
        return view

    def test_view_registered(self):
        view = getMultiAdapter((self.context, TestRequest()), name="block-separator")
        assert view is not None

    def test_view_name(self):
        view = getMultiAdapter((self.context, TestRequest()), name="block-separator")
        assert view.__name__ == "block-separator"

    def test_plain_separator_css_class(self):
        view = self._view({"@type": "separator"})
        assert view.css_class == "block separator"

    def test_short_line_class(self):
        view = self._view({"@type": "separator", "styles": {"shortLine": True}})
        assert "has--shortLine--true" in view.css_class

    def test_align_and_block_width_classes(self):
        view = self._view(
            {
                "@type": "separator",
                "styles": {"align": "center", "blockWidth": "narrow"},
            }
        )
        assert "has--align--center" in view.css_class
        assert "has--blockWidth--narrow" in view.css_class

    def test_renders_line(self):
        view = self._view({"@type": "separator"})
        html = view()
        assert '<div class="line">' in html
        assert "block separator" in html
