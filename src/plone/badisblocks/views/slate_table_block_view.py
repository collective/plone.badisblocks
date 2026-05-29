"""SlateTableBlockView browser view.

Render a slate table block
"""
from Products.Five.browser import BrowserView


class SlateTableBlockView(BrowserView):
    """Render a slate table block"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("slate_table_block_view.pt")

    def __call__(self):
        return self.index()
