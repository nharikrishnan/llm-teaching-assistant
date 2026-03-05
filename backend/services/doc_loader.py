"""Load PDF documents and extract text with page boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import fitz  # PyMuPDF


@dataclass
class PageContent:
    page_num: int
    text: str


def load_pdf(path: Union[str, Path]) -> list[PageContent]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(path)
    try:
        pages: list[PageContent] = []
        for i in range(len(doc)):
            page = doc.load_page(i)
            text = page.get_text()
            pages.append(PageContent(page_num=i + 1, text=text))
        return pages
    finally:
        doc.close()


def load_pdf_as_text(path: Union[str, Path]) -> str:
    pages = load_pdf(path)
    return "\n\n".join(p.text for p in pages)
