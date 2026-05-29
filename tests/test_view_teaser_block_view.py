"""Tests for TeaserBlockView view."""
import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewTeaserBlockView:
    """Test TeaserBlockView view."""

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
            name="block-teaser",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-teaser",
        )
        assert view.__name__ == "block-teaser"

    def _view(self, data):
        view = getMultiAdapter((self.context, TestRequest()), name="block-teaser")
        view.data = data
        return view

    def test_image_base_path_readds_portal_prefix(self):
        """plone.volto strips the site id from preview_image base_path; re-add it."""
        portal_path = "/".join(self.portal.getPhysicalPath())
        view = self._view(
            {
                "@type": "teaser",
                # base_path as produced by plone.volto: navigation-root relative,
                # i.e. with the portal/site-id prefix stripped off.
                "preview_image": [
                    {
                        "base_path": "/an-image.jpg",
                        "download": "@@images/image-600.jpeg",
                        "scales": {},
                    }
                ],
            }
        )
        assert view.image_base_path == f"{portal_path}/an-image.jpg"
        assert view.image_src == f"{portal_path}/an-image.jpg/@@images/image-600.jpeg"

    def test_image_base_path_from_target_id_unchanged(self):
        """Without a preview base_path, fall back to the target @id path."""
        portal_path = "/".join(self.portal.getPhysicalPath())
        view = self._view(
            {
                "@type": "teaser",
                "href": [
                    {
                        "@id": f"http://nohost{portal_path}/target-page",
                        "image_field": "image",
                        "image_scales": {
                            "image": [{"download": "@@images/image-600.jpeg", "scales": {}}]
                        },
                    }
                ],
            }
        )
        assert view.image_base_path == f"{portal_path}/target-page"
