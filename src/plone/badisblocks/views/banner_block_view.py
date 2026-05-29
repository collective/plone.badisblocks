"""BannerBlockView browser view.

Renders a banner (hero) block from volto-light-theme: a background image with
``text`` and ``additionalText`` lines overlaid. The image comes from
``image_scales["image"][0]`` with ``url`` as its base path (the raw object url,
which — unlike the teaser's ``preview_image`` — already carries the site-id
prefix Classic UI is served under), so a responsive ``srcset`` is built the same
way as the plain image block.
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView


class BannerBlockView(BaseBlockView):
    """Render a banner block."""

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
    def src(self):
        img = self._image
        if not img or not img.get("download"):
            return ""
        return f"{self.base_path}/{img['download']}"

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

    @property
    def alt(self):
        return (self.data or {}).get("alt") or ""

    @property
    def text(self):
        return (self.data or {}).get("text") or ""

    @property
    def additional_text(self):
        return (self.data or {}).get("additionalText") or ""

    @property
    def theme(self):
        return (self.data or {}).get("theme") or "default"

    @property
    def css_class(self):
        return f"block banner has--theme--{self.theme}"
