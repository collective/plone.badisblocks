"""SliderBlockView browser view.

Renders a slider/carousel block (``@type`` ``slider`` from
``@kitconcept/volto-slider-block``). Each slide is itself a teaser: ``href[0]``
is the resolved target (brain summary), with ``head_title``/``title``/
``description`` overridable on the slide and an optional ``preview_image``
override. The slide image is resolved by the shared ``teaser_image`` helper.

Volto drives the carousel with JavaScript (Embla); here every slide is rendered
into a CSS scroll-snap track so the block is usable server-side without any JS.
volto-light-theme's per-slide extras are honoured: ``buttonText``/``hideButton``
(a call-to-action, shown as a styled span since the whole slide is already a
link) and ``flagAlign`` (text block left/right).
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.teaser_image import teaser_image


class SliderBlockView(BaseBlockView):
    """Render a slider block's slides as a scroll-snap carousel."""

    @property
    def slides(self):
        result = []
        for slide in (self.data or {}).get("slides") or []:
            href = slide.get("href") or []
            target = href[0] if href else None
            target = target or {}
            url = target.get("@id")
            image = teaser_image(slide.get("preview_image"), target)
            title = slide.get("title") or target.get("title") or ""
            result.append(
                {
                    "head_title": slide.get("head_title") or target.get("head_title") or "",
                    "title": title,
                    "description": slide.get("description") or target.get("description") or "",
                    "href": urlparse(url).path or url if url else "",
                    "target": "_blank" if slide.get("openLinkInNewTab") else None,
                    "rel": "noopener noreferrer" if slide.get("openLinkInNewTab") else None,
                    "image_src": image["src"] if image else "",
                    "image_srcset": image["srcset"] if image else None,
                    "image_alt": (image["alt"] if image else "") or title,
                    "show_button": not slide.get("hideButton"),
                    "button_text": slide.get("buttonText") or "Continue reading",
                    "flag_align": slide.get("flagAlign") or "left",
                }
            )
        return result

    @property
    def slide_count(self):
        return len(self.slides)

    @property
    def css_class(self):
        return "block slider"
