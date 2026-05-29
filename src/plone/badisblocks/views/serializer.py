"""Apply plone.restapi block serialization transforms for Classic UI rendering.

Volto blocks are stored in a *raw* form: image blocks hold a ``resolveuid/<uid>``
reference with no ``image_scales``, slate links hold unresolved UIDs, teaser blocks
hold an unresolved ``href``. plone.restapi enriches these at GET time via
``IBlockFieldSerializationTransformer`` adapters (resolving UIDs, attaching
``image_scales`` from the catalog brain, etc.). Reading ``context.blocks`` directly
therefore yields under-populated blocks (e.g. images render empty).

This runs the same transformers — the exact logic of restapi's
``BlocksJSONFieldSerializer`` — so the renderer sees the data the frontend receives.
Transforms recurse into nested blocks (e.g. grid columns) via ``visit_blocks``.
"""

import copy

from plone.restapi.blocks import iter_block_transform_handlers
from plone.restapi.blocks import visit_blocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from plone.restapi.serializer.converters import json_compatible


def serialize_blocks(context, blocks):
    """Return an enriched, JSON-compatible copy of ``blocks``."""
    value = copy.deepcopy(blocks or {})
    for block in visit_blocks(context, value):
        new_block = block.copy()
        for handler in iter_block_transform_handlers(
            context, block, IBlockFieldSerializationTransformer
        ):
            new_block = handler(new_block)
        block.clear()
        block.update(new_block)
    return json_compatible(value)
