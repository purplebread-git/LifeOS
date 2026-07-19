"""In-memory PDF builder for tests.

Собираем минимальный валидный PDF с текстовым слоем прямо в памяти — без
бинарных фикстур на диске, без reportlab и без зависимости от файловой системы.
Тесты остаются детерминированными и быстрыми. Каждая страница из `pages`
получает один текстовый объект; страницы без текста не добавляем здесь намеренно
(сценарий скана проверяется отдельно pdf-ом вообще без текстового слоя).
"""

from __future__ import annotations


def make_text_pdf(pages: list[str]) -> bytes:
    objects: list[bytes] = []

    # 1: Catalog, 2: Pages, 3: shared Font; страницы и их контент — далее.
    page_count = len(pages)
    first_page_obj = 4
    kids = " ".join(f"{first_page_obj + i * 2} 0 R" for i in range(page_count))

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(
        b"<< /Type /Pages /Kids ["
        + kids.encode("latin-1")
        + b"] /Count "
        + str(page_count).encode("latin-1")
        + b" >>"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for i, text in enumerate(pages):
        content_obj = first_page_obj + i * 2 + 1
        page_dict = (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents "
            + str(content_obj).encode("latin-1")
            + b" 0 R /Resources << /Font << /F1 3 0 R >> >> >>"
        )
        stream = f"BT /F1 24 Tf 50 200 Td ({text}) Tj ET".encode("latin-1")
        content = (
            b"<< /Length "
            + str(len(stream)).encode("latin-1")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        objects.append(page_dict)
        objects.append(content)

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(idx).encode("latin-1") + b" 0 obj\n" + obj + b"\nendobj\n"

    xref_pos = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode("latin-1") + b"\n"
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("latin-1")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode("latin-1")
        + b"\n%%EOF"
    )
    return bytes(out)


def make_textless_pdf() -> bytes:
    """PDF из одной страницы без текстового слоя (имитация скана)."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(idx).encode("latin-1") + b" 0 obj\n" + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 " + str(len(objects) + 1).encode("latin-1") + b"\n"
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += (
        b"trailer\n<< /Size "
        + str(len(objects) + 1).encode("latin-1")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_pos).encode("latin-1")
        + b"\n%%EOF"
    )
    return bytes(out)
