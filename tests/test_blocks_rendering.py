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

    def test_introduction_block(self):
        blocks = {
            "a": {
                "@type": "introduction",
                "value": [
                    {
                        "type": "p",
                        "children": [
                            {"text": "Intro "},
                            {"type": "em", "children": [{"text": "lead"}]},
                        ],
                    }
                ],
            }
        }
        html = self._render(blocks, ["a"])
        assert "block introduction" in html
        assert "<p>Intro <em>lead</em></p>" in html

    def test_html_block(self):
        blocks = {
            "a": {
                "@type": "html",
                "html": "<aside>Raw <b>markup</b></aside>",
                "styles": {"align": "center"},
            }
        }
        html = self._render(blocks, ["a"])
        assert "<aside>Raw <b>markup</b></aside>" in html
        assert "has--align--center" in html

    def test_html_block_empty_renders_nothing(self):
        html = self._render({"a": {"@type": "html", "html": "   "}}, ["a"])
        assert "<div" not in html

    def test_slate_table_block(self):
        def cell(text):
            return {"value": [{"type": "p", "children": [{"text": text}]}]}

        blocks = {
            "a": {
                "@type": "slateTable",
                "table": {
                    "striped": True,
                    "rows": [
                        {"cells": [cell("Name"), cell("Role")]},
                        {"cells": [cell("Ada"), cell("Engineer")]},
                        {"cells": [cell("Bob"), cell("Designer")]},
                    ],
                },
            }
        }
        html = self._render(blocks, ["a"])
        assert "block slateTable" in html
        assert "slateTable--striped" in html
        assert "<th scope=\"col\"><p>Name</p></th>" in html
        assert "<td><p>Ada</p></td>" in html
        assert "<td><p>Designer</p></td>" in html
        # First row is the header, not a body row.
        assert html.index("<thead") < html.index("<tbody")

    def test_slate_table_block_hide_headers(self):
        def cell(text):
            return {"value": [{"type": "p", "children": [{"text": text}]}]}

        blocks = {
            "a": {
                "@type": "slateTable",
                "table": {
                    "hideHeaders": True,
                    "rows": [
                        {"cells": [cell("H1")]},
                        {"cells": [cell("R1")]},
                    ],
                },
            }
        }
        html = self._render(blocks, ["a"])
        assert "<thead" not in html
        assert "R1" in html

    def test_slate_heading_gets_anchor_id(self):
        blocks = {
            "h": {
                "@type": "slate",
                "value": [{"type": "h2", "children": [{"text": "My Section"}]}],
            }
        }
        html = self._render(blocks, ["h"])
        assert '<h2 id="h-my-section">My Section</h2>' in html

    def test_toc_block_links_to_slate_headings(self):
        blocks = {
            "h1b": {
                "@type": "slate",
                "value": [{"type": "h2", "children": [{"text": "First Section"}]}],
            },
            "txt": {
                "@type": "slate",
                "value": [{"type": "p", "children": [{"text": "body"}]}],
            },
            "h2b": {
                "@type": "slate",
                "value": [{"type": "h3", "children": [{"text": "Sub Section"}]}],
            },
            "toc": {"@type": "toc", "title": "Contents"},
        }
        html = self._render(blocks, ["toc", "h1b", "txt", "h2b"])
        # Title shown, links target the anchors the slate renderer emits.
        assert "Contents" in html
        assert 'href="#h1b-first-section"' in html
        assert 'href="#h2b-sub-section"' in html
        assert "toc-level-2" in html
        assert "toc-level-3" in html
        # Anchor targets actually exist in the rendered page.
        assert 'id="h1b-first-section"' in html
        assert 'id="h2b-sub-section"' in html
        # The paragraph is not a heading and is excluded.
        assert "toc-level-1" not in html

    def test_toc_block_empty_when_no_headings(self):
        blocks = {
            "txt": {
                "@type": "slate",
                "value": [{"type": "p", "children": [{"text": "no headings"}]}],
            },
            "toc": {"@type": "toc"},
        }
        html = self._render(blocks, ["toc", "txt"])
        assert "No headings found on this page." in html

    def test_video_block_youtube(self):
        blocks = {
            "v": {
                "@type": "video",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "align": "center",
            }
        }
        html = self._render(blocks, ["v"])
        assert "block video has--align--center" in html
        assert 'src="https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"' in html
        assert "<iframe" in html
        assert 'title="youtube video player"' in html

    def test_video_block_vimeo(self):
        blocks = {"v": {"@type": "video", "url": "https://vimeo.com/123456789"}}
        html = self._render(blocks, ["v"])
        assert 'src="https://player.vimeo.com/video/123456789"' in html
        assert "has--align--full" in html

    def test_video_block_self_hosted(self):
        blocks = {
            "v": {
                "@type": "video",
                "url": "https://example.com/clip.mp4",
                "preview_image": "https://example.com/poster.jpg",
                "styles": {"align": "left"},
            }
        }
        html = self._render(blocks, ["v"])
        assert "<video" in html
        assert 'src="https://example.com/clip.mp4"' in html
        assert 'poster="https://example.com/poster.jpg"' in html
        assert "has--align--left" in html
        assert "<iframe" not in html

    def test_video_block_empty_url_renders_no_media(self):
        html = self._render({"v": {"@type": "video"}}, ["v"])
        assert "<iframe" not in html
        assert "<video" not in html
        assert "block video" in html

    def test_maps_block(self):
        blocks = {
            "m": {
                "@type": "maps",
                "url": "https://www.google.com/maps/embed?pb=!1m18",
                "title": "Office Location",
                "align": "center",
            }
        }
        html = self._render(blocks, ["m"])
        assert "block maps has--align--center" in html
        assert 'src="https://www.google.com/maps/embed?pb=!1m18"' in html
        assert 'title="Office Location"' in html
        assert 'loading="lazy"' in html
        assert 'href="#after-map-m"' in html
        assert 'id="after-map-m"' in html

    def test_maps_block_rejects_unsafe_url(self):
        blocks = {"m": {"@type": "maps", "url": "javascript:alert(1)"}}
        html = self._render(blocks, ["m"])
        assert "<iframe" not in html
        assert "javascript" not in html
        assert "block maps" in html

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
        # volto-light-theme markup: ul.items > li.listing-item, title is a
        # div.title with a card-primary-link (not a heading).
        assert 'class="items"' in html
        assert "listing-item document-listing" in html
        assert '<div class="title">' in html
        assert "card-primary-link" in html
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
        # Summary items carry has--align--left and the shared card markup.
        assert "listing-item has--align--left" in html
        assert 'class="card"' in html
        assert 'class="card-summary"' in html
        assert "card-primary-link" in html
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
