"""Serialize Volto slate (rich text) node trees to safe HTML.

Volto stores slate as a recursive tree: text nodes carry only ``text``; inline
formatting (strong/em/link/...) and block elements are *element* nodes with a
``type`` and ``children``. Every text leaf is HTML-escaped and only whitelisted
element types emit a tag, so no unsanitized editor markup reaches the page.
Link hrefs are additionally restricted to an allowlist of URL schemes to block
``javascript:`` and similar XSS vectors.
"""

import re
from html import escape
from urllib.parse import urlparse


# Schemes permitted in link hrefs. "" allows relative URLs (incl. resolveuid).
SAFE_SCHEMES = {"http", "https", "mailto", "tel", ""}

# Control chars browsers ignore inside URLs; they can hide a scheme
# (e.g. "java\tscript:"), so strip them before validating.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f]")


# slate element ``type`` -> HTML tag
TAG_MAP = {
    "p": "p",
    "h1": "h1",
    "h2": "h2",
    "h3": "h3",
    "h4": "h4",
    "h5": "h5",
    "h6": "h6",
    "blockquote": "blockquote",
    "ul": "ul",
    "ol": "ol",
    "li": "li",
    "strong": "strong",
    "b": "strong",
    "em": "em",
    "i": "em",
    "u": "u",
    "underline": "u",
    "s": "s",
    "strikethrough": "s",
    "del": "del",
    "sub": "sub",
    "sup": "sup",
    "code": "code",
    "br": "br",
}

VOID_TAGS = {"br"}


def render_nodes(nodes):
    """Render a list of slate nodes to an HTML string."""
    if not nodes:
        return ""
    return "".join(render_node(node) for node in nodes)


def render_node(node):
    """Render a single slate node (text leaf or element) to an HTML string."""
    if not isinstance(node, dict):
        return ""
    if "text" in node:
        return escape(node["text"])
    node_type = node.get("type")
    children = render_nodes(node.get("children"))
    if node_type == "link":
        return _render_link(node, children)
    tag = TAG_MAP.get(node_type)
    if tag is None:
        # Unknown element: drop the wrapper but keep its content.
        return children
    if tag in VOID_TAGS:
        return f"<{tag} />"
    return f"<{tag}>{children}</{tag}>"


def _render_link(node, children):
    url = (node.get("data") or {}).get("url") or ""
    cleaned = _CONTROL_CHARS.sub("", url).strip()
    if urlparse(cleaned).scheme.lower() not in SAFE_SCHEMES:
        # Unsafe scheme (e.g. javascript:): drop the link, keep the text.
        return children
    href = escape(cleaned, quote=True)
    return f'<a href="{href}">{children}</a>'
