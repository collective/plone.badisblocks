"""Tests for SearchBlockView view."""

import pytest
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING


PATH_OP = "plone.app.querystring.operation.string.absolutePath"


class TestViewSearchBlockView:
    """Test SearchBlockView view."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        # The real Plone request (unlike zope.publisher's TestRequest) supports
        # request.set(), which plone.restapi's summary serializer needs.
        self.request = integration["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="search-here",
            title="Search Here",
        )
        self.doc_a = api.content.create(
            container=self.folder,
            type="Document",
            id="alpha",
            title="Alpha document",
            subject=["news"],
        )
        self.doc_b = api.content.create(
            container=self.folder,
            type="Document",
            id="beta",
            title="Beta document",
            subject=["event"],
        )

    def _view(self, data, form=None):
        self.request.form.clear()
        self.request.form.update(form or {})
        view = getMultiAdapter((self.folder, self.request), name="block-search")
        view.data = data
        return view

    def _base_query_data(self, **extra):
        data = {
            "@type": "search",
            "query": {
                "query": [
                    {
                        "i": "path",
                        "o": PATH_OP,
                        "v": "/".join(self.folder.getPhysicalPath()),
                    }
                ],
            },
        }
        data.update(extra)
        return data

    def test_view_registered(self):
        view = getMultiAdapter((self.folder, TestRequest()), name="block-search")
        assert view is not None

    def test_view_name(self):
        view = getMultiAdapter((self.folder, TestRequest()), name="block-search")
        assert view.__name__ == "block-search"

    def test_headline_falls_back_to_section_title(self):
        view = self._view({"@type": "search", "sectionTitle": "Find it"})
        assert view.headline == "Find it"

    def test_build_query_includes_searchable_text(self):
        view = self._view(self._base_query_data(), form={"SearchableText": "hello"})
        criteria = view._build_query()
        assert any(
            c["i"] == "SearchableText" and c["v"] == "hello" for c in criteria
        )

    def test_build_query_includes_facet_selection(self):
        data = self._base_query_data(
            facets=[{"field": {"value": "Subject", "label": "Tags"}, "title": "Tags"}]
        )
        view = self._view(data, form={"Subject": "news"})
        criteria = view._build_query()
        assert any(
            c["i"] == "Subject" and c["v"] == ["news"] for c in criteria
        )

    def test_items_resolves_base_query(self):
        view = self._view(self._base_query_data())
        urls = {item["url"] for item in view.items}
        assert "/plone/search-here/alpha" in urls
        assert "/plone/search-here/beta" in urls

    def test_searchable_text_filters_items(self):
        view = self._view(self._base_query_data(), form={"SearchableText": "Alpha"})
        titles = {item["title"] for item in view.items}
        assert "Alpha document" in titles
        assert "Beta document" not in titles

    def test_facet_selection_filters_items(self):
        data = self._base_query_data(
            facets=[{"field": {"value": "Subject", "label": "Tags"}, "title": "Tags"}]
        )
        view = self._view(data, form={"Subject": "event"})
        titles = {item["title"] for item in view.items}
        assert titles == {"Beta document"}

    def test_facet_options_from_catalog(self):
        data = self._base_query_data(
            facets=[{"field": {"value": "Subject", "label": "Tags"}, "title": "Tags"}]
        )
        view = self._view(data)
        facets = view.facets
        assert len(facets) == 1
        values = {option["value"] for option in facets[0]["options"]}
        assert {"news", "event"}.issubset(values)

    def test_no_query_defaults_to_navigation_root(self):
        # Volto's applyDefaults falls back to "everything under the navigation
        # root" when no base query is configured; mirror that instead of showing
        # an empty result set.
        view = self._view({"@type": "search"})
        urls = {item["url"] for item in view.items}
        assert "/plone/search-here/alpha" in urls
        assert "/plone/search-here/beta" in urls

    def test_sort_options_marks_selected(self):
        data = self._base_query_data(
            showSortOn=True,
            sortOnOptions=["sortable_title", "effective"],
        )
        view = self._view(data, form={"sort_on": "effective"})
        assert view.show_sort is True
        selected = [o for o in view.sort_options if o["selected"]]
        assert len(selected) == 1
        assert selected[0]["value"] == "effective"

    def test_standalone_populates_from_request(self):
        # Put a search block on the folder, then render the view standalone
        # (no dispatcher) the way the AJAX live-filter fetch does.
        block_id = "search-1"
        self.folder.blocks = {block_id: self._base_query_data()}
        self.request.form.clear()
        self.request.form["block_id"] = block_id
        view = getMultiAdapter((self.folder, self.request), name="block-search")
        view()
        assert view.block_id == block_id
        assert view.data["@type"] == "search"
