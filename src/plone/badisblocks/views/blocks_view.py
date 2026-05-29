"""BlocksView browser view.

Page-level entry point that renders the Volto/Seven blocks of the context.
"""

from Products.Five.browser import BrowserView

from plone.badisblocks.views.base import BlockDispatchMixin
from plone.badisblocks.views.serializer import serialize_blocks


class BlocksView(BrowserView, BlockDispatchMixin):
    """Render the context's blocks in ``blocks_layout`` order."""

    @property
    def raw_blocks(self):
        return getattr(self.context, "blocks", None) or {}

    @property
    def layout_items(self):
        layout = getattr(self.context, "blocks_layout", None) or {}
        return layout.get("items", [])

    def render(self):
        blocks = serialize_blocks(self.context, self.raw_blocks)
        return self.render_blocks(blocks, self.layout_items)

    def __call__(self):
        return self.index()
