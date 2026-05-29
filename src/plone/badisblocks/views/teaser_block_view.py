"""TeaserBlockView browser view.

Renders a teaser block. After block serialization ``data["href"][0]`` holds the
resolved target (a brain summary); with ``overwrite`` false the serializer already
copies the target's title/description/head_title onto ``data`` itself, so ``data``'s
values are authoritative either way. The image comes from an overwritten
``preview_image`` or the target's ``image_scales[image_field]``.
"""

from urllib.parse import urlparse

from plone import api
from plone.badisblocks.views.base import BaseBlockView


class TeaserBlockView(BaseBlockView):
    """Render a teaser block."""

    @property
    def target(self):
        href = (self.data or {}).get("href") or []
        return href[0] if href else None

    @property
    def title(self):
        return (self.data or {}).get("title") or (self.target or {}).get("title") or ""

    @property
    def description(self):
        data = self.data or {}
        if data.get("hide_description"):
            return ""
        return data.get("description") or (self.target or {}).get("description") or ""

    @property
    def head_title(self):
        return (self.data or {}).get("head_title") or (self.target or {}).get("head_title") or ""

    @property
    def href(self):
        target = self.target or {}
        url = target.get("@id")
        if not url:
            return ""
        return urlparse(url).path or url

    @property
    def align(self):
        return ((self.data or {}).get("styles") or {}).get("align") or "left"

    @property
    def css_class(self):
        return f"block teaser has--align--{self.align}"

    @property
    def _image(self):
        data = self.data or {}
        preview = data.get("preview_image")
        if preview:
            return preview[0]
        target = self.target or {}
        field = target.get("image_field")
        scales = target.get("image_scales") or {}
        if field and scales.get(field):
            return scales[field][0]
        return None

    @property
    def image_base_path(self):
        img = self._image or {}
        base = img.get("base_path")
        if base:
            # plone.volto's preview-image adapter stores base_path relative to
            # the navigation root (it strips portal_url), which is what Volto
            # wants but drops the site-id prefix Classic UI is served under
            # (e.g. ``/Plone``). Re-add it so the image resolves.
            prefix = urlparse(api.portal.get().absolute_url()).path
            return f"{prefix}{base}"
        url = (self.target or {}).get("@id")
        return urlparse(url).path if url else ""

    @property
    def image_src(self):
        img = self._image
        if not img or not img.get("download"):
            return ""
        return f"{self.image_base_path}/{img['download']}"

    @property
    def image_srcset(self):
        img = self._image
        if not img:
            return None
        scales = img.get("scales") or {}
        entries = [
            f"{self.image_base_path}/{v['download']} {v['width']}w"
            for v in scales.values()
            if v.get("download") and v.get("width")
        ]
        return ", ".join(entries) or None

    @property
    def image_alt(self):
        img = self._image or {}
        return img.get("alt") or self.title or ""
