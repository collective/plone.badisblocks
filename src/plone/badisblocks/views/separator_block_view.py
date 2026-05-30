"""SeparatorBlockView browser view.

Renders the ``separator`` block from ``@kitconcept/volto-separator-block`` (used by
volto-light-theme): a thin horizontal divider. The markup mirrors the upstream
``SeparatorView`` -- a ``div.block.separator`` wrapping a ``div.line`` -- and the
volto-light-theme styling hooks are reproduced as ``has--<key>--<value>`` classes
on the wrapper: ``shortLine`` (a boolean toggling a short, fixed-width line),
``align`` (blockAlignment) and ``blockWidth``. See ``_separator.scss`` upstream.
"""

from plone.badisblocks.views.base import BaseBlockView


class SeparatorBlockView(BaseBlockView):
    """Render a separator (divider) block."""

    @property
    def _styles(self):
        return (self.data or {}).get("styles") or {}

    @property
    def css_class(self):
        styles = self._styles
        classes = ["block", "separator"]
        if styles.get("shortLine"):
            classes.append("has--shortLine--true")
        align = styles.get("align")
        if align:
            classes.append(f"has--align--{align}")
        block_width = styles.get("blockWidth")
        if block_width:
            classes.append(f"has--blockWidth--{block_width}")
        return " ".join(classes)
