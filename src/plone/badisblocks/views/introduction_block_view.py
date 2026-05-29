"""IntroductionBlockView browser view.

Renders an introduction block. Like the slate block, its content is a
``value`` node tree; it differs only in its wrapping markup.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.slate import render_nodes


class IntroductionBlockView(BaseBlockView):
    """Render an introduction block's node tree as safe HTML."""

    def render(self):
        return render_nodes((self.data or {}).get("value"))
