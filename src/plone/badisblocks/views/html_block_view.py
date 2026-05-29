"""HtmlBlockView browser view.

Render a raw HTML block
"""
from Products.Five.browser import BrowserView


class HtmlBlockView(BrowserView):
    """Render a raw HTML block"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("html_block_view.pt")

    def __call__(self):
        return self.index()
