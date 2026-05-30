"""SearchBlockView browser view.

Renders the ``search`` block from volto-light-theme. In Volto this is a faceted
search that queries ``@querystring-search`` client-side and re-renders a listing;
here it renders server-side through a plain GET form so it works without
JavaScript -- a text input (``SearchableText``), one ``<select>`` per configured
facet, and an optional sort dropdown. Submitting reloads the page with the
filter applied.

The block stores a base query in ``data["query"]`` (a querystring object: a list
of ``{i, o, v}`` criteria plus ``sort_on``/``sort_order``/``b_size``). This view
resolves that base query -- extended with the live ``SearchableText`` and facet
selections read from the request -- through the ``querybuilderresults`` adapter
(the same plone.app.querystring machinery behind the endpoint) and serialises
each brain via ``ISerializeToJsonSummary`` with ``_all`` metadata, exactly like
the listing block, then renders the listing card markup. When no base query is
configured (the common case -- the editor leaves it empty), it falls back to
"everything under the navigation root", mirroring Volto's ``applyDefaults``;
without this the block would render empty.

Facets come from ``data["facets"]``; each one's ``field.value`` is a catalog
index name. The available options are collected from the result brains' metadata
column of that name (NOT ``catalog.uniqueValuesFor``, which returns nothing for a
``KeywordIndex`` like ``Subject`` here). A facet selection is added to the query
as a ``selection.any`` criterion on that index.

Live filtering: badisblocks.js fetches this same view standalone
(``<context>/@@block-search?block_id=…&SearchableText=…``) and swaps the
``.search-block-results`` fragment in place, keeping the query logic server-side.
When rendered standalone the dispatcher hasn't filled ``data``, so ``__call__``
self-populates it from the context's blocks using ``block_id``.
"""

from Missing import Value as MISSING
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter

from plone.badisblocks.views.base import BaseBlockView
from plone.badisblocks.views.listing_block_view import _image_view_model
from plone.badisblocks.views.listing_block_view import _path
from plone.base.navigationroot import get_navigation_root
from plone.restapi.interfaces import ISerializeToJsonSummary


SEARCHABLE_TEXT_OP = "plone.app.querystring.operation.string.contains"
SELECTION_ANY_OP = "plone.app.querystring.operation.selection.any"
ABSOLUTE_PATH_OP = "plone.app.querystring.operation.string.absolutePath"


class SearchBlockView(BaseBlockView):
    """Render the search block as a server-side GET-form search."""

    default_batch_size = 25

    # -- block data -----------------------------------------------------------

    @property
    def headline(self):
        data = self.data or {}
        return data.get("headline") or data.get("sectionTitle") or ""

    @property
    def show_search_input(self):
        data = self.data or {}
        return data.get("showSearchInput", True)

    @property
    def search_input_prompt(self):
        return (self.data or {}).get("searchInputPrompt") or ""

    @property
    def _query_config(self):
        # ``data["query"]`` is normally a querystring object ({query: [...],
        # sort_on, b_size, …}); tolerate it being just the criteria list too.
        query = (self.data or {}).get("query")
        if isinstance(query, dict):
            return query
        if isinstance(query, list):
            return {"query": query}
        return {}

    @property
    def _facet_settings(self):
        return [f for f in ((self.data or {}).get("facets") or []) if f.get("field")]

    # -- request-driven filter state -----------------------------------------

    def _param(self, name):
        value = self.request.form.get(name)
        return value.strip() if isinstance(value, str) else ""

    def _param_list(self, name):
        value = self.request.form.get(name)
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [v for v in value if v]
        value = value.strip()
        return [value] if value else []

    @property
    def search_text(self):
        return self._param("SearchableText")

    @staticmethod
    def _as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @property
    def form_action(self):
        return self.context.absolute_url()

    @property
    def block_url(self):
        """URL of this view for the AJAX live-filter fetch (JS appends params)."""
        return f"{self.context.absolute_url()}/@@block-search"

    def __call__(self):
        if self.data is None:
            self._populate_from_request()
        return self.index()

    def _populate_from_request(self):
        """Fill ``data``/``block_id`` when rendered standalone (AJAX fetch).

        Resolve the block from the context's blocks by ``block_id``, falling back
        to the first search block on the page (mirrors the event calendar block).
        """
        block_id = self.request.form.get("block_id") or ""
        blocks = getattr(self.context, "blocks", None) or {}
        data = blocks.get(block_id) if block_id else None
        if data is None:
            for bid, block in blocks.items():
                if isinstance(block, dict) and block.get("@type") == "search":
                    block_id, data = bid, block
                    break
        self.block_id = block_id
        self.data = data or {}

    # -- query ----------------------------------------------------------------

    @property
    def _sort_on(self):
        return self._param("sort_on") or self._query_config.get("sort_on") or ""

    @property
    def _sort_order(self):
        order = self._query_config.get("sort_order")
        return "descending" if order == "descending" else "ascending"

    def _default_criteria(self):
        """Volto's fallback when no base query is configured: everything under
        the navigation root (see ``applyDefaults`` in Volto's SearchBlockView)."""
        root = get_navigation_root(self.context)
        return [{"i": "path", "o": ABSOLUTE_PATH_OP, "v": root}]

    def _base_criteria(self):
        """Configured base query extended with the live text search (no facets)."""
        criteria = list(self._query_config.get("query") or [])
        if not criteria:
            criteria = self._default_criteria()
        if self.search_text:
            criteria.append(
                {"i": "SearchableText", "o": SEARCHABLE_TEXT_OP, "v": self.search_text}
            )
        return criteria

    def _facet_criteria(self):
        """Criteria for the currently selected facet values."""
        criteria = []
        for facet in self._facet_settings:
            name = facet["field"].get("value")
            selected = self._param_list(name) if name else []
            if selected:
                criteria.append({"i": name, "o": SELECTION_ANY_OP, "v": selected})
        return criteria

    def _build_query(self):
        """Base query criteria extended with text search and facet selections."""
        return self._base_criteria() + self._facet_criteria()

    def _run_querybuilder(self, query, b_size):
        if not query:
            return []
        try:
            querybuilder = getMultiAdapter(
                (self.context, self.request), name="querybuilderresults"
            )
        except ComponentLookupError:
            return []
        try:
            return querybuilder(
                query=query,
                brains=True,
                batch=False,
                b_start=0,
                b_size=b_size,
                sort_on=self._sort_on or None,
                sort_order=self._sort_order,
                limit=b_size,
            )
        except Exception:
            # An invalid criterion (e.g. unknown index) must not break the page.
            return []

    def _resolve_items(self):
        b_size = self._as_int(self._query_config.get("b_size"), self.default_batch_size)
        brains = self._run_querybuilder(self._build_query(), b_size)
        if not brains:
            return []
        # The summary serializer reads requested metadata from the request form;
        # ask for ``_all`` so image_scales/image_field are included, then restore
        # the form so we don't leak state into the surrounding request.
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

    # -- view model -----------------------------------------------------------

    @property
    def items(self):
        models = []
        for item in self._resolve_items():
            models.append({
                "url": _path(item.get("@id")),
                "head_title": item.get("head_title") or "",
                "title": item.get("title") or "",
                "description": item.get("description") or "",
                "image": _image_view_model(item),
            })
        return models

    # Cap on how many brains are scanned to build facet option lists, so a huge
    # base query can't make rendering the dropdowns unbounded.
    facet_scan_limit = 1000

    def _facet_source_brains(self):
        """Brains for the base query (text search applied, facets not), used to
        derive the available facet values -- so options reflect the full scope the
        user can narrow within, independent of the current facet selection."""
        if not hasattr(self, "_facet_brains_cache"):
            self._facet_brains_cache = self._run_querybuilder(
                self._base_criteria(), self.facet_scan_limit
            )
        return self._facet_brains_cache

    def _facet_options(self, index_name):
        """Distinct values for a facet, collected from the result brains.

        The catalog metadata column is assumed to share the index's name (true for
        the usual facet fields: ``Subject``, ``portal_type``, ``review_state`` …).
        Both keyword (sequence) and single-value columns are handled.
        """
        values = set()
        for brain in self._facet_source_brains():
            try:
                value = getattr(brain, index_name)
            except (AttributeError, KeyError):
                continue
            if value is MISSING:
                continue
            if isinstance(value, (list, tuple, set)):
                values.update(str(v) for v in value if v not in (None, ""))
            elif value not in (None, ""):
                values.add(str(value))
        return sorted(values)

    @property
    def facets(self):
        models = []
        for facet in self._facet_settings:
            field = facet["field"]
            name = field.get("value")
            if not name:
                continue
            selected = set(self._param_list(name))
            options = [
                {"value": value, "label": value, "selected": value in selected}
                for value in self._facet_options(name)
            ]
            models.append({
                "name": name,
                "title": facet.get("title") or field.get("label") or name,
                "multiple": bool(facet.get("multiple")),
                "options": options,
            })
        return models

    @property
    def show_sort(self):
        data = self.data or {}
        return bool(data.get("showSortOn")) and bool(self.sort_options)

    @property
    def sort_options(self):
        raw = (self.data or {}).get("sortOnOptions") or []
        current = self._sort_on
        options = []
        for entry in raw:
            if isinstance(entry, dict):
                value = entry.get("value") or entry.get("id") or ""
                label = entry.get("label") or value
            else:
                value = label = entry
            if not value:
                continue
            options.append({
                "value": value,
                "label": label,
                "selected": value == current,
            })
        return options
