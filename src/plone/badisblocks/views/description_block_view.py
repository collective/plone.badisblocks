"""DescriptionBlockView browser view.

Renders the context description (the description block maps to the content's
description).
"""

from plone.badisblocks.views.base import BaseBlockView


class DescriptionBlockView(BaseBlockView):
    """Render the context description."""
