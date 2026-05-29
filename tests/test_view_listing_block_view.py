"""Tests for ListingBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewListingBlockView:
    """Test ListingBlockView view."""

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
            name="block-listing",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-listing",
        )
        assert view.__name__ == "block-listing"


class TestImageViewModel:
    """Unit tests for the summary card image view model."""

    def _item(self, scales):
        return {
            "@id": "http://localhost:8080/Plone/some-item",
            "title": "Some item",
            "image_field": "image",
            "image_scales": {
                "image": [
                    {
                        "download": "@@images/image-6000.jpeg",
                        "width": 6000,
                        "height": 4000,
                        "scales": scales,
                    }
                ]
            },
        }

    def test_src_uses_small_preview_scale_not_original(self):
        """The card src/size must be a small scale, never the 6000px original."""
        from plone.badisblocks.views.listing_block_view import _image_view_model

        model = _image_view_model(
            self._item(
                {
                    "great": {"download": "@@images/image-1200.jpeg", "width": 1200, "height": 800},
                    "preview": {"download": "@@images/image-400.jpeg", "width": 400, "height": 266},
                }
            )
        )
        assert model["src"] == "/Plone/some-item/@@images/image-400.jpeg"
        assert model["width"] == 400
        assert model["height"] == 266
        assert model["sizes"]
        # srcset still offers every scale for responsive selection.
        assert "image-1200.jpeg 1200w" in model["srcset"]
        assert "image-400.jpeg 400w" in model["srcset"]

    def test_falls_back_to_smallest_scale_when_no_preferred_name(self):
        from plone.badisblocks.views.listing_block_view import _image_view_model

        model = _image_view_model(
            self._item(
                {
                    "huge": {"download": "@@images/image-2000.jpeg", "width": 2000, "height": 1333},
                    "small": {"download": "@@images/image-300.jpeg", "width": 300, "height": 200},
                }
            )
        )
        assert model["src"] == "/Plone/some-item/@@images/image-300.jpeg"
        assert model["width"] == 300

    def test_falls_back_to_original_when_no_named_scales(self):
        from plone.badisblocks.views.listing_block_view import _image_view_model

        model = _image_view_model(self._item({}))
        assert model["src"] == "/Plone/some-item/@@images/image-6000.jpeg"
        assert model["width"] == 6000

    def test_returns_none_without_usable_image(self):
        from plone.badisblocks.views.listing_block_view import _image_view_model

        assert _image_view_model({"@id": "http://x/y", "title": "t"}) is None
