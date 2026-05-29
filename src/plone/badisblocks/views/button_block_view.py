"""ButtonBlockView browser view.

Renders a button block (``@type`` ``__button`` from ``@kitconcept/volto-button-block``).
The label is ``data["title"]``; the link target is the first entry of
``data["href"]`` (an object-browser value, ``href[0]["@id"]``), stripped to a path
so it resolves under Classic UI. ``openLinkInNewTab`` opens the link in a new tab.
Alignment comes from volto-light-theme's ``styles["align"]`` (blockAlignment),
falling back to the upstream ``inneralign`` field, default ``left``.
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView


class ButtonBlockView(BaseBlockView):
    """Render a button block."""

    @property
    def text(self):
        return (self.data or {}).get("title") or ""

    @property
    def href(self):
        href = (self.data or {}).get("href") or []
        url = href[0].get("@id") if href else None
        if not url:
            return ""
        return urlparse(url).path or url

    @property
    def target(self):
        return "_blank" if (self.data or {}).get("openLinkInNewTab") else None

    @property
    def rel(self):
        # Pair noopener with target=_blank so the opened page can't reach
        # window.opener (reverse-tabnabbing), matching Volto's UniversalLink.
        return "noopener noreferrer" if self.target else None

    @property
    def align(self):
        data = self.data or {}
        return (data.get("styles") or {}).get("align") or data.get("inneralign") or "left"

    @property
    def css_class(self):
        return f"block button has--align--{self.align}"
