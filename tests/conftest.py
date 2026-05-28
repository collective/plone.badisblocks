"""Pytest configuration for plone.badisblocks tests."""
from pytest_plone import fixtures_factory

from plone.badisblocks.testing import FUNCTIONAL_TESTING
from plone.badisblocks.testing import INTEGRATION_TESTING


globals().update(
    fixtures_factory(
        (
            (INTEGRATION_TESTING, "integration"),
            (FUNCTIONAL_TESTING, "functional"),
        )
    )
)
