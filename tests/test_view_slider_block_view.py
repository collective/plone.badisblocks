"""Tests for SliderBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


def _slide(**kw):
    slide = {"@id": "slide-1"}
    slide.update(kw)
    return slide


def _preview_image(field="image"):
    """A serialized ``preview_image`` value (UID resolved + image_scales)."""
    return [
        {
            "@id": "http://nohost/plone/img1",
            "image_scales": {
                field: [
                    {
                        "download": "@@images/image-1-abc.png",
                        "width": 1600,
                        "height": 900,
                        "scales": {
                            "great": {
                                "download": "@@images/image-great-xyz.png",
                                "width": 1200,
                            },
                        },
                    }
                ]
            },
        }
    ]


def _href_with_image(url, field="image", base_path=None):
    """A serialized ``href`` target carrying an image (summary shape)."""
    img = {
        "download": "@@images/image-6000-def.jpeg",
        "width": 6000,
        "height": 4000,
        "scales": {
            "great": {"download": "@@images/image-1200-ghi.jpeg", "width": 1200},
        },
    }
    if base_path:
        img["base_path"] = base_path
    return [
        {
            "@id": url,
            "Title": "Target",
            "image_field": field,
            "image_scales": {field: [img]},
        }
    ]


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
        view = getMultiAdapter((self.context, TestRequest()), name="block-slider")
        assert view is not None

    def test_view_name(self):
        view = getMultiAdapter((self.context, TestRequest()), name="block-slider")
        assert view.__name__ == "block-slider"

    def test_slide_count(self):
        view = self._view({"@type": "slider", "slides": [_slide(), _slide()]})
        assert view.slide_count == 2

    def test_href_stripped_to_path(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(
                        title="One",
                        href=[{"@id": "http://nohost/plone/target"}],
                    )
                ],
            }
        )
        slide = view.slides[0]
        assert slide["href"] == "/plone/target"
        assert slide["title"] == "One"

    def test_nav_title_preferred_over_title(self):
        view = self._view(
            {"@type": "slider", "slides": [_slide(title="T", nav_title="Nav")]}
        )
        assert view.slides[0]["title"] == "Nav"

    def test_head_title_and_description(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [_slide(title="T", head_title="Kicker", description="Desc")],
            }
        )
        slide = view.slides[0]
        assert slide["head_title"] == "Kicker"
        assert slide["description"] == "Desc"

    def test_new_tab_sets_target_and_rel(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(
                        title="T",
                        href=[{"@id": "http://nohost/plone/t"}],
                        openLinkInNewTab=True,
                    )
                ],
            }
        )
        slide = view.slides[0]
        assert slide["target"] == "_blank"
        assert slide["rel"] == "noopener noreferrer"

    def test_no_new_tab_has_no_target(self):
        view = self._view(
            {"@type": "slider", "slides": [_slide(title="T", href=[{"@id": "http://nohost/plone/t"}])]}
        )
        slide = view.slides[0]
        assert slide["target"] is None
        assert slide["rel"] is None

    def test_image_from_preview_image(self):
        view = self._view(
            {"@type": "slider", "slides": [_slide(title="T", preview_image=_preview_image())]}
        )
        image = view.slides[0]["image"]
        assert image is not None
        assert image["src"] == "/plone/img1/@@images/image-1-abc.png"
        assert image["width"] == 1600
        assert "/plone/img1/@@images/image-great-xyz.png 1200w" in image["srcset"]
        assert image["alt"] == "T"

    def test_image_from_href_target(self):
        # The common case: no preview_image override, image comes from the href
        # target's image_field/image_scales (with no base_path -> use @id path).
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(
                        title="T",
                        href=_href_with_image("http://nohost/plone/an-image"),
                    )
                ],
            }
        )
        image = view.slides[0]["image"]
        assert image is not None
        assert image["src"] == "/plone/an-image/@@images/image-6000-def.jpeg"
        assert "/plone/an-image/@@images/image-1200-ghi.jpeg 1200w" in image["srcset"]

    def test_image_base_path_gets_site_prefix(self):
        # When the target image carries a base_path (navigation-root relative),
        # it is re-prefixed with the site id for Classic UI.
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(
                        title="T",
                        href=_href_with_image(
                            "http://nohost/plone/another-page",
                            field="preview_image_link",
                            base_path="/some-folder/the-image.jpg",
                        ),
                    )
                ],
            }
        )
        image = view.slides[0]["image"]
        assert image["src"] == "/plone/some-folder/the-image.jpg/@@images/image-6000-def.jpeg"

    def test_preview_image_overrides_href(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(
                        title="T",
                        preview_image=_preview_image(),
                        href=_href_with_image("http://nohost/plone/an-image"),
                    )
                ],
            }
        )
        # preview_image wins over the href target image.
        assert view.slides[0]["image"]["src"] == "/plone/img1/@@images/image-1-abc.png"

    def test_no_image_when_no_preview_and_no_target_image(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [_slide(title="T", href=[{"@id": "http://nohost/plone/plain"}])],
            }
        )
        assert view.slides[0]["image"] is None

    def test_renders_slider_markup(self):
        view = self._view(
            {
                "@type": "slider",
                "slides": [
                    _slide(title="First", href=[{"@id": "http://nohost/plone/a"}]),
                    _slide(title="Second", href=[{"@id": "http://nohost/plone/b"}]),
                ],
            }
        )
        html = view()
        assert "block slider" in html
        assert "slider-viewport" in html
        assert html.count('class="slider-slide"') == 2
        assert "slider-dot" in html  # >1 slide -> dots rendered
        assert 'href="/plone/a"' in html

    def test_single_slide_has_no_dots_or_arrows(self):
        view = self._view(
            {"@type": "slider", "slides": [_slide(title="Only", href=[{"@id": "http://nohost/plone/a"}])]}
        )
        html = view()
        assert "slider-slide" in html
        assert "slider-dot" not in html
        assert "slider-button" not in html

    def test_empty_slides_renders_no_wrapper(self):
        view = self._view({"@type": "slider", "slides": []})
        html = view()
        assert "slider-wrapper" not in html
