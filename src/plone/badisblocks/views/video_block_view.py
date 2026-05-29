"""VideoBlockView browser view.

Renders a video block. YouTube and Vimeo URLs become privacy-friendly iframe
embeds; everything else is treated as a self-hosted file served by ``<video>``.
"""

import re

from plone.badisblocks.views.base import BaseBlockView


_YOUTUBE_PATTERNS = (
    re.compile(r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)"),
    re.compile(r"youtu\.be/([a-zA-Z0-9_-]+)"),
    re.compile(r"youtube\.com/embed/([a-zA-Z0-9_-]+)"),
)
_VIMEO_PATTERN = re.compile(r"vimeo\.com/(\d+)")

_YOUTUBE_ALLOW = (
    "accelerometer; autoplay; clipboard-write; encrypted-media; "
    "gyroscope; picture-in-picture; web-share"
)
_VIMEO_ALLOW = "autoplay; fullscreen; picture-in-picture"


class VideoBlockView(BaseBlockView):
    """Render a YouTube/Vimeo embed or a self-hosted video."""

    @property
    def url(self):
        return (self.data or {}).get("url") or ""

    @property
    def source(self):
        url = self.url
        if not url:
            return None
        if any(s in url for s in ("youtube.com/watch", "youtu.be/", "youtube.com/embed/")):
            return "youtube"
        if "vimeo.com/" in url:
            return "vimeo"
        return "self-hosted"

    @property
    def embed_url(self):
        """The iframe src for a YouTube/Vimeo video, else None."""
        url = self.url
        if self.source == "youtube":
            for pattern in _YOUTUBE_PATTERNS:
                match = pattern.search(url)
                if match:
                    return f"https://www.youtube-nocookie.com/embed/{match.group(1)}"
        elif self.source == "vimeo":
            match = _VIMEO_PATTERN.search(url)
            if match:
                return f"https://player.vimeo.com/video/{match.group(1)}"
        return None

    @property
    def iframe_title(self):
        return f"{self.source} video player"

    @property
    def iframe_allow(self):
        return _YOUTUBE_ALLOW if self.source == "youtube" else _VIMEO_ALLOW

    @property
    def video_src(self):
        """The file URL for a self-hosted video, else None."""
        return self.url if self.source == "self-hosted" and self.url else None

    @property
    def poster(self):
        return (self.data or {}).get("preview_image") or None

    @property
    def css_class(self):
        data = self.data or {}
        align = (data.get("styles") or {}).get("align") or data.get("align") or "full"
        return f"block video has--align--{align}"
