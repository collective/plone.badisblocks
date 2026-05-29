"""AccordionBlockView browser view.

Renders an accordion block (``@type`` ``accordion``) as a list of native
``<details>``/``<summary>`` panels, reusing the block dispatch machinery for
each panel's nested blocks (so no client-side JavaScript is needed).

Panel data follows the EEA ``volto-accordion-block`` layout: the panels live
under ``data["data"]`` as a ``blocks`` mapping keyed by id plus a
``blocks_layout`` giving their order. Each panel carries a string ``title`` and
its own nested ``blocks``/``blocks_layout``. Older content may store the
``blocks``/``blocks_layout`` directly on ``data``; both shapes are accepted.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.base import BlockDispatchMixin


class AccordionBlockView(BaseBlockView, BlockDispatchMixin):
    """Render an accordion block's panels as <details> elements."""

    @property
    def _container(self):
        data = self.data or {}
        return data.get("data") or data

    @property
    def title(self):
        return (self.data or {}).get("title")

    @property
    def _collapsed(self):
        # EEA defaults panels to collapsed; treat a missing flag as collapsed.
        return (self.data or {}).get("collapsed", True)

    @property
    def _exclusive(self):
        # non_exclusive false (the default) means only one panel open at a time.
        return not (self.data or {}).get("non_exclusive", False)

    @property
    def panels(self):
        container = self._container
        blocks = container.get("blocks") or {}
        items = (container.get("blocks_layout") or {}).get("items", [])
        # A shared name groups the <details> so opening one closes the others
        # (exclusive accordion); omitted when panels may stay open together.
        group = f"accordion-{self.block_id}" if self._exclusive else None
        open_attr = None if self._collapsed else "open"
        panels = []
        for panel_id in items:
            panel = blocks.get(panel_id)
            if not panel:
                continue
            content = self.render_blocks(
                panel.get("blocks") or {},
                (panel.get("blocks_layout") or {}).get("items", []),
            )
            panels.append(
                {
                    "title": panel.get("title") or "",
                    "content": content,
                    "open": open_attr,
                    "name": group,
                }
            )
        return panels
