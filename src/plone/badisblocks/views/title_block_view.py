"""TitleBlockView browser view.

Renders the context title (the title block maps to the content's title).
"""

from plone.badisblocks.views.base import BaseBlockView


class TitleBlockView(BaseBlockView):
    """Render the context title as the document heading."""
