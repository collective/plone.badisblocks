"""TocBlockView browser view.

Render a table of contents block
"""
from Products.Five.browser import BrowserView


class TocBlockView(BrowserView):
    """Render a table of contents block"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("toc_block_view.pt")

    def __call__(self):
        return self.index()
