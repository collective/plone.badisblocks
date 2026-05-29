# Spec: Chameleon renderer for Volto/Seven blocks in Classic UI (Badis UI)

## Goal

Render content created by the Volto/Seven block editor inside Plone Classic UI
("Badis UI") using Chameleon page templates. No frontend build step — pure
server-side rendering through BrowserViews and `.pt` templates.

Reference implementation (SvelteKit prototype) being ported:
`/home/maik/develop/svelteplayground/svolto/` — see `src/lib/RenderBlocks.svelte`,
`RenderBlock.svelte`, `blocks/index.ts`, and `blocks/{title,description,image,slate,grid}/`.

## Data source

Block-enabled content carries the `volto.blocks` behavior
(`plone.restapi.behaviors.IBlocks`), which stores two attributes directly on the
content object:

- `context.blocks` — `dict` mapping a block UID → block data (`{"@type": ..., ...}`)
- `context.blocks_layout` — `{"items": [<uid>, <uid>, ...]}` giving render order

A BrowserView reads these directly; no REST round-trip.

## Architecture — named-BrowserView registry

Mirrors the svolto `blocksConfig` registry in Zope idiom. One entry view dispatches
by block `@type` to a per-type view named `@@block-<type>`; unknown types fall back
to `@@block-default`. The grid view re-uses the same dispatch over its own nested
blocks (the "nested views" requirement).

```
@@blocks-view                 entry; iterates blocks_layout["items"]
 ├─ @@block-title             context.title       -> <h1 class="documentFirstHeading">
 ├─ @@block-description       context.description -> <p class="documentDescription">
 ├─ @@block-slate             data["value"]       -> Python serializer -> structure
 ├─ @@block-image             data image_scales/url/alt -> <img srcset>
 ├─ @@block-gridBlock         data blocks/blocks_layout -> re-dispatch (nested)
 ├─ @@block-teaser            data["href"][0] target -> linked card
 ├─ @@block-listing          catalog query -> list of items
 ├─ @@block-introduction      data["value"] (slate) -> lead paragraph
 ├─ @@block-html              data["html"] -> raw HTML
 ├─ @@block-slateTable        data["table"] -> <table>
 ├─ @@block-toc               slate headings -> anchored ToC
 ├─ @@block-video             data["url"] -> responsive embed
 ├─ @@block-maps              data["url"] -> responsive map iframe
 ├─ @@block-accordion         data["data"] blocks/blocks_layout -> <details> panels (nested)
 └─ @@block-default           fallback
```

### Dispatch

- `BaseBlockView(BrowserView)` — carries `data`, `block_id`, `block_type` set by the
  dispatcher before render.
- `BlockDispatchMixin` — provides:
  - `render_blocks(blocks, items)` → concatenated HTML of all blocks in order.
  - `render_block(block_id, blocks)` → resolve `@type`, look up the sub-view via
    `getMultiAdapter((context, request), name="block-<type>")` (fallback
    `block-default`), set `.data`/`.block_id`/`.block_type`, return `view()`.
- `BlocksView(BrowserView, BlockDispatchMixin)` — entry point `@@blocks-view`. Template
  iterates `view.block_ids` and injects each via `tal:content="structure ..."`.
- `GridBlockView(BaseBlockView, BlockDispatchMixin)` — re-dispatches over
  `data["blocks"]` / `data["blocks_layout"]["items"]`.

## Block data enrichment (stored vs serialized) — important

`context.blocks` is the *raw stored* form, which is under-populated for rendering:
image blocks hold `url: "resolveuid/<uid>"` with **no** `image_scales`; slate links
and teaser hrefs hold unresolved UIDs. plone.restapi only enriches these at REST GET
time via `IBlockFieldSerializationTransformer` adapters (resolve UIDs → urls, attach
`image_scales` from the catalog brain, etc.).

So `BlocksView.render()` runs those same transformers first via
`views/serializer.py:serialize_blocks` (the exact logic of restapi's
`BlocksJSONFieldSerializer`, recursing into nested grid blocks through `visit_blocks`).
Without this, image blocks render empty. The transformers are looked up via
`zope.globalrequest.getRequest()`, which is set during a real request (and must be set
manually in tests).

## Per-block specs

| View | Reads | Renders |
|---|---|---|
| `@@block-title` | `context.title` | `<h1 class="documentFirstHeading">` |
| `@@block-description` | `context.description` (or block `data`) | `<p class="documentDescription">` |
| `@@block-slate` | `data["value"]` (node tree) | escaped HTML via serializer |
| `@@block-image` | `data["image_scales"]`, `data["url"]`, `data["alt"]` | `<img>` with `srcset` |
| `@@block-gridBlock` | `data["headline"]`, `data["blocks"]`, `data["blocks_layout"]` | nested blocks in a Bootstrap `row row-cols-1 row-cols-md-{n}` (Barceloneta ships the CSS; responsive, stacks on mobile) |
| `@@block-teaser` | `data["href"][0]` target + block fields | optional image, kicker, title, description, linked to target |
| `@@block-default` | — | nothing visible (type name in dev) |

### Slate serializer (the hard part)

Volto stores slate as a recursive JSON node tree. Inline formatting (strong/em/link)
are **element** nodes with `children`, not leaf marks; text nodes carry only `text`.

`browser/slate.py` walks the tree:

- text node (`"text" in node`) → `html.escape(node["text"])`
- element node → whitelist `node["type"]` to a tag; recurse over `children`;
  unknown types are dropped (children still rendered) — never emit raw editor markup.
- Whitelisted tags: `p, h2, h3, h4, h5, h6, blockquote, ul, ol, li, strong, em,
  u/underline, s/strikethrough, del, sub, sup, code, a (link), br`.
- Links: emit `href` from `node["data"]["url"]` as-is; Plone resolves
  `resolveuid/<uid>` via traversal.

Returns a plain string; template injects with `tal:content="structure view/render"`.
**Security:** every text leaf is escaped and only whitelisted tags are emitted, so no
unsanitized editor HTML reaches the page.

### Image

Base path = `data["url"]` with host stripped to a path. `image_scales["image"][0]`
gives `download`, `width`, `height`, and `scales` (each `{download, width}`). Build
`src = base + "/" + download` and `srcset` from the scales. `alt` from `data["alt"]`.

## Entry-point wiring (replace default view immediately)

- `profiles/default/types.xml` lists `Document`, `News Item`, `Event`; the matching
  per-type files set `default_view` → `blocks-view` and append it to `view_methods`
  (`purge="False"`).
- **Filename rule:** GenericSetup maps spaces in the FTI id to underscores for the
  filename, so the News Item file must be `types/News_Item.xml` (not `News Item.xml`).
- **Upgrade step 1000 → 1001** (`src/plone/badisblocks/upgrades/v1001.py`) reapplies the
  default profile via `loadMigrationProfile` so already-installed sites pick up both the
  FTI `default_view` change and the hidden `voltobackendwarning` viewlet. Add a new
  `plonecli add upgrade_step` for any future profile change that must reach live sites.
- **Caveat:** this makes *all* Documents/News Items/Events render through
  `@@blocks-view`. Content without `blocks_layout` renders an empty content-core (the
  renderer returns `""`). Fine for a blocks-first site; revisit with a fallback if the
  site mixes classic richtext content.
- **Hide the Volto backend warning:** `profiles/default/viewlets.xml` hides
  `plone.volto`'s `voltobackendwarning` viewlet (manager `plone.globalstatusmessage`,
  `skinname="*"`) since blocks are rendered in Classic UI on purpose; the uninstall
  profile restores it with `remove="True"`. Done via the `plone.app.viewletmanager`
  hidden-viewlet registry rather than a layer override, because `IPloneBadisblocksLayer`
  and `IPloneVoltoCoreLayer` are sibling layers (both extend `IDefaultBrowserLayer`),
  so adapter specificity between them is ambiguous.

## Testing (pytest-plone, already configured)

Per-block tests under `tests/`: build a Document with representative
`blocks`/`blocks_layout`, render `@@blocks-view`, assert HTML — heading text, escaped
slate output, image `srcset`, nested grid columns, unknown-type fallback. Real tests
only (no throwaway verification scripts). Run via `plonecli test` / `uv run`.

## Implementation phases

- **Phase 0** — Scaffold views with plonecli (`blocks-view`, `block-default`,
  `block-title`, `block-description`, `block-slate`, `block-image`, `block-grid`).
- **Phase 1** — Dispatch core (`BaseBlockView`, `BlockDispatchMixin`, `BlocksView`).
- **Phase 2** — Simple blocks: title, description, slate (+ serializer), image, default.
- **Phase 3** — Grid (nested re-dispatch).
- **Phase 4** — Wire `blocks-view` as default view via FTI (`types.xml` +
  `types/{Document,News_Item,Event}.xml`).
- **Phase 5** — Tests per block.

All phases implemented; full suite green (`uv run --extra test pytest`) and
`ruff check` clean.

## Implemented block views

All blocks from the svolto reference are now ported. Each has a per-type named view
(`@@block-<type>`) registered in `views/configure.zcml`, a `.pt` template, and a
per-block test under `tests/test_view_<name>_block_view.py`.

| View | Reads | Renders |
|---|---|---|
| `@@block-title` | `context.title` | `<h1 class="documentFirstHeading">` |
| `@@block-description` | `context.description` (or block `data`) | `<p class="documentDescription">` |
| `@@block-slate` | `data["value"]` (node tree) | escaped HTML via `slate.py` serializer |
| `@@block-image` | `data["image_scales"]`, `data["url"]`, `data["alt"]` | `<img>` with `srcset` |
| `@@block-gridBlock` | `data["blocks"]`, `data["blocks_layout"]` | nested re-dispatch in a Bootstrap `row` |
| `@@block-teaser` | `data["href"][0]` target + block fields | optional image, kicker, title, description, linked to target |
| `@@block-listing` | catalog query / `data["querystring"]` results | list of items aligned with volto-light-theme markup |
| `@@block-introduction` | `data["value"]` (slate) | intro/lead paragraph via slate serializer |
| `@@block-html` | `data["html"]` | raw HTML passthrough |
| `@@block-slateTable` | `data["table"]` (rows/cells of slate) | `<table>` with serialized cell content |
| `@@block-toc` | document slate headings | anchored table-of-contents list |
| `@@block-video` | `data["url"]` (YouTube/Vimeo/file) | responsive embed / `<video>` |
| `@@block-maps` | `data["url"]` (embed src) | responsive map iframe |
| `@@block-accordion` | `data["data"]["blocks"]`, `data["data"]["blocks_layout"]`, panel `title`, `collapsed`, `non_exclusive` | native `<details>`/`<summary>` panels, nested re-dispatch |
| `@@block-default` | — | nothing visible (type name in dev) |

`@@block-teaser` reads the resolved target from `data["href"][0]` (or block fields
when `overwrite` is true), renders an optional image (from `preview_image` or the
target's `image_scales[image_field]`), kicker, title, description, and links to the
target path; with no resolvable target it renders title/description without a link.

**Image path caveat:** a `preview_image`'s `base_path` is produced by `plone.volto`'s
`PreviewImageScalesFieldAdapter` as `linked_image.absolute_url().replace(portal_url, "")`
— navigation-root relative (site-id prefix stripped), which is what Volto serves but not
Classic UI. `image_base_path` re-adds the portal path prefix (`urlparse(portal.absolute_url()).path`,
e.g. `/Plone`, empty under VHM) so the `@@images` URL resolves. The `image_scales[image_field]`
fallback uses the target `@id` path, which already carries the prefix.

## Styling (CSS)

The renderers otherwise inherit Barceloneta, but ship one small stylesheet,
`static/badisblocks.css`, registered as the `++resource++plone.badisblocks`
resource directory and linked into the document head by an `IHtmlHead` viewlet
bound to `IPloneBadisblocksLayer` (so it loads only when the addon is installed
and applies on restart, with no GenericSetup reimport). It covers two things CSS
must own:

- **Listing** — the semantic `<ul>` would otherwise render with disc markers and
  a 32px indent; the stylesheet drops both, owns the inter-item spacing, and lays
  out the summary variation as image-beside-text (stacking under 768px).
- **Block alignment** — `@@block-video` and `@@block-maps` emit a
  `has--align--<value>` class (from `data["styles"]["align"]`, falling back to
  `data["align"]`, default `full`), mirroring Volto. The stylesheet backs those
  classes with volto-light-theme's model (`theme/_layout.scss`): `center` →
  narrow (620px), `wide` → 940px, `full` → full content width, each centered;
  `left`/`right` float the embed to the side at 50% width with content wrapping
  beside it (and stack full-width under 768px). Both embeds get a 16:9 box since
  the iframes/`<video>` carry no intrinsic size. The `css_class` derivation is
  covered by the video/maps view tests.

## Out of scope / future work

- `column`/`listing` template variations beyond the default markup.
- Search block and other add-on blocks not present in the svolto reference.
  (see "Entry-point wiring" above — only needed once the addon is released).
