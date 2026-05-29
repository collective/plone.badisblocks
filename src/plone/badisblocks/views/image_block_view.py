"""ImageBlockView browser view.

Renders an image block from Volto ``image_scales`` data, building a responsive
``srcset`` from the available scales.
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView


class ImageBlockView(BaseBlockView):
    """Render an image block."""

    @property
    def _image(self):
        scales = (self.data or {}).get("image_scales") or {}
        images = scales.get("image") or []
        return images[0] if images else None

    @property
    def base_path(self):
        url = (self.data or {}).get("url") or ""
        return urlparse(url).path or url

    @property
    def alt(self):
        return (self.data or {}).get("alt") or ""

    @property
    def src(self):
        img = self._image
        if not img or not img.get("download"):
            return ""
        return f"{self.base_path}/{img['download']}"

    @property
    def width(self):
        img = self._image
        return img.get("width") if img else None

    @property
    def height(self):
        img = self._image
        return img.get("height") if img else None

    @property
    def srcset(self):
        img = self._image
        if not img:
            return None
        scales = img.get("scales") or {}
        entries = [
            f"{self.base_path}/{v['download']} {v['width']}w"
            for v in scales.values()
            if v.get("download") and v.get("width")
        ]
        return ", ".join(entries) or None
