"""ListingBlockView browser view.

Renders a listing block. Unlike most blocks, the listing block stores only a
``querystring`` (a saved search) and no resolved results -- plone.restapi does not
populate the items at serialization time; Volto fetches them separately from the
``@querystring-search`` endpoint. So this view resolves the query itself with the
``querybuilderresults`` adapter (the same plone.app.querystring machinery that
backs the endpoint) and serializes each brain via ``ISerializeToJsonSummary``,
requesting ``_all`` metadata so each item carries ``image_scales``/``image_field``
for image rendering.

When the block has no querystring configured, Volto falls back to showing the
current context's contained items (folder contents, in folder order); this view
mirrors that with a path/depth-1 catalog query.

Two variations are supported (matching Volto's built-ins): ``default`` (a simple
list of links) and ``summary`` (a card grid with preview images). Unknown
variations fall back to ``default``.
"""

from urllib.parse import urlparse

from Products.CMFCore.utils import getToolByName
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter

from plone.badisblocks.views.base import BaseBlockView
from plone.restapi.interfaces import ISerializeToJsonSummary


def _path(url):
    """Return the site-relative path of an absolute content URL."""
    if not url:
        return ""
    return urlparse(url).path or url


# Named scales (largest first) preferred for the card's ``src`` and intrinsic
# size. Volto's summary listing renders a small preview, not the full original;
# we ship no CSS, so the ``src`` scale and its width/height attributes are what
# constrain the rendered size. Fall back to the smallest available scale.
_PREVIEW_SCALE_PREFERENCE = ("preview", "teaser", "large", "mini", "thumb", "tile")

# Hint the browser to pick a card-sized scale from ``srcset`` instead of the
# default 100vw (which would download a large scale on wide viewports).
_CARD_SIZES = "(max-width: 768px) 100vw, 400px"


def _pick_preview_scale(scales):
    """Choose a small named scale for the card image.

    Prefer a known preview-sized scale; otherwise fall back to the smallest
    scale by width. Returns ``None`` when there are no usable scales.
    """
    usable = {
        name: v
        for name, v in scales.items()
        if v.get("download") and v.get("width")
    }
    if not usable:
        return None
    for name in _PREVIEW_SCALE_PREFERENCE:
        if name in usable:
            return usable[name]
    return min(usable.values(), key=lambda v: v["width"])


def _image_view_model(item):
    """Build image fields (src/srcset/alt/width/height) for a listing summary.

    Mirrors the teaser/image blocks: pick ``image_scales[image_field][0]`` and
    build a responsive ``srcset`` from its named scales. The ``src`` and intrinsic
    width/height use a small preview scale (not the full original) so the card
    image renders at a Volto-like size. Returns ``None`` when the item has no
    usable image.
    """
    field = item.get("image_field")
    scales = item.get("image_scales") or {}
    images = scales.get(field) or [] if field else []
    img = images[0] if images else None
    if not img or not img.get("download"):
        return None
    base = img.get("base_path") or _path(item.get("@id"))
    named_scales = img.get("scales") or {}
    srcset_entries = [
        f"{base}/{v['download']} {v['width']}w"
        for v in named_scales.values()
        if v.get("download") and v.get("width")
    ]
    # Use a small scale for src + intrinsic size; fall back to the original when
    # no named scales are present.
    preview = _pick_preview_scale(named_scales)
    if preview:
        src = f"{base}/{preview['download']}"
        width = preview.get("width")
        height = preview.get("height")
    else:
        src = f"{base}/{img['download']}"
        width = img.get("width")
        height = img.get("height")
    return {
        "src": src,
        "srcset": ", ".join(srcset_entries) or None,
        "sizes": _CARD_SIZES,
        "width": width,
        "height": height,
        "alt": img.get("alt") or item.get("title") or "",
    }


class ListingBlockView(BaseBlockView):
    """Render a listing block by resolving its querystring server-side."""

    default_batch_size = 25

    @staticmethod
    def _as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @property
    def headline(self):
        return (self.data or {}).get("headline") or ""

    @property
    def headline_tag(self):
        tag = (self.data or {}).get("headlineTag")
        return tag if tag in ("h2", "h3") else "h2"

    @property
    def variation(self):
        return (self.data or {}).get("variation") or "default"

    @property
    def css_class(self):
        return f"block listing variation-{self.variation}"

    @property
    def link_more_title(self):
        return (self.data or {}).get("linkTitle") or ""

    @property
    def link_more_href(self):
        href = (self.data or {}).get("linkHref") or []
        if not href:
            return ""
        first = href[0]
        # ``linkHref`` may be a resolved summary ({"@id": ...}) or a plain path.
        url = first.get("@id") if isinstance(first, dict) else first
        return _path(url)

    @property
    def show_link_more(self):
        return bool(self.link_more_title and self.link_more_href)

    def _resolve_items(self):
        querystring = (self.data or {}).get("querystring") or {}
        query = querystring.get("query")
        # Volto stores b_size/limit as strings; coerce so they can be used as
        # slice/limit integers below.
        b_size = self._as_int(querystring.get("b_size"), self.default_batch_size)
        limit = self._as_int(querystring.get("limit"), b_size)
        sort_on = querystring.get("sort_on")
        sort_order = querystring.get("sort_order")
        if sort_order:
            sort_order = "descending" if sort_order == "descending" else "ascending"
        if query:
            try:
                querybuilder = getMultiAdapter(
                    (self.context, self.request), name="querybuilderresults"
                )
            except ComponentLookupError:
                return []
            brains = querybuilder(
                query=query,
                brains=True,
                batch=False,
                b_start=0,
                b_size=b_size,
                sort_on=sort_on,
                sort_order=sort_order,
                limit=limit,
            )
        else:
            # No query configured: list the context's immediate children, the way
            # Volto shows the container's contents for an unconfigured listing.
            brains = self._context_children(sort_on, sort_order)
        # The summary serializer reads requested metadata fields from the request
        # form; request ``_all`` so image_scales/image_field are included, then
        # restore the form to avoid leaking state into the surrounding request.
        form = self.request.form
        saved = form.get("metadata_fields", None)
        form["metadata_fields"] = "_all"
        try:
            return [
                getMultiAdapter((brain, self.request), ISerializeToJsonSummary)()
                for brain in brains[:b_size]
            ]
        finally:
            if saved is None:
                form.pop("metadata_fields", None)
            else:
                form["metadata_fields"] = saved

    def _context_children(self, sort_on, sort_order):
        catalog = getToolByName(self.context, "portal_catalog")
        path = "/".join(self.context.getPhysicalPath())
        query = {
            "path": {"query": path, "depth": 1},
            "sort_on": sort_on or "getObjPositionInParent",
        }
        if sort_order:
            query["sort_order"] = sort_order
        return catalog(**query)

    @property
    def items(self):
        models = []
        for item in self._resolve_items():
            models.append({
                "url": _path(item.get("@id")),
                "title": item.get("title") or "",
                "description": item.get("description") or "",
                "image": _image_view_model(item),
            })
        return models
