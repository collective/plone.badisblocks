"""IntroductionBlockView browser view.

Render an introduction block (slate-style rich text)
"""
from Products.Five.browser import BrowserView


class IntroductionBlockView(BrowserView):
    """Render an introduction block (slate-style rich text)"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("introduction_block_view.pt")

    def __call__(self):
        return self.index()
