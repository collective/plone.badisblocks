"""SliderBlockView browser view.

Renders the ``slider`` block from ``@kitconcept/volto-slider-block`` (used by
volto-light-theme): a full-width slideshow of content teasers. Unlike the
carousel block (which nests teaser *blocks* in ``columns``), the slider stores a
flat ``data["slides"]`` list; each slide references a content item via ``href``
and carries its own ``title``/``nav_title``/``head_title``/``description`` plus an
optional ``preview_image``.

After block serialization (``serialize_blocks``), plone.volto's
``NestedBlocksVisitor`` recurses into ``slides``, so each slide's ``href`` is
resolved to the target's summary (carrying ``image_field`` + ``image_scales``)
and any ``preview_image`` override is enriched with ``image_scales``. The slide
image therefore comes from the ``preview_image`` override when set, otherwise from
the ``href`` target -- mirroring volto-slider-block's ``DefaultBody``
(``image || href``).

Volto drives the slider with Embla (loop + optional autoplay); here each slide is
rendered into a CSS scroll-snap viewport (one slide wide) so the block works
server-side without JavaScript. badisblocks.js progressively enhances it with the
same prev/next + dot navigation used by the carousel. Autoplay is not reproduced.
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.teaser_image import image_base_path


def _path(url):
    """Site-relative path of an absolute content URL."""
    if not url:
        return ""
    return urlparse(url).path or url


def _image_holder(slide):
    """Return ``(holder, image)`` for a slide -- the dict carrying the image and
    the raw image dict itself -- from the ``preview_image`` override if set,
    otherwise from the ``href`` target. Both carry ``image_scales`` keyed by
    field; the target additionally names its field in ``image_field``. Returns
    ``(None, None)`` when the slide has no usable image.
    """
    preview = slide.get("preview_image") or []
    if preview and isinstance(preview[0], dict):
        obj = preview[0]
        scales_map = obj.get("image_scales") or {}
        field = "image" if "image" in scales_map else next(iter(scales_map), None)
        images = (scales_map.get(field) or []) if field else []
        if images:
            return obj, images[0]
    href = slide.get("href") or []
    if href and isinstance(href[0], dict):
        target = href[0]
        field = target.get("image_field")
        scales_map = target.get("image_scales") or {}
        images = (scales_map.get(field) or []) if field else []
        if images:
            return target, images[0]
    return None, None


def _slide_image(slide):
    """Build ``{src, srcset, sizes, width, height, alt}`` for a slide, or None.

    Uses the ``preview_image`` override or the ``href`` target (see
    ``_image_holder``). The ``download``/scale paths are resolved against the
    image's ``base_path`` (re-prefixed with the site id for Classic UI by the
    shared ``image_base_path`` helper) or, failing that, the holder's ``@id``.
    """
    holder, img = _image_holder(slide)
    if not img or not img.get("download"):
        return None
    base = image_base_path(img, holder)
    named_scales = img.get("scales") or {}
    srcset = (
        ", ".join(
            f"{base}/{v['download']} {v['width']}w"
            for v in named_scales.values()
            if v.get("download") and v.get("width")
        )
        or None
    )
    return {
        "src": f"{base}/{img['download']}",
        "srcset": srcset,
        "sizes": "100vw",
        "width": img.get("width"),
        "height": img.get("height"),
        "alt": img.get("alt") or slide.get("title") or "",
    }


class SliderBlockView(BaseBlockView):
    """Render a slider block as a scroll-snap slideshow of content teasers."""

    @property
    def _slides(self):
        return [s for s in (self.data or {}).get("slides") or [] if isinstance(s, dict)]

    @staticmethod
    def _href(slide):
        href = slide.get("href") or []
        if not href:
            return ""
        first = href[0]
        url = first.get("@id") if isinstance(first, dict) else first
        return _path(url)

    @property
    def slides(self):
        models = []
        for slide in self._slides:
            href = self._href(slide)
            new_tab = bool(slide.get("openLinkInNewTab"))
            models.append({
                "href": href,
                "target": "_blank" if new_tab else None,
                # Pair noopener with target=_blank (reverse-tabnabbing), as the
                # button/teaser blocks do.
                "rel": "noopener noreferrer" if new_tab else None,
                "head_title": slide.get("head_title") or "",
                "title": slide.get("nav_title") or slide.get("title") or "",
                "description": slide.get("description") or "",
                "image": _slide_image(slide),
            })
        return models

    @property
    def slide_count(self):
        return len(self._slides)

    @property
    def css_class(self):
        return "block slider"
