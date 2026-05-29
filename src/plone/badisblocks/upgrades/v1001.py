"""Reimport typeinfo and viewlets."""
import logging

from .base import reload_gs_profile

logger = logging.getLogger(__name__)


def upgrade(context):
    """Apply blocks-view default_view and hide voltobackendwarning on installed sites

    Upgrade from profile version 1000 to 1001.
    """
    logger.info("Running upgrade step: Reimport typeinfo and viewlets")
    reload_gs_profile(context)
