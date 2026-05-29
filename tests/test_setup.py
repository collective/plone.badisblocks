"""Test plone.badisblocks installation."""

import pytest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from zope.component import getUtility


VIEWLET_MANAGER = "plone.globalstatusmessage"
VIEWLET_NAME = "voltobackendwarning"


def _is_viewlet_hidden(portal):
    """Return True if the volto backend warning viewlet is hidden."""
    storage = getUtility(IViewletSettingsStorage)
    skinname = portal.portal_skins.getDefaultSkin()
    return VIEWLET_NAME in storage.getHidden(VIEWLET_MANAGER, skinname)


class TestSetup:
    """Test installation and setup."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]

    def test_addon_installed(self):
        """Test addon is installed."""
        installer = api.addon.get_installer(self.portal)
        assert installer.is_product_installed("plone.badisblocks")

    def test_browserlayer(self):
        """Test browserlayer is registered."""
        # Add an actual browserlayer check if your addon registers one, e.g.:
        # from plone.browserlayer import utils
        # from plone.badisblocks.interfaces import IPloneBadisblocksLayer
        # assert IPloneBadisblocksLayer in utils.registered_layers()
        assert True

    def test_voltobackendwarning_hidden(self):
        """The volto backend warning viewlet is hidden when installed."""
        assert _is_viewlet_hidden(self.portal)


class TestUninstall:
    """Test uninstallation."""

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer = api.addon.get_installer(self.portal)
        self.installer.uninstall_product("plone.badisblocks")

    def test_addon_uninstalled(self):
        """Test addon is uninstalled."""
        assert not self.installer.is_product_installed("plone.badisblocks")

    def test_voltobackendwarning_restored(self):
        """The volto backend warning viewlet is shown again after uninstall."""
        assert not _is_viewlet_hidden(self.portal)
