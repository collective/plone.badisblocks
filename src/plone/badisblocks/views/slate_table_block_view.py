"""SlateTableBlockView browser view.

Renders a slate table block. The table lives in ``data.table.rows``; each row
has ``cells``, and each cell's ``value`` is a slate node tree rendered with the
shared slate serializer. The first row is the header (unless ``hideHeaders``).
Client-side features (sorting) are dropped — Classic UI renders a static table.
"""

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.slate import render_nodes


# data.table flags -> CSS modifier class suffix
_TABLE_FLAGS = {
    "hideHeaders": "hide-headers",
    "sortable": "sortable",
    "fixed": "fixed",
    "compact": "compact",
    "basic": "basic",
    "celled": "celled",
    "inverted": "inverted",
    "striped": "striped",
}


class SlateTableBlockView(BaseBlockView):
    """Render a slate table block as a static HTML table."""

    @property
    def _table(self):
        return (self.data or {}).get("table") or {}

    @property
    def _rows(self):
        return self._table.get("rows") or []

    @property
    def has_rows(self):
        return bool(self._rows)

    @property
    def hide_headers(self):
        return bool(self._table.get("hideHeaders"))

    @property
    def header_cells(self):
        return (self._rows[0].get("cells") or []) if self._rows else []

    @property
    def data_rows(self):
        return self._rows[1:] if self._rows else []

    @property
    def table_classes(self):
        classes = [
            f"slateTable--{suffix}"
            for flag, suffix in _TABLE_FLAGS.items()
            if self._table.get(flag)
        ]
        return " ".join(classes)

    def cell_html(self, cell):
        """Render a cell's slate value, or a non-breaking space when empty."""
        return render_nodes((cell or {}).get("value")) or " "
