"""HtmlBlockView browser view.

Renders a raw HTML block. The stored ``html`` is editor-provided content and
is emitted verbatim (``structure``), mirroring how Volto renders this block.
"""

from plone.badisblocks.views.base import BaseBlockView


class HtmlBlockView(BaseBlockView):
    """Render a raw HTML block."""

    @property
    def html(self):
        return (self.data or {}).get("html") or ""

    @property
    def has_content(self):
        return bool(self.html.strip())

    @property
    def css_class(self):
        """Build the wrapper class list, matching the Volto block markup."""
        styles = (self.data or {}).get("styles") or {}
        classes = ["block", "html"]
        classes.append(f"has--align--{styles.get('align') or 'left'}")
        if styles.get("customCss"):
            classes.append(styles["customCss"])
        return " ".join(classes)
