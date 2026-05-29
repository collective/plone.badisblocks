# Changelog

## 1.0.0a1 (unreleased)

- Initial release.
- Add Classic UI renderer for Volto/Seven blocks via named BrowserViews dispatching
  by block `@type`, with a Python slate serializer.
- Add block renderers: title, description, slate, image, gridBlock (nested), teaser,
  listing, introduction, html, slateTable, toc, video, and maps.
- Wire `@@blocks-view` as the default view for Document, News Item, and Event.
