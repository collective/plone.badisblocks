"""Tests for HeadingBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewHeadingBlockView:
    """Test HeadingBlockView view."""

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
        view = getMultiAdapter((self.context, TestRequest()), name="block-heading")
        view.data = data
        return view

    def test_view_registered(self):
        view = getMultiAdapter((self.context, TestRequest()), name="block-heading")
        assert view is not None

    def test_view_name(self):
        view = getMultiAdapter((self.context, TestRequest()), name="block-heading")
        assert view.__name__ == "block-heading"

    def test_default_tag_is_h2(self):
        view = self._view({"@type": "heading", "heading": "Hello"})
        assert view.tag == "h2"
        assert view.text == "Hello"

    def test_unknown_tag_falls_back_to_h2(self):
        view = self._view({"@type": "heading", "heading": "x", "tag": "span"})
        assert view.tag == "h2"

    def test_h3_tag_respected(self):
        view = self._view({"@type": "heading", "heading": "x", "tag": "h3"})
        assert view.tag == "h3"

    def test_anchor_id_is_slug(self):
        view = self._view({"@type": "heading", "heading": "Hello World"})
        assert view.anchor_id == "hello-world"

    def test_align_class(self):
        view = self._view(
            {"@type": "heading", "heading": "x", "styles": {"align": "center"}}
        )
        assert "has--align--center" in view.css_class

    def test_renders_heading_with_id(self):
        view = self._view({"@type": "heading", "heading": "My Title", "tag": "h2"})
        html = view()
        assert "block heading block-heading-h2" in html
        assert 'id="my-title"' in html
        assert "My Title" in html

    def test_empty_heading_renders_nothing(self):
        view = self._view({"@type": "heading", "heading": ""})
        assert view().strip() == ""
