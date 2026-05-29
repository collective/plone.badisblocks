"""Tests for VideoBlockView view."""
import pytest
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewVideoBlockView:
    """Test VideoBlockView view."""

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

    def test_view_registered(self):
        """Test view is registered."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-video",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-video",
        )
        assert view.__name__ == "block-video"

    def _view(self, data):
        view = getMultiAdapter((self.context, TestRequest()), name="block-video")
        view.data = data
        return view

    def test_css_class_defaults_to_full(self):
        """Without an align setting the block is full width, like Volto."""
        assert self._view({}).css_class == "block video has--align--full"

    @pytest.mark.parametrize("align", ["left", "right", "center", "wide", "full"])
    def test_css_class_reflects_styles_align(self, align):
        """``styles.align`` from Volto becomes a has--align--<value> class."""
        view = self._view({"styles": {"align": align}})
        assert view.css_class == f"block video has--align--{align}"

    def test_css_class_falls_back_to_top_level_align(self):
        """Older data carries ``align`` at the top level rather than in styles."""
        assert self._view({"align": "center"}).css_class == (
            "block video has--align--center"
        )
