"""Unit tests for the slate -> HTML serializer (no Plone layer needed)."""

from plone.badisblocks.views.slate import render_nodes


class TestSlateSerializer:
    """Test slate node-tree serialization."""

    def test_empty(self):
        assert render_nodes(None) == ""
        assert render_nodes([]) == ""

    def test_text_is_escaped(self):
        nodes = [{"text": "a < b & c > d"}]
        assert render_nodes(nodes) == "a &lt; b &amp; c &gt; d"

    def test_paragraph_with_inline_formatting(self):
        nodes = [
            {
                "type": "p",
                "children": [
                    {"text": "Hello "},
                    {"type": "strong", "children": [{"text": "bold"}]},
                    {"text": " and "},
                    {"type": "em", "children": [{"text": "italic"}]},
                ],
            }
        ]
        assert render_nodes(nodes) == "<p>Hello <strong>bold</strong> and <em>italic</em></p>"

    def test_lists(self):
        nodes = [
            {
                "type": "ul",
                "children": [
                    {"type": "li", "children": [{"text": "one"}]},
                    {"type": "li", "children": [{"text": "two"}]},
                ],
            }
        ]
        assert render_nodes(nodes) == "<ul><li>one</li><li>two</li></ul>"

    def test_link_renders_href(self):
        nodes = [
            {
                "type": "link",
                "data": {"url": "https://example.org/page"},
                "children": [{"text": "link"}],
            }
        ]
        assert render_nodes(nodes) == '<a href="https://example.org/page">link</a>'

    def test_link_href_is_escaped(self):
        nodes = [
            {
                "type": "link",
                "data": {"url": '"><script>alert(1)</script>'},
                "children": [{"text": "x"}],
            }
        ]
        out = render_nodes(nodes)
        assert "<script>" not in out
        assert "&lt;script&gt;" in out or "&gt;" in out

    def test_link_javascript_scheme_is_dropped(self):
        nodes = [
            {
                "type": "link",
                "data": {"url": "javascript:alert(1)"},
                "children": [{"text": "click"}],
            }
        ]
        out = render_nodes(nodes)
        assert out == "click"
        assert "<a" not in out
        assert "javascript" not in out

    def test_link_obfuscated_scheme_is_dropped(self):
        # Browsers ignore embedded control chars, so "java\tscript:" executes;
        # the serializer must strip them and still reject the scheme.
        for url in ("java\tscript:alert(1)", " javascript:alert(1)", "JAVASCRIPT:x"):
            nodes = [{"type": "link", "data": {"url": url}, "children": [{"text": "x"}]}]
            out = render_nodes(nodes)
            assert out == "x"
            assert "<a" not in out

    def test_link_relative_and_mailto_allowed(self):
        for url in ("../resolveuid/abc123", "/some/page", "mailto:a@b.com"):
            nodes = [{"type": "link", "data": {"url": url}, "children": [{"text": "x"}]}]
            out = render_nodes(nodes)
            assert out.startswith("<a href=")
            assert ">x</a>" in out

    def test_unknown_element_drops_wrapper_keeps_children(self):
        nodes = [{"type": "weird", "children": [{"text": "kept"}]}]
        assert render_nodes(nodes) == "kept"

    def test_void_break(self):
        nodes = [{"type": "br", "children": []}]
        assert render_nodes(nodes) == "<br />"

    def test_headings(self):
        nodes = [{"type": "h2", "children": [{"text": "Title"}]}]
        assert render_nodes(nodes) == "<h2>Title</h2>"
