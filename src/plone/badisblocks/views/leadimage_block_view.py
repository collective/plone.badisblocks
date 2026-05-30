"""LeadImageBlockView browser view.

Renders the ``leadimage`` block from Volto core. Unlike the image block (which
carries its own ``image_scales``), the lead image block renders the *context's*
own ``image`` field -- so it only shows up on content that has one (Volto
restricts the block the same way). The markup mirrors Volto's ``LeadImage`` View:
a ``p.block.image.align <align>`` wrapping the image, optionally linked.

The responsive ``<img>`` (with ``srcset``) is produced by Plone's standard
``@@images`` scaling view (``tag()``), so scale generation/HiDPI handling matches
the rest of Classic UI. ``data["align"]`` controls alignment (default ``center``,
``full`` for full width); ``data["href"]`` optionally links the image, opening in
a new tab when ``openLinkInNewTab`` is set.
"""

from urllib.parse import urlparse

from Acquisition import aq_inner
from zope.component import getMultiAdapter

from plone.badisblocks.views.base import BaseBlockView


class LeadImageBlockView(BaseBlockView):
    """Render the context's lead image."""

    image_field = "image"
    # Display scale used as the image's main size; srcset is added by ``tag()``.
    main_scale = "great"

    @property
    def align(self):
        return (self.data or {}).get("align") or "center"

    @property
    def css_class(self):
        return f"block image align {self.align}"

    @property
    def image_css_class(self):
        return "full-width" if self.align == "full" else None

    @property
    def href(self):
        href = (self.data or {}).get("href") or ""
        if not href:
            return ""
        # Volto stores an app-relative path already; strip any absolute URL.
        return urlparse(href).path or href

    @property
    def target(self):
        return "_blank" if (self.data or {}).get("openLinkInNewTab") else None

    @property
    def rel(self):
        # Pair noopener with target=_blank (reverse-tabnabbing), as the other
        # link-bearing blocks do.
        return "noopener noreferrer" if self.target else None

    @property
    def has_image(self):
        return bool(getattr(aq_inner(self.context), self.image_field, None))

    @property
    def alt(self):
        return getattr(self.context, "image_caption", "") or ""

    def image_tag(self):
        """The responsive ``<img>`` HTML for the context image, or ``""``."""
        if not self.has_image:
            return ""
        try:
            scaling = getMultiAdapter((self.context, self.request), name="images")
            tag = scaling.tag(
                self.image_field,
                scale=self.main_scale,
                alt=self.alt,
                css_class=self.image_css_class,
            )
        except Exception:
            return ""
        return tag or ""
