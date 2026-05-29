"""VideoBlockView browser view.

Render a video block (YouTube/Vimeo/self-hosted)
"""
from Products.Five.browser import BrowserView


class VideoBlockView(BrowserView):
    """Render a video block (YouTube/Vimeo/self-hosted)"""

    # If you need to override the template registered in configure.zcml:
    # index = ViewPageTemplateFile("video_block_view.pt")

    def __call__(self):
        return self.index()
