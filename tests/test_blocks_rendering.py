"""Integration tests for end-to-end block rendering via @@blocks-view."""

import pytest
from zope.component import getMultiAdapter

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


class TestBlocksRendering:
    """Render blocks set directly on the content object."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        self.request = integration["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.doc = api.content.create(
            container=self.portal,
            type="Document",
            id="doc",
            title="Hello World",
            description="A short summary",
        )

    def _render(self, blocks, items):
        self.doc.blocks = blocks
        self.doc.blocks_layout = {"items": items}
        view = getMultiAdapter((self.doc, self.request), name="blocks-view")
        return view.render()

    def test_title_block(self):
        html = self._render({"a": {"@type": "title"}}, ["a"])
        assert "Hello World" in html
        assert "documentFirstHeading" in html

    def test_description_block(self):
        html = self._render({"a": {"@type": "description"}}, ["a"])
        assert "A short summary" in html

    def test_slate_block(self):
        blocks = {
            "a": {
                "@type": "slate",
                "value": [
                    {
                        "type": "p",
                        "children": [
                            {"text": "Hello "},
                            {"type": "strong", "children": [{"text": "bold"}]},
                        ],
                    }
                ],
            }
        }
        html = self._render(blocks, ["a"])
        assert "<p>Hello <strong>bold</strong></p>" in html

    def test_unknown_block_falls_back_to_default(self):
        html = self._render({"a": {"@type": "nonexistent"}}, ["a"])
        assert 'data-block-type="nonexistent"' in html

    def test_image_block_builds_srcset(self):
        blocks = {
            "a": {
                "@type": "image",
                "alt": "Alt text",
                "url": "http://localhost:8080/Plone/img",
                "image_scales": {
                    "image": [
                        {
                            "download": "@@images/image-1200.png",
                            "width": 1200,
                            "height": 800,
                            "scales": {
                                "preview": {
                                    "download": "@@images/image-400.png",
                                    "width": 400,
                                }
                            },
                        }
                    ]
                },
            }
        }
        html = self._render(blocks, ["a"])
        assert "/Plone/img/@@images/image-1200.png" in html
        assert "/Plone/img/@@images/image-400.png 400w" in html
        assert 'alt="Alt text"' in html

    def test_image_block_real_data_shape(self):
        # Real Volto image block: empty alt, full url path, many named scales,
        # extra top-level keys (align/size/image_field/content-type).
        blocks = {
            "a": {
                "@type": "image",
                "align": "center",
                "alt": "",
                "size": "l",
                "image_field": "image",
                "url": "http://localhost:8080/Plone/badis-page-with-blocks/dsc06000_1.jpg",
                "image_scales": {
                    "image": [
                        {
                            "content-type": "image/jpeg",
                            "download": "@@images/image-6000-eac50fda.jpeg",
                            "filename": "DSC06000_1.JPG",
                            "width": 6000,
                            "height": 4000,
                            "scales": {
                                "great": {
                                    "download": "@@images/image-1200-a2d7990e.jpeg",
                                    "width": 1200,
                                    "height": 800,
                                },
                                "preview": {
                                    "download": "@@images/image-400-abc.jpeg",
                                    "width": 400,
                                    "height": 266,
                                },
                            },
                        }
                    ]
                },
            }
        }
        html = self._render(blocks, ["a"])
        assert "image-richtext" in html
        assert (
            "/Plone/badis-page-with-blocks/dsc06000_1.jpg/@@images/image-6000-eac50fda.jpeg" in html
        )
        assert "image-1200-a2d7990e.jpeg 1200w" in html

    def test_teaser_block_with_target(self):
        target = {
            "@id": "http://localhost:8080/Plone/some-target",
            "@type": "Document",
            "title": "Target Title",
            "description": "Target description",
            "image_field": "image",
            "image_scales": {
                "image": [
                    {
                        "download": "@@images/img.png",
                        "width": 800,
                        "height": 600,
                        "scales": {
                            "preview": {
                                "download": "@@images/img-400.png",
                                "width": 400,
                            }
                        },
                    }
                ]
            },
        }
        blocks = {
            "a": {
                "@type": "teaser",
                "overwrite": False,
                "href": [target],
                "styles": {"align": "right"},
            }
        }
        html = self._render(blocks, ["a"])
        assert 'href="/Plone/some-target"' in html
        assert "Target Title" in html
        assert "Target description" in html
        assert "/Plone/some-target/@@images/img.png" in html
        assert "/Plone/some-target/@@images/img-400.png 400w" in html
        assert "has--align--right" in html

    def test_teaser_overwrite_uses_block_fields(self):
        target = {"@id": "http://localhost:8080/Plone/t", "title": "Target Title"}
        blocks = {
            "a": {
                "@type": "teaser",
                "overwrite": True,
                "title": "Custom Title",
                "description": "Custom desc",
                "href": [target],
            }
        }
        html = self._render(blocks, ["a"])
        assert "Custom Title" in html
        assert "Custom desc" in html

    def test_teaser_without_target_renders_title_no_link(self):
        blocks = {
            "a": {
                "@type": "teaser",
                "overwrite": False,
                "href": [],
                "title": "another page",
            }
        }
        html = self._render(blocks, ["a"])
        assert "another page" in html
        assert "<a " not in html
        assert "block teaser" in html

    def test_grid_block_nests_children(self):
        blocks = {
            "g": {
                "@type": "gridBlock",
                "headline": "My grid",
                "blocks": {
                    "c1": {
                        "@type": "slate",
                        "value": [{"type": "p", "children": [{"text": "Col1"}]}],
                    },
                    "c2": {
                        "@type": "slate",
                        "value": [{"type": "p", "children": [{"text": "Col2"}]}],
                    },
                },
                "blocks_layout": {"items": ["c1", "c2"]},
            }
        }
        html = self._render(blocks, ["g"])
        assert "My grid" in html
        assert "Col1" in html
        assert "Col2" in html
        assert "row-cols-md-2" in html
        assert html.count("grid-column") == 2

    def test_blocks_render_in_layout_order(self):
        blocks = {
            "t": {"@type": "title"},
            "d": {"@type": "description"},
        }
        html = self._render(blocks, ["t", "d"])
        assert html.index("Hello World") < html.index("A short summary")

    def test_no_blocks_renders_empty(self):
        view = getMultiAdapter((self.doc, self.request), name="blocks-view")
        assert view.render() == ""

    def _make_listing_targets(self):
        for i in range(1, 4):
            api.content.create(
                container=self.portal,
                type="Document",
                id=f"listing-item-{i}",
                title=f"Listing Item {i}",
                description=f"Description {i}",
            )

    @staticmethod
    def _listing_query(portal_type="Document"):
        return {
            "query": [
                {
                    "i": "portal_type",
                    "o": "plone.app.querystring.operation.selection.any",
                    "v": [portal_type],
                }
            ],
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }

    def test_listing_block_default_variation(self):
        self._make_listing_targets()
        blocks = {
            "l": {
                "@type": "listing",
                "headline": "My Listing",
                "querystring": self._listing_query(),
            }
        }
        html = self._render(blocks, ["l"])
        assert "My Listing" in html
        assert "listing-items" in html
        assert "Listing Item 1" in html
        assert "Listing Item 3" in html
        assert "Description 2" in html
        assert 'href="/plone/listing-item-1"' in html.lower()

    def test_listing_block_summary_variation(self):
        self._make_listing_targets()
        blocks = {
            "l": {
                "@type": "listing",
                "variation": "summary",
                "querystring": self._listing_query(),
            }
        }
        html = self._render(blocks, ["l"])
        assert "variation-summary" in html
        assert "listing-summary" in html
        assert "listing-card" in html
        assert "Listing Item 1" in html

    def test_listing_block_no_results(self):
        blocks = {
            "l": {
                "@type": "listing",
                "querystring": self._listing_query(portal_type="Event"),
            }
        }
        html = self._render(blocks, ["l"])
        assert "No results found." in html

    def test_listing_block_link_more(self):
        self._make_listing_targets()
        blocks = {
            "l": {
                "@type": "listing",
                "querystring": self._listing_query(),
                "linkTitle": "See all",
                "linkHref": [{"@id": "http://localhost:8080/Plone/some-target"}],
            }
        }
        html = self._render(blocks, ["l"])
        assert "See all" in html
        assert 'href="/Plone/some-target"' in html

    def test_listing_block_no_query_lists_context_children(self):
        # With no querystring, Volto shows the context's contents; we list the
        # context's immediate children. Render with the portal as context.
        self._make_listing_targets()
        view = getMultiAdapter((self.portal, self.request), name="block-listing")
        view.data = {"@type": "listing"}
        view.block_id = "l"
        view.block_type = "listing"
        html = view()
        assert "Listing Item 1" in html
        assert "Listing Item 3" in html
        assert "No results found." not in html

    def test_listing_block_string_b_size(self):
        # Volto stores b_size as a string; it must not break result slicing.
        self._make_listing_targets()
        querystring = self._listing_query()
        querystring["b_size"] = "30"
        blocks = {"l": {"@type": "listing", "querystring": querystring}}
        html = self._render(blocks, ["l"])
        assert "Listing Item 1" in html
        assert "No results found." not in html

    def test_listing_block_headline_tag_h3(self):
        self._make_listing_targets()
        blocks = {
            "l": {
                "@type": "listing",
                "headline": "Tagged",
                "headlineTag": "h3",
                "querystring": self._listing_query(),
            }
        }
        html = self._render(blocks, ["l"])
        assert "<h3" in html
        assert "Tagged" in html
