"""TocBlockView browser view.

Renders a table of contents by scanning the page's slate blocks for heading
nodes (h2-h6 by default) and linking to the anchors the slate serializer emits
on those headings (see ``slate.heading_anchor_id``).
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.slate import heading_anchor_id
from plone.badisblocks.views.slate import node_text


DEFAULT_LEVELS = ["h2", "h3", "h4", "h5", "h6"]


class TocBlockView(BaseBlockView):
    """Render a table of contents for the page's slate headings."""

    @property
    def levels(self):
        return (self.data or {}).get("levels") or DEFAULT_LEVELS

    @property
    def title(self):
        return (self.data or {}).get("title")

    @property
    def show_title(self):
        data = self.data or {}
        return bool(data.get("title")) and not data.get("hide_title")

    @property
    def aria_label(self):
        return (self.data or {}).get("title") or "Table of Contents"

    @property
    def ordered(self):
        return bool((self.data or {}).get("ordered"))

    @property
    def entries(self):
        """Headings from the context's slate blocks, in layout order."""
        blocks = getattr(self.context, "blocks", None) or {}
        layout = getattr(self.context, "blocks_layout", None) or {}
        levels = self.levels
        entries = []
        for block_id in layout.get("items") or []:
            block = blocks.get(block_id)
            if not block or block.get("@type") != "slate":
                continue
            for node in block.get("value") or []:
                node_type = node.get("type") if isinstance(node, dict) else None
                if node_type not in levels:
                    continue
                text = node_text(node).strip()
                if not text:
                    continue
                entries.append({
                    "level": int(node_type[1]),
                    "title": text,
                    "id": heading_anchor_id(block_id, text),
                })
        return entries
