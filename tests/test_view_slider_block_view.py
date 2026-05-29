"""Tests for SliderBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestViewSliderBlockView:
    """Test SliderBlockView view."""

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
        view = getMultiAdapter((self.context, TestRequest()), name="block-slider")
        view.data = data
        return view

    def test_view_registered(self):
        """Test view is registered."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-slider",
        )
        assert view is not None

    def test_view_name(self):
        """Test view __name__."""
        request = TestRequest()
        view = getMultiAdapter(
            (self.context, request),
            name="block-slider",
        )
        assert view.__name__ == "block-slider"

    def test_no_slides_is_empty(self):
        view = self._view({"@type": "slider"})
        assert view.slides == []
        assert view.slide_count == 0

    def test_slide_falls_back_to_target_fields(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    {
                        "href": [
                            {
                                "@id": "http://nohost/plone/target",
                                "title": "Target Title",
                                "description": "Target description",
                            }
                        ]
                    }
                ],
            }
        )
        slide = view.slides[0]
        assert slide["title"] == "Target Title"
        assert slide["description"] == "Target description"
        assert slide["href"] == "/plone/target"
        # default call-to-action, shown unless hideButton
        assert slide["show_button"] is True
        assert slide["button_text"] == "Continue reading"
        assert slide["flag_align"] == "left"

    def test_slide_overrides_and_extras(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    {
                        "href": [{"@id": "http://nohost/plone/t", "title": "T"}],
                        "head_title": "Kicker",
                        "title": "Custom",
                        "description": "Custom desc",
                        "buttonText": "Learn more",
                        "hideButton": True,
                        "flagAlign": "right",
                        "openLinkInNewTab": True,
                    }
                ],
            }
        )
        slide = view.slides[0]
        assert slide["head_title"] == "Kicker"
        assert slide["title"] == "Custom"
        assert slide["description"] == "Custom desc"
        assert slide["show_button"] is False
        assert slide["button_text"] == "Learn more"
        assert slide["flag_align"] == "right"
        assert slide["target"] == "_blank"
        assert slide["rel"] == "noopener noreferrer"
