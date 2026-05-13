from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import unquote
from typing import Dict, List, Tuple
from html.parser import HTMLParser
from math import ceil

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
INDEX_FILE = ROOT / "index.html"


def attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(value: object) -> str:
    return html.escape(str(value), quote=False)


def as_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_frontmatter(path: Path) -> Tuple[Dict[str, object], str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        return {}, raw

    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"Unclosed frontmatter in {path}")

    frontmatter = parts[0].splitlines()[1:]
    body = parts[1]
    data: Dict[str, object] = {}

    for line in frontmatter:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"Invalid frontmatter line in {path}: {line}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() == "true":
            data[key] = True
        elif value.lower() == "false":
            data[key] = False
        else:
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            data[key] = value

    return data, body.strip("\n")


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
MARKDOWN_IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\((.+)\)\s*$")
WIKI_IMAGE_RE = re.compile(r"^!\[\[([^\]]+)\]\]\s*$")
ORDERED_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
SLUG_RE = re.compile(r"[^a-z0-9]+")
HTML_BLOCK_TAG_RE = re.compile(r"^</?(?:div|iframe|section|article|aside|figure|figcaption|video|audio|details|summary|pre|code|table|thead|tbody|tr|td|th|ul|ol|li|blockquote|h[1-6])(?:\s|>|$)", re.IGNORECASE)
READING_SPEED_WPM = 220


class StatsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.frames: List[Dict[str, object]] = []
        self.countable_words: Dict[str, List[str]] = {}
        self.reflection_words: Dict[str, List[str]] = {}

    def handle_starttag(self, tag: str, attrs_list: List[Tuple[str, str | None]]) -> None:
        attrs = {name: (value or "") for name, value in attrs_list}
        parent = self.frames[-1] if self.frames else {"skip": False, "count_id": None, "reflection_id": None}

        count_id = parent["count_id"]
        classes = attrs.get("class", "").split()
        data_count_id = attrs.get("data-count-id")
        if "countable" in classes and data_count_id:
            count_id = data_count_id

        reflection_id = parent["reflection_id"]
        if attrs.get("data-word-count-id"):
            reflection_id = attrs["data-word-count-id"]

        skip = bool(parent["skip"] or tag in {"script", "style"})
        hidden_count_span = bool(tag == "span" and reflection_id and attrs.get("id") == reflection_id)

        self.frames.append(
            {
                "skip": skip,
                "count_id": count_id,
                "reflection_id": reflection_id,
                "hidden_count_span": hidden_count_span,
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if self.frames:
            self.frames.pop()

    def handle_data(self, data: str) -> None:
        if not self.frames:
            return

        frame = self.frames[-1]
        if frame["skip"] or frame["hidden_count_span"]:
            return

        count_id = frame["count_id"]
        if count_id:
            self.countable_words.setdefault(str(count_id), []).append(data)

        reflection_id = frame["reflection_id"]
        if reflection_id:
            self.reflection_words.setdefault(str(reflection_id), []).append(data)


def count_words(text_value: str) -> int:
    return len([token for token in re.split(r"\s+", text_value.strip()) if token])


def format_reading_label(words: int) -> str:
    word_label = "word" if words == 1 else "words"
    minutes = max(1, ceil(words / READING_SPEED_WPM)) if words else 0
    minute_label = "min" if minutes == 1 else "mins"
    return f"{words} {word_label} · {minutes} {minute_label} read"


def build_word_counts_label_map(html_source: str) -> Dict[str, str]:
    parser = StatsParser()
    parser.feed(html_source)

    counts: Dict[str, int] = {
        count_id: count_words(" ".join(chunks))
        for count_id, chunks in parser.countable_words.items()
    }

    for reflection_id, chunks in parser.reflection_words.items():
        if counts.get(reflection_id, 0) > 0:
            continue
        counts[reflection_id] = count_words(" ".join(chunks))

    return {count_id: format_reading_label(total) for count_id, total in counts.items()}


def apply_word_count_labels(html_source: str, labels: Dict[str, str]) -> str:
    span_re = re.compile(r'<span(?P<attrs>[^>]*\sid="(?P<id>[^"]+)"[^>]*)>(?P<content>[^<]*)</span>')

    def replace_span(match: re.Match[str]) -> str:
        count_id = match.group("id")
        if count_id not in labels:
            return match.group(0)
        return f'<span{match.group("attrs")}>{text(labels[count_id])}</span>'

    return span_re.sub(replace_span, html_source)


def is_external_url(src: str) -> bool:
    return src.startswith(("http://", "https://", "data:"))


def filename_to_alt(src: str) -> str:
    clean_src = src.split("#", 1)[0].split("?", 1)[0]
    name = Path(clean_src).stem or clean_src
    return name.replace("_", " ").replace("-", " ").strip().capitalize()


def strip_optional_title(src: str) -> str:
    src = src.strip()
    if src.startswith("<") and ">" in src:
        return src[1 : src.index(">")].strip()
    title_match = re.match(r"^(?P<src>.+?)\s+(?P<quote>[\"']).*(?P=quote)$", src)
    if title_match:
        return title_match.group("src").strip()
    return src


def parse_image_line(line: str) -> Tuple[str, str, str]:
    stripped = line.strip()

    markdown_match = MARKDOWN_IMAGE_RE.match(stripped)
    if markdown_match:
        alt_caption = markdown_match.group(1).strip()
        src = strip_optional_title(markdown_match.group(2))
        alt_text = alt_caption or filename_to_alt(src)
        caption = ""
        if "|" in alt_caption:
            alt_text, caption = [part.strip() for part in alt_caption.split("|", 1)]
        return src, alt_text, caption

    wiki_match = WIKI_IMAGE_RE.match(stripped)
    if wiki_match:
        target = wiki_match.group(1).strip()
        caption = ""
        if "|" in target:
            src, caption = [part.strip() for part in target.split("|", 1)]
            alt_text = caption if caption and not re.fullmatch(r"\d+(?:x\d+)?", caption) else filename_to_alt(src)
            caption = "" if re.fullmatch(r"\d+(?:x\d+)?", caption) else caption
        else:
            src = target
            alt_text = filename_to_alt(src)
        return src, alt_text, caption

    raise ValueError(f"Invalid image line: {line}")


def validate_image_src(src: str) -> None:
    if is_external_url(src) or src.startswith("#"):
        return

    clean_src = unquote(src.split("#", 1)[0].split("?", 1)[0])
    if not clean_src:
        return

    candidate = (ROOT / clean_src).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return

    if not candidate.exists():
        raise FileNotFoundError(f"Markdown image not found: {clean_src}")


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return slug or "resource"


def resource_slug(meta: Dict[str, object]) -> str:
    return str(meta.get("slug") or slugify(str(meta.get("title", "resource"))))


def split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def resource_media_images(meta: Dict[str, object]) -> List[str]:
    images: List[str] = []

    if meta.get("media_images"):
        images.extend(split_csv(str(meta.get("media_images", ""))))
    elif meta.get("media_image"):
        images.append(str(meta.get("media_image")))

    for index in range(2, 10):
        key = f"media_image_{index}"
        if meta.get(key):
            images.append(str(meta.get(key)))

    unique_images: List[str] = []
    for image in images:
        if image not in unique_images:
            validate_image_src(image)
            unique_images.append(image)

    return unique_images


def render_inline(markdown: str) -> str:
    def link_repl(match: re.Match[str]) -> str:
        label = render_inline(match.group(1))
        href = match.group(2).strip()
        extra = ""
        if href.startswith("http://") or href.startswith("https://"):
            extra = ' target="_blank" rel="noreferrer"'
        return f'<a href="{attr(href)}"{extra}>{label}</a>'

    rendered = LINK_RE.sub(link_repl, markdown)
    rendered = EM_RE.sub(r"<em>\1</em>", rendered)
    return rendered


def paragraph_html(parts: List[str], countable: bool, count_id: str | None) -> str:
    content = " ".join(part.strip() for part in parts).strip()
    content = content.replace("  ", " ")
    class_attr = f' class="countable" data-count-id="{attr(count_id)}"' if countable and count_id else ""
    return f"<p{class_attr}>{render_inline(content)}</p>"


def split_table_row(line: str) -> List[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def render_table(lines: List[str]) -> str:
    headers = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    out = ["<table>", "  <thead>", "    <tr>"]
    for header in headers:
        out.append(f"      <th>{render_inline(header)}</th>")
    out.extend(["    </tr>", "  </thead>", "  <tbody>"])
    for row in rows:
        out.append("    <tr>")
        for cell in row:
            out.append(f"      <td>{render_inline(cell)}</td>")
        out.append("    </tr>")
    out.extend(["  </tbody>", "</table>"])
    return "\n".join(out)


def render_image(line: str) -> str:
    src, alt_text, caption = parse_image_line(line)
    validate_image_src(src)
    referrer = ' referrerpolicy="no-referrer"' if src.startswith(("http://", "https://")) else ""
    out = ["<figure>"]
    out.append(f'  <img class="resource-card-image" src="{attr(src)}" alt="{attr(alt_text)}" loading="eager"{referrer} />')
    if caption:
        out.append(f"  <figcaption>{render_inline(caption)}</figcaption>")
    out.append("</figure>")
    return "\n".join(out)


def is_html_block_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("<!--"):
        return False
    return bool(HTML_BLOCK_TAG_RE.match(stripped))


def render_blocks(markdown: str, *, count_id: str | None = None, countable_default: bool = False) -> str:
    lines = markdown.splitlines()
    out: List[str] = []
    paragraph: List[str] = []
    i = 0
    countable = countable_default

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(paragraph_html(paragraph, countable, count_id))
            paragraph = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == "<!-- countable-start -->":
            flush_paragraph()
            countable = True
            i += 1
            continue
        if stripped == "<!-- countable-end -->":
            flush_paragraph()
            countable = False
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        heading = HEADING_RE.match(stripped)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)), 6)
            out.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            i += 1
            continue

        if MARKDOWN_IMAGE_RE.match(stripped) or WIKI_IMAGE_RE.match(stripped):
            flush_paragraph()
            out.append(render_image(stripped))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}:?", lines[i + 1]):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(render_table(table_lines))
            continue

        if ORDERED_RE.match(line):
            flush_paragraph()
            items = []
            while i < len(lines):
                match = ORDERED_RE.match(lines[i])
                if not match:
                    break
                items.append(match.group(1).strip())
                i += 1
            out.append("<ol>")
            for item in items:
                out.append(f"  <li>{render_inline(item)}</li>")
            out.append("</ol>")
            continue

        if is_html_block_line(line):
            flush_paragraph()
            html_lines = []
            while i < len(lines) and lines[i].strip():
                html_lines.append(lines[i])
                i += 1
            out.append("\n".join(html_lines))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            class_attr = f' class="countable" data-count-id="{attr(count_id)}"' if countable and count_id else ""
            quote = "<br />\n".join(render_inline(part) for part in quote_lines)
            out.append(f"<blockquote>\n  <p{class_attr}>{quote}</p>\n</blockquote>")
            continue

        paragraph.append(line)
        i += 1

    flush_paragraph()
    return "\n".join(out)


def indent_html(markup: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else "" for line in markup.splitlines())


def replace_region(source: str, name: str, markup: str) -> str:
    start = f"<!-- BEGIN:{name} -->"
    end = f"<!-- END:{name} -->"
    pattern = re.compile(
        rf"(?P<indent>^[ \t]*){re.escape(start)}.*?^[ \t]*{re.escape(end)}",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        raise ValueError(f"Missing build region: {name}")
    indent = match.group("indent")
    replacement = f"{indent}{start}\n{indent_html(markup, len(indent) + 2)}\n{indent}{end}"
    return pattern.sub(replacement, source, count=1)


def render_about_content() -> str:
    meta, body = parse_frontmatter(CONTENT_DIR / "about.md")
    return render_blocks(body, count_id=str(meta.get("count_id", "aboutCount")), countable_default=True)


def render_about_sidebar() -> str:
    meta, _ = parse_frontmatter(CONTENT_DIR / "about.md")
    return "\n".join(
        [
            '<img',
            '  class="profile-photo"',
            f'  src="{attr(meta.get("portrait_src", ""))}"',
            f'  alt="{attr(meta.get("portrait_alt", ""))}"',
            '  loading="lazy"',
            '  referrerpolicy="no-referrer"',
            '/>',
            f'<p class="profile-caption">{text(meta.get("portrait_caption", ""))}</p>',
            f'<h3>{text(meta.get("current_priorities_heading", "Current priorities"))}</h3>',
            f'<p>{render_inline(str(meta.get("current_priorities", "")))}</p>',
            f'<h3 style="margin-top: 1rem;">{text(meta.get("next_step_heading", "Next step"))}</h3>',
            f'<p>{render_inline(str(meta.get("next_step", "")))}</p>',
        ]
    )


def render_blog_content() -> str:
    meta, body = parse_frontmatter(CONTENT_DIR / "blog.md")
    count_id = str(meta.get("count_id", "blogCount"))
    parts = [f"<h3>{text(meta.get('title', 'Blog Post'))}</h3>"]
    author = meta.get("author")
    if author:
        parts.append(f'<p class="countable" data-count-id="{attr(count_id)}">{text(author)}</p>')
    parts.append(render_blocks(body, count_id=count_id, countable_default=True))
    return "\n".join(parts)


def render_blog_sidebar() -> str:
    meta, _ = parse_frontmatter(CONTENT_DIR / "blog.md")
    return "\n".join(
        [
            f'<span class="tag">{text(meta.get("download_tag", "Download"))}</span>',
            f'<h3>{text(meta.get("download_heading", "Downloadable Resource"))}</h3>',
            '<img',
            '  class="blog-download-thumb"',
            f'  src="{attr(meta.get("download_image", ""))}"',
            f'  alt="{attr(meta.get("download_alt", ""))}"',
            '  loading="lazy"',
            '/>',
            f'<p class="blog-download-copy">{render_inline(str(meta.get("download_copy", "")))}</p>',
            f'<a class="blog-download-link" href="{attr(meta.get("download_file", ""))}" download>',
            '  <i data-lucide="file-down"></i>',
            f'  {text(meta.get("download_label", "Download PDF"))}',
            '</a>',
        ]
    )


def load_resources() -> List[Tuple[Dict[str, object], str]]:
    resources = [parse_frontmatter(path) for path in sorted((CONTENT_DIR / "resources").glob("*.md"))]
    ordered = sorted(resources, key=lambda item: int(item[0].get("id", 0)))
    seen_slugs: Dict[str, str] = {}
    for meta, _ in ordered:
        slug = resource_slug(meta)
        if slug in seen_slugs:
            raise ValueError(f"Duplicate resource slug '{slug}' for {meta.get('title')} and {seen_slugs[slug]}")
        meta["slug"] = slug
        seen_slugs[slug] = str(meta.get("title", "Resource"))
    return ordered


def render_resource_card(meta: Dict[str, object]) -> str:
    classes = ["resource-card", "reveal"]
    card_class = str(meta.get("card_class", "")).strip()
    if card_class:
        classes.extend(card_class.split())
    if as_bool(meta.get("extra")):
        classes.append("extra")

    resource_id = attr(meta.get("id", ""))
    slug = attr(resource_slug(meta))
    detail_href = f"#resources/{slug}"
    label = text(meta.get("title", "Resource"))
    out = [f'<!-- Resource {resource_id}: {text(meta.get("title", "Resource"))} -->']
    out.append(
        f'<div class="{" ".join(classes)}" data-resource="{resource_id}" data-slug="{slug}" data-route="{attr(detail_href)}" tabindex="0" role="link" aria-label="Open {label} reflection page">'
    )
    out.append('  <div class="resource-card-summary">')
    out.append('    <div class="resource-head">')
    out.append(f'      <h3>{text(meta.get("title", "Resource"))}</h3>')
    out.append(f'      <i data-lucide="{attr(meta.get("icon", "file-text"))}"></i>')
    out.append('    </div>')
    out.append(f'    <p>{render_inline(str(meta.get("summary", "")))}</p>')

    if meta.get("image"):
        out.extend(
            [
                '    <img',
                '      class="resource-card-image"',
                f'      src="{attr(meta.get("image"))}"',
                f'      alt="{attr(meta.get("image_alt", ""))}"',
                '      loading="lazy"',
                '    />',
            ]
        )

    if meta.get("link_url"):
        href = str(meta.get("link_url"))
        label = str(meta.get("link_text", "Open resource →"))
        if as_bool(meta.get("link_download")):
            attrs = " download"
        elif href.startswith(("http://", "https://")):
            attrs = ' target="_blank" rel="noreferrer"'
        else:
            attrs = ""
        out.append(f'    <p><a href="{attr(href)}"{attrs}>{text(label)}</a></p>')

    out.append('  </div>')
    out.append('  <div class="resource-card-footer">')
    out.append('    <i data-lucide="arrow-right" style="width: 14px; height: 14px;"></i> Open Reflection Page')
    out.append('  </div>')
    out.append('</div>')
    return "\n".join(out)


def render_resource_cards() -> str:
    chunks: List[str] = []
    inserted_divider = False
    for meta, _ in load_resources():
        if as_bool(meta.get("extra")) and not inserted_divider:
            chunks.append(
                "\n".join(
                    [
                        '<div class="resources-divider" aria-label="Extra resources">',
                        '  <span>Extras</span>',
                        '</div>',
                    ]
                )
            )
            inserted_divider = True
        chunks.append(render_resource_card(meta))
    return "\n\n".join(chunks)


def render_reflection_attrs(meta: Dict[str, object]) -> str:
    media_images = resource_media_images(meta)
    pairs = {
        "id": f"reflection-{meta.get('id')}",
        "data-resource": meta.get("id"),
        "data-slug": resource_slug(meta),
        "data-title": meta.get("modal_title", meta.get("title", "Resource")),
        "data-card-title": meta.get("title", "Resource"),
        "data-summary": meta.get("summary", ""),
        "data-word-count-id": meta.get("count_id", f"ref{meta.get('id')}Count"),
        "data-media-images": "|".join(media_images),
    }
    optional_keys = [
        "media_link",
        "media_link_text",
        "media_download",
        "media_download_name",
        "media_downloads",
        "media_download_names",
    ]
    attr_names = {
        "media_image": "data-media-image",
        "media_link": "data-media-link",
        "media_link_text": "data-media-link-text",
        "media_download": "data-media-download",
        "media_download_name": "data-media-download-name",
        "media_downloads": "data-media-downloads",
        "media_download_names": "data-media-download-names",
    }
    for key in optional_keys:
        if meta.get(key):
            value = meta.get(key)
            if key in {"media_downloads", "media_download_names"}:
                value = "|".join(split_csv(str(value)))
            pairs[attr_names[key]] = value
    return " ".join(f'{name}="{attr(value)}"' for name, value in pairs.items())


def render_resource_reflection(meta: Dict[str, object], body: str) -> str:
    count_id = str(meta.get("count_id", f"ref{meta.get('id')}Count"))
    out = [f"<div {render_reflection_attrs(meta)}>"]
    out.append(f'  <span id="{attr(count_id)}" style="display: none;">0 words</span>')
    body_html = render_blocks(body, count_id=count_id, countable_default=as_bool(meta.get("countable"), True))
    out.append(indent_html(body_html, 2))
    out.append("</div>")
    return "\n".join(out)


def render_resource_reflections() -> str:
    return "\n\n".join(render_resource_reflection(meta, body) for meta, body in load_resources())


def render_references() -> str:
    body = (CONTENT_DIR / "references.md").read_text(encoding="utf-8")
    return render_blocks(body)


def build() -> None:
    source = INDEX_FILE.read_text(encoding="utf-8")
    regions = {
        "about-content": render_about_content(),
        "about-sidebar": render_about_sidebar(),
        "blog-content": render_blog_content(),
        "blog-sidebar": render_blog_sidebar(),
        "resource-cards": render_resource_cards(),
        "resource-reflections": render_resource_reflections(),
        "references-list": render_references(),
    }

    for name, markup in regions.items():
        source = replace_region(source, name, markup)

    word_count_labels = build_word_counts_label_map(source)
    source = apply_word_count_labels(source, word_count_labels)

    INDEX_FILE.write_text(source, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build()
    print(f"Built {INDEX_FILE.relative_to(ROOT)} from Markdown content.")
