"""Verify block-enabled types use blocks-view as their default view."""
import pytest

from plone.badisblocks.testing import INTEGRATION_TESTING


class TestDefaultView:
    """The default profile sets blocks-view as default_view on core types."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]

    @pytest.mark.parametrize("type_name", ["Document", "News Item", "Event"])
    def test_default_view_is_blocks_view(self, type_name):
        fti = self.portal.portal_types[type_name]
        assert fti.default_view == "blocks-view"
        assert "blocks-view" in fti.view_methods
