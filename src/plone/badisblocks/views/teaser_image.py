"""Resolve a teaser-style image (preview_image override or target scales).

Shared by the teaser block and the slider block, whose slides are themselves
teasers. An overwritten ``preview_image`` wins; otherwise the target's
``image_scales[image_field]`` is used. The base path re-adds the site-id prefix
that plone.volto's preview-image adapter strips (it stores ``base_path``
navigation-root relative, which Volto serves but Classic UI does not), or falls
back to the target ``@id`` path.
"""

from urllib.parse import urlparse

from plone import api


def resolve_image(preview_image, target):
    """Return the raw image dict (preview override or target scales), or None."""
    if preview_image:
        return preview_image[0]
    target = target or {}
    field = target.get("image_field")
    scales = target.get("image_scales") or {}
    if field and scales.get(field):
        return scales[field][0]
    return None


def image_base_path(image, target):
    """Return the path the image's ``download``/scales are relative to."""
    base = (image or {}).get("base_path")
    if base:
        prefix = urlparse(api.portal.get().absolute_url()).path
        return f"{prefix}{base}"
    url = (target or {}).get("@id")
    return urlparse(url).path if url else ""


def teaser_image(preview_image, target):
    """Return ``{src, srcset, alt}`` for a teaser image, or None when absent."""
    image = resolve_image(preview_image, target)
    if not image or not image.get("download"):
        return None
    base = image_base_path(image, target)
    scales = image.get("scales") or {}
    srcset = (
        ", ".join(
            f"{base}/{v['download']} {v['width']}w"
            for v in scales.values()
            if v.get("download") and v.get("width")
        )
        or None
    )
    return {
        "src": f"{base}/{image['download']}",
        "srcset": srcset,
        "alt": image.get("alt") or "",
    }
