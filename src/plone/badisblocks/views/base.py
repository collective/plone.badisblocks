"""Base classes for rendering Volto/Seven blocks in Classic UI."""

from Products.Five.browser import BrowserView
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter


class BlockDispatchMixin:
    """Render an ordered set of Volto blocks by dispatching to per-type views.

    Each block is rendered by a named browser view ``@@block-<@type>``; unknown
    types fall back to ``@@block-default``. Used by the page-level ``BlocksView``
    and by container blocks (e.g. grid) that nest their own blocks.
    """

    def render_blocks(self, blocks, items):
        """Render ``items`` (an ordered list of block ids) from ``blocks``."""
        if not blocks or not items:
            return ""
        return "".join(self.render_block(block_id, blocks) for block_id in items)

    def render_block(self, block_id, blocks):
        """Render a single block by dispatching to its per-type view."""
        data = (blocks or {}).get(block_id)
        if not data:
            return ""
        block_type = data.get("@type", "")
        try:
            view = getMultiAdapter((self.context, self.request), name=f"block-{block_type}")
        except ComponentLookupError:
            view = getMultiAdapter((self.context, self.request), name="block-default")
        view.block_id = block_id
        view.block_type = block_type
        view.data = data
        return view()


class BaseBlockView(BrowserView):
    """Base for per-block views; the dispatcher fills these before rendering."""

    data = None
    block_id = ""
    block_type = ""

    def __call__(self):
        return self.index()
