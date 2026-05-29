"""MapsBlockView browser view.

Render a maps (embed) block
"""
from Products.Five.browser import BrowserView


class MapsBlockView(BrowserView):
    """Render a maps (embed) block"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("maps_block_view.pt")

    def __call__(self):
        return self.index()
