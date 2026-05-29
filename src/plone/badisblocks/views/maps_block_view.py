"""MapsBlockView browser view.

Renders a maps block as an embedded iframe (typically a Google Maps embed).
The embed ``url`` is restricted to http(s) so a stored ``javascript:`` or other
scheme can't be smuggled into the iframe ``src``.
"""

from urllib.parse import urlparse

from plone.badisblocks.views.base import BaseBlockView


class MapsBlockView(BaseBlockView):
    """Render a maps embed iframe."""

    @property
    def url(self):
        url = (self.data or {}).get("url") or ""
        if urlparse(url.strip()).scheme.lower() in ("http", "https"):
            return url.strip()
        return ""

    @property
    def title(self):
        return (self.data or {}).get("title") or "Google Maps embed"

    @property
    def aria_label(self):
        return (self.data or {}).get("title") or "Map location"

    @property
    def anchor_id(self):
        return f"after-map-{self.block_id}"

    @property
    def css_class(self):
        data = self.data or {}
        align = (data.get("styles") or {}).get("align") or data.get("align") or "full"
        return f"block maps has--align--{align}"
