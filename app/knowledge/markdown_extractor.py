"""MarkdownExtractor — извлечение читаемого текста из Markdown (CommonMark).

Парсинг Markdown делегирован markdown-it-py (зрелый CommonMark-парсер). А вот
ПОЛИТИКА извлечения текста — доменная логика LifeOS и живёт здесь, а не во
внешней библиотеке: markdown → tokens → (наш обход) → plain text. Промежуточного
HTML нет.

Политика извлечения (намеренное поведение; правьте осознанно):
  * заголовки → обычный текст (без `#`);
  * абзацы → текст;
  * strong / emphasis / strikethrough → только внутренний текст (маркеры сняты);
  * ссылки → только видимый текст (URL отбрасывается);
  * inline code → текст кода;
  * fenced / indented code → содержимое как текст (сам fence и язык отброшены);
  * списки → каждый элемент отдельной строкой (без маркеров);
  * blockquote → текст;
  * softbreak → пробел, hardbreak → перевод строки;
  * изображения → игнорируются (alt не извлекается);
  * HTML-блоки и inline-HTML → игнорируются.

Блоки соединяются переводом строки; ведущие/замыкающие пробелы обрезаются.
Пустой/пробельный результат отдаётся как есть (пустоту отфильтрует ingestion).

На будущее (пока НЕ реализовано, требует осознанного решения): сохранять язык
code fence, форматировать ссылку как "text (url)", включать/исключать содержимое
code fence, специально обрабатывать GFM-таблицы (сейчас парсер — commonmark).
"""

from __future__ import annotations

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.core.document_extractor import DocumentExtractor

_INLINE_MARKUP_TOKENS = frozenset(
    {
        "strong_open",
        "strong_close",
        "em_open",
        "em_close",
        "s_open",
        "s_close",
        "link_open",
        "link_close",
    }
)


class MarkdownExtractor(DocumentExtractor):
    def __init__(self) -> None:
        self._md = MarkdownIt("commonmark")

    async def extract(self, content: bytes) -> str:
        tokens = self._md.parse(content.decode("utf-8"))
        blocks = [block for block in self._render_blocks(tokens) if block]
        return "\n".join(blocks).strip()

    def _render_blocks(self, tokens: list[Token]) -> list[str]:
        blocks: list[str] = []
        for token in tokens:
            if token.type == "inline":
                blocks.append(self._render_inline(token.children or []))
            elif token.type in ("fence", "code_block"):
                blocks.append(token.content.rstrip("\n"))
        return blocks

    def _render_inline(self, children: list[Token]) -> str:
        parts: list[str] = []
        for token in children:
            if token.type in ("text", "code_inline"):
                parts.append(token.content)
            elif token.type == "softbreak":
                parts.append(" ")
            elif token.type == "hardbreak":
                parts.append("\n")
            elif token.type in _INLINE_MARKUP_TOKENS:
                continue
            # image / html_inline и прочее — игнорируются
        return "".join(parts)
