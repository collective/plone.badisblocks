"""SlateBlockView browser view.

Renders a slate (rich text) block from its ``value`` node tree.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.slate import render_nodes


class SlateBlockView(BaseBlockView):
    """Render a slate block's node tree as safe HTML."""

    def render(self):
        return render_nodes((self.data or {}).get("value"), self.block_id)
