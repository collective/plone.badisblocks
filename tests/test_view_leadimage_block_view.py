"""Tests for LeadImageBlockView view."""

import base64

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING
from plone.namedfile.file import NamedBlobImage


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class TestViewLeadImageBlockView:
    """Test LeadImageBlockView view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        # The real Plone request supports request.set()/scaling, unlike the
        # zope.publisher TestRequest.
        self.request = integration["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.news = api.content.create(
            container=self.portal,
            type="News Item",
            id="a-news-item",
            title="A News Item",
        )
        self.news.image = NamedBlobImage(data=PNG, filename="lead.png")
        self.news.reindexObject()
        # A context without an image field/value.
        self.doc = api.content.create(
            container=self.portal,
            type="Document",
            id="a-doc",
            title="A Doc",
        )

    def _view(self, context, data):
        view = getMultiAdapter((context, self.request), name="block-leadimage")
        view.data = data
        return view

    def test_view_registered(self):
        view = getMultiAdapter((self.news, TestRequest()), name="block-leadimage")
        assert view is not None

    def test_view_name(self):
        view = getMultiAdapter((self.news, TestRequest()), name="block-leadimage")
        assert view.__name__ == "block-leadimage"

    def test_has_image_true_when_context_has_image(self):
        view = self._view(self.news, {"@type": "leadimage"})
        assert view.has_image is True

    def test_has_image_false_without_image(self):
        view = self._view(self.doc, {"@type": "leadimage"})
        assert view.has_image is False

    def test_default_align_is_center(self):
        view = self._view(self.news, {"@type": "leadimage"})
        assert view.align == "center"
        assert view.css_class == "block image align center"

    def test_align_full_sets_image_css_class(self):
        view = self._view(self.news, {"@type": "leadimage", "align": "full"})
        assert view.css_class == "block image align full"
        assert view.image_css_class == "full-width"

    def test_href_stripped_to_path(self):
        view = self._view(
            self.news,
            {"@type": "leadimage", "href": "http://nohost/plone/target"},
        )
        assert view.href == "/plone/target"

    def test_new_tab_sets_target_and_rel(self):
        view = self._view(
            self.news,
            {"@type": "leadimage", "href": "/plone/t", "openLinkInNewTab": True},
        )
        assert view.target == "_blank"
        assert view.rel == "noopener noreferrer"

    def test_image_tag_renders_img(self):
        view = self._view(self.news, {"@type": "leadimage"})
        tag = view.image_tag()
        assert "<img" in tag
        assert "/a-news-item/@@images/image" in tag

    def test_renders_full_block(self):
        view = self._view(self.news, {"@type": "leadimage", "align": "center"})
        html = view()
        assert "block image align center" in html
        assert "<img" in html

    def test_renders_linked_image(self):
        view = self._view(
            self.news, {"@type": "leadimage", "href": "http://nohost/plone/target"}
        )
        html = view()
        assert 'href="/plone/target"' in html
        assert "<img" in html

    def test_no_image_renders_nothing(self):
        view = self._view(self.doc, {"@type": "leadimage"})
        assert view().strip() == ""
