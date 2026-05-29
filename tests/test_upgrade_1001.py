"""Tests for upgrade step 1000 -> 1001."""
import pytest
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from zope.component import getUtility

from plone.badisblocks.testing import INTEGRATION_TESTING


VIEWLET_MANAGER = "plone.globalstatusmessage"
VIEWLET_NAME = "voltobackendwarning"


class TestUpgrade1001:
    """Test upgrade to version 1001."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def _hidden(self):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.portal.portal_skins.getDefaultSkin()
        return storage.getHidden(VIEWLET_MANAGER, skinname)

    def test_upgrade_handler_importable(self):
        """Test the upgrade handler can be imported."""
        from plone.badisblocks.upgrades.v1001 import upgrade

        assert callable(upgrade)

    def test_upgrade_rehides_voltobackendwarning(self):
        """Upgrade reapplies the profile so stale sites get the viewlet hidden."""
        from plone.badisblocks.upgrades.v1001 import upgrade

        # Simulate a site installed before the viewlets.xml change: the
        # warning viewlet is still visible.
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.portal.portal_skins.getDefaultSkin()
        storage.setHidden(VIEWLET_MANAGER, skinname, ())
        assert VIEWLET_NAME not in self._hidden()

        upgrade(self.portal.portal_setup)

        assert VIEWLET_NAME in self._hidden()
