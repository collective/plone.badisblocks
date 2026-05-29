"""Serialize Volto slate (rich text) node trees to safe HTML.

Volto stores slate as a recursive tree: text nodes carry only ``text``; inline
formatting (strong/em/link/...) and block elements are *element* nodes with a
``type`` and ``children``. Every text leaf is HTML-escaped and only whitelisted
element types emit a tag, so no unsanitized editor markup reaches the page.
Link hrefs are additionally restricted to an allowlist of URL schemes to block
``javascript:`` and similar XSS vectors.
"""

import re
import unicodedata
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

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def node_text(node):
    """Concatenate the plain text of a slate node and its descendants."""
    if not isinstance(node, dict):
        return ""
    if "text" in node:
        return node["text"]
    return "".join(node_text(child) for child in node.get("children") or [])


def slugify(text):
    """Build a URL-safe slug from heading text (accents stripped, lowercased)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def heading_anchor_id(block_id, text):
    """Stable anchor id for a heading, matching the toc block's link targets."""
    slug = slugify(text)
    return f"{block_id}-{slug}" if slug else block_id


def render_nodes(nodes, block_id=""):
    """Render a list of slate nodes to an HTML string.

    ``block_id`` (when given) makes heading elements carry an ``id`` anchor so
    the table-of-contents block can link to them.
    """
    if not nodes:
        return ""
    return "".join(render_node(node, block_id) for node in nodes)


def render_node(node, block_id=""):
    """Render a single slate node (text leaf or element) to an HTML string."""
    if not isinstance(node, dict):
        return ""
    if "text" in node:
        return escape(node["text"])
    node_type = node.get("type")
    children = render_nodes(node.get("children"), block_id)
    if node_type == "link":
        return _render_link(node, children)
    tag = TAG_MAP.get(node_type)
    if tag is None:
        # Unknown element: drop the wrapper but keep its content.
        return children
    if tag in VOID_TAGS:
        return f"<{tag} />"
    if tag in HEADING_TAGS and block_id:
        anchor = heading_anchor_id(block_id, node_text(node))
        if anchor:
            attr = escape(anchor, quote=True)
            return f'<{tag} id="{attr}">{children}</{tag}>'
    return f"<{tag}>{children}</{tag}>"


def _render_link(node, children):
    url = (node.get("data") or {}).get("url") or ""
    cleaned = _CONTROL_CHARS.sub("", url).strip()
    if urlparse(cleaned).scheme.lower() not in SAFE_SCHEMES:
        # Unsafe scheme (e.g. javascript:): drop the link, keep the text.
        return children
    href = escape(cleaned, quote=True)
    return f'<a href="{href}">{children}</a>'
