"""Shared upgrade step utilities for plone.badisblocks."""
from plone.app.upgrade.utils import loadMigrationProfile


def reload_gs_profile(context):
    """Reload the default GenericSetup profile."""
    loadMigrationProfile(context, "profile-plone.badisblocks:default")
