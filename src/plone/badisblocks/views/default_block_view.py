"""DefaultBlockView browser view.

Fallback renderer for block types that have no dedicated view.
"""

from plone.badisblocks.views.base import BaseBlockView


class DefaultBlockView(BaseBlockView):
    """Render nothing visible; keep the block type for debugging."""
