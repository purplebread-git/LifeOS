"""PdfExtractor — извлечение встроенного текста из PDF.

Первый бинарный формат: тот же контракт bytes → text, что и у текстовых
extractor'ов, но на вход приходит бинарный документ. Парсинг делегирован pypdf
(BSD-3, pure Python, де-факто стандарт для извлечения текста из PDF).

Политика извлечения (намеренно узкая; правьте осознанно):
  * извлекается ТОЛЬКО встроенный текстовый слой;
  * OCR отсутствует — страницы-сканы (без текстового слоя) не дают вклад;
  * документ без текстового слоя целиком → "" (ingestion ничего не сохранит);
  * страницы соединяются переводом строки (chunker далее нормализует пробелы);
  * ошибки чтения PDF (битый/зашифрованный документ) НЕ подавляются — пусть
    инфраструктурная ошибка pypdf всплывает к вызывающему. Собственная иерархия
    ошибок (ExtractorError) не вводится ради одного формата — появится, только
    когда станет реально общей как минимум для трёх extractor'ов.
"""

from __future__ import annotations

import io

from pypdf import PdfReader

from app.core.document_extractor import DocumentExtractor


class PdfExtractor(DocumentExtractor):
    async def extract(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() for page in reader.pages]
        return "\n".join(page for page in pages if page).strip()
