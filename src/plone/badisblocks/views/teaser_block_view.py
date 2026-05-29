"""TeaserBlockView browser view.

Renders a teaser block. After block serialization ``data["href"][0]`` holds the
resolved target (a brain summary); with ``overwrite`` false the serializer already
copies the target's title/description/head_title onto ``data`` itself, so ``data``'s
values are authoritative either way. The image comes from an overwritten
``preview_image`` or the target's ``image_scales[image_field]`` (resolved by the
shared ``teaser_image`` helper).
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.teaser_image import image_base_path
from plone.badisblocks.views.teaser_image import resolve_image
from plone.badisblocks.views.teaser_image import teaser_image


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
        return resolve_image((self.data or {}).get("preview_image"), self.target)

    @property
    def image_base_path(self):
        return image_base_path(self._image, self.target)

    @property
    def _resolved_image(self):
        return teaser_image((self.data or {}).get("preview_image"), self.target)

    @property
    def image_src(self):
        img = self._resolved_image
        return img["src"] if img else ""

    @property
    def image_srcset(self):
        img = self._resolved_image
        return img["srcset"] if img else None

    @property
    def image_alt(self):
        img = self._resolved_image
        return (img["alt"] if img else "") or self.title or ""
