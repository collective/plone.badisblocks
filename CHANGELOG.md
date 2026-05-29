# Changelog

## 1.0.0a1 (unreleased)

- Initial release.
- Add Classic UI renderer for Volto/Seven blocks via named BrowserViews dispatching
  by block `@type`, with a Python slate serializer.
- Add block renderers: title, description, slate, image, gridBlock (nested), teaser,
  listing, introduction, html, slateTable, toc, video, maps, accordion, banner,
  `__button` (button), and carousel (a container of teaser columns re-dispatched
  into a scroll-snap viewport with Volto-style prev/next arrows and dot navigation,
  driven by a small progressive-enhancement script `static/badisblocks.js`).
- Extract the teaser image resolution into a shared `views/teaser_image.py` helper.
- Wire `@@blocks-view` as the default view for Document, News Item, and Event.
- Hide plone.volto's "voltobackendwarning" viewlet while the add-on is installed,
  since blocks are rendered in Classic UI on purpose.
- Add upgrade step 1000 → 1001 reapplying the default profile so already-installed
  sites pick up the `blocks-view` default view and the hidden backend warning.
- Fix teaser block preview image not resolving in Classic UI: re-add the site-id
  path prefix that plone.volto strips from the `preview_image` `base_path`.
