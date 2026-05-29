"""Tests that the renderer enriches stored blocks like plone.restapi does.

Stored Volto blocks hold raw references (``resolveuid/<uid>`` urls, no
``image_scales``); the renderer must run the restapi serialization transformers
so e.g. image blocks resolve to a usable url. See views/serializer.py.
"""

import pytest
from zope.globalrequest import setRequest

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.badisblocks.testing import INTEGRATION_TESTING
from plone.badisblocks.views.serializer import serialize_blocks
from plone.uuid.interfaces import IUUID


class TestBlockSerialization:
    """serialize_blocks runs restapi IBlockFieldSerializationTransformer handlers."""

    layer = INTEGRATION_TESTING

    @pytest.fixture(autouse=True)
    def _setup(self, integration):
        self.portal = integration["portal"]
        self.request = integration["request"]
        # Transformers are looked up via zope.globalrequest.getRequest().
        setRequest(self.request)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        yield
        setRequest(None)

    def test_resolveuid_url_in_block_is_resolved(self):
        target = api.content.create(
            container=self.portal, type="Document", id="target", title="Target"
        )
        uid = IUUID(target)
        blocks = {"a": {"@type": "image", "url": f"resolveuid/{uid}"}}

        result = serialize_blocks(self.portal, blocks)

        assert result["a"]["url"] != f"resolveuid/{uid}"
        assert result["a"]["url"].endswith("/target")

    def test_resolveuid_url_in_nested_grid_block_is_resolved(self):
        target = api.content.create(
            container=self.portal, type="Document", id="target2", title="Target2"
        )
        uid = IUUID(target)
        blocks = {
            "g": {
                "@type": "gridBlock",
                "blocks": {"c1": {"@type": "image", "url": f"resolveuid/{uid}"}},
                "blocks_layout": {"items": ["c1"]},
            }
        }

        result = serialize_blocks(self.portal, blocks)

        assert result["g"]["blocks"]["c1"]["url"].endswith("/target2")
