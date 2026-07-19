from app.knowledge.markdown_extractor import MarkdownExtractor


async def _extract(md: str) -> str:
    return await MarkdownExtractor().extract(md.encode("utf-8"))


async def test_headings_become_plain_text() -> None:
    assert await _extract("# Title\n\n## Subtitle") == "Title\nSubtitle"


async def test_emphasis_and_strong_keep_only_text() -> None:
    assert await _extract("This is **bold** and *italic*.") == "This is bold and italic."


async def test_links_keep_only_visible_text() -> None:
    assert await _extract("See [OpenAI](https://openai.com) docs.") == "See OpenAI docs."


async def test_inline_code_kept_as_text() -> None:
    assert await _extract("Run `pytest` now.") == "Run pytest now."


async def test_code_fence_content_preserved_without_markers() -> None:
    md = "```python\nprint(1)\n```"
    assert await _extract(md) == "print(1)"


async def test_list_items_each_on_own_line() -> None:
    assert await _extract("- one\n- two\n- three") == "one\ntwo\nthree"


async def test_blockquote_becomes_text() -> None:
    assert await _extract("> quoted line") == "quoted line"


async def test_images_are_ignored() -> None:
    assert await _extract("![alt text](img.png)") == ""


async def test_html_blocks_are_ignored() -> None:
    assert await _extract("<div>raw</div>\n\nreal text") == "real text"


async def test_empty_and_whitespace_markdown_returns_empty() -> None:
    assert await _extract("") == ""
    assert await _extract("   \n\n\t") == ""


async def test_combined_document() -> None:
    md = (
        "# Guide\n\n"
        "Use **LifeOS** with [docs](https://x).\n\n"
        "- first\n- second\n\n"
        "```json\n{}\n```\n"
    )
    assert await _extract(md) == "Guide\nUse LifeOS with docs.\nfirst\nsecond\n{}"
