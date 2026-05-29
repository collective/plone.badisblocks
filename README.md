# Plone Badisblocks

Server-side rendering of Volto/Seven blocks in Plone Classic UI ("Badis UI") with
Chameleon page templates — no frontend build step. Block-enabled content is rendered
through BrowserViews that dispatch by block `@type` to per-type `@@block-<type>` views.

See `docs/blocks-renderer-spec.md` for the architecture.

## Features

- Compatible with Plone 6.2+
- Renders block content (`volto.blocks` behavior) without a REST round-trip
- Block renderers: title, description, slate (rich text), image, gridBlock (nested),
  teaser, listing, introduction, html, slateTable, toc, video, maps, plus a default
  fallback
- Slate rich-text serializer with tag whitelisting (no unsanitized editor HTML reaches
  the page)

## Installation

Add `plone.badisblocks` to your project's dependencies:

```python
# In your pyproject.toml
dependencies = [
    "plone.badisblocks",
    # ...
]
```

Then activate the addon in your Plone site's control panel or via GenericSetup.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/collective/plone.badisblocks.git
cd plone.badisblocks

# Install in development mode (creates .venv, resolves the test extra)
uv sync --extra test
```

### Running Tests

```bash
uv run --extra test pytest
```

### Running Tests with Coverage

```bash
uv run --extra test pytest --cov=plone.badisblocks --cov-report=html
```

## License

GPL-2.0-or-later

## Author

Maik Derstappen <md@derico.de>
