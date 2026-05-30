"""HeadingBlockView browser view.

Renders the ``heading`` block from ``@kitconcept/volto-heading-block`` (used by
volto-light-theme): a standalone heading with its own anchor. The markup mirrors
the upstream ``HeadingView`` -- ``div.block.heading.block-heading-<tag>`` wrapping
a ``div.heading-wrapper`` and the heading element itself (``heading.heading-<tag>``
carrying an ``id``).

The tag comes from ``data["tag"]`` (volto-light-theme restricts the editor to
``h2``); only ``h2``-``h6`` are accepted, anything else falls back to ``h2``. The
anchor ``id`` is a slug of the heading text built with the same ``slugify`` the
slate serializer/toc block use, so a table-of-contents can target it. Alignment
from ``styles["align"]`` (blockAlignment) is exposed as a ``has--align--<value>``
class, matching the other blocks.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.slate import slugify


ALLOWED_TAGS = ("h2", "h3", "h4", "h5", "h6")


class HeadingBlockView(BaseBlockView):
    """Render a heading block."""

    @property
    def text(self):
        return (self.data or {}).get("heading") or ""

    @property
    def tag(self):
        tag = (self.data or {}).get("tag")
        return tag if tag in ALLOWED_TAGS else "h2"

    @property
    def anchor_id(self):
        return slugify(self.text) or None

    @property
    def align(self):
        return ((self.data or {}).get("styles") or {}).get("align")

    @property
    def css_class(self):
        classes = ["block", "heading", f"block-heading-{self.tag}"]
        if (self.data or {}).get("ordered"):
            classes.append("ordered")
        if self.align:
            classes.append(f"has--align--{self.align}")
        return " ".join(classes)

    @property
    def heading_class(self):
        return f"heading heading-{self.tag}"
