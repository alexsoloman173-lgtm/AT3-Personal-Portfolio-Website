## Editing portfolio content

The site is generated into `index.html` from Markdown files in `content/`.

- `content/about.md` — About Me body text and sidebar metadata.
- `content/blog.md` — blog post text and downloadable PDF sidebar metadata.
- `content/resources/*.md` — each resource card, modal title, links, media, and reflection text.
- `content/references.md` — reference capture list.

Each resource Markdown file can also define a `slug:` in frontmatter. That slug becomes the resource URL fragment:

```text
#resources/your-slug
```

Example:

```markdown
---
title: Infographic
slug: infographic
---
```

This produces the resource page URL `#resources/infographic`.

Resource detail sidebars can show multiple images. In a resource frontmatter block, use `media_images` as a comma-separated list:

```markdown
---
title: Infographic
slug: infographic
media_images: clown_meme.png, principal_skinner_meme.png, bike_meme.png, salesman_meme.png
---
```

You can still use `media_image` for a single image.

To rebuild after editing Markdown:

```powershell
python scripts/build_site.py
```

The build script uses only the Python standard library. It replaces the generated regions in `index.html` between `<!-- BEGIN:... -->` and `<!-- END:... -->` markers.

Markdown images are embedded as `<figure>` blocks. Standard Markdown image syntax works:

```markdown
![Alt text](image-name.png)
```

Obsidian-style image embeds also work:

```markdown
![[image-name.png]]
```

Local Markdown image paths are checked during the build, so a missing image file will stop the rebuild with an error.

For resource reflections, all paragraphs are counted by default. If a resource contains introductory material that should not be included in the reflection word count, wrap the counted section with:

```markdown
<!-- countable-start -->

Reflection text here.

<!-- countable-end -->
```
