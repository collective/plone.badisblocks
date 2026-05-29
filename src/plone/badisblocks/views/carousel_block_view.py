"""CarouselBlockView browser view.

Renders a carousel block (``@type`` ``carousel``): a horizontally scrollable row
of teaser cards. Like the grid block it is a *container* — its ``columns`` are
themselves blocks (teasers) — so it re-uses the block dispatch machinery to
render each column through its own per-type view. ``headline`` is an optional
heading and ``items_to_show`` is how many cards are visible at once.

The columns' teasers are enriched (href resolved, ``image_scales`` attached) by
``serialize_blocks``: plone.volto's ``NestedBlocksVisitor`` recurses into
``columns`` so the standard teaser/image transformers run on each.

Volto drives the carousel with JavaScript; here every column is rendered into a
CSS scroll-snap track so the block is usable server-side without any JS.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.base import BlockDispatchMixin


class CarouselBlockView(BaseBlockView, BlockDispatchMixin):
    """Render a carousel block's columns as a scroll-snap row of teasers."""

    @property
    def headline(self):
        return (self.data or {}).get("headline")

    @property
    def items_to_show(self):
        try:
            count = int((self.data or {}).get("items_to_show") or 0)
        except (TypeError, ValueError):
            count = 0
        return count if count > 0 else 3

    @property
    def track_style(self):
        return f"--bb-carousel-items: {self.items_to_show}"

    @property
    def _column_ids(self):
        return [col["@id"] for col in (self.data or {}).get("columns") or [] if col.get("@id")]

    @property
    def column_count(self):
        return len(self._column_ids)

    @property
    def columns(self):
        cols = (self.data or {}).get("columns") or []
        blocks = {col["@id"]: col for col in cols if col.get("@id")}
        return [self.render_block(cid, blocks) for cid in self._column_ids]

    @property
    def css_class(self):
        return "block carousel"
