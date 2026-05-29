"""GridBlockView browser view.

Renders a grid block (``@type`` ``gridBlock``) by nesting its child blocks as
columns, reusing the block dispatch machinery.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.base import BlockDispatchMixin


class GridBlockView(BaseBlockView, BlockDispatchMixin):
    """Render a grid block's child blocks as columns."""

    @property
    def _items(self):
        return ((self.data or {}).get("blocks_layout") or {}).get("items", [])

    @property
    def headline(self):
        return (self.data or {}).get("headline")

    @property
    def column_count(self):
        # Bootstrap row-cols-md-* is defined for 1..6.
        return min(max(len(self._items), 1), 6)

    @property
    def columns(self):
        blocks = (self.data or {}).get("blocks") or {}
        return [self.render_block(block_id, blocks) for block_id in self._items]
