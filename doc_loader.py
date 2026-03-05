"""Load PDF documents and extract text with page boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import fitz  # PyMuPDF


@dataclass
class PageContent:
    """Text content for a single page."""

    page_num: int
    text: str


def load_pdf(path: Union[str, Path]) -> list[PageContent]:
    """
    Load a PDF file and extract text per page.

    Args:
        path: File path to the PDF (or path-like).

    Returns:
        List of PageContent with page_num (1-based) and text for each page.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid PDF.
    """
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
    """
    Load a PDF and return its full text concatenated, with optional page markers.

    Args:
        path: File path to the PDF.

    Returns:
        Full document text (pages joined with newlines).
    """
    pages = load_pdf(path)
    return "\n\n".join(p.text for p in pages)


def get_full_text_with_page_boundaries(
    path: Union[str, Path],
) -> tuple[str, list[tuple[int, int]]]:
    """
    Return full text and a list of (start_char, end_char) per page for chunking.

    Args:
        path: File path to the PDF.

    Returns:
        (full_text, [(start, end), ...]) where each tuple is the character range
        for that page (1-based page index implied by list position).
    """
    pages = load_pdf(path)
    parts: list[str] = []
    boundaries: list[tuple[int, int]] = []
    offset = 0
    for p in pages:
        start = offset
        text = p.text if p.text.endswith("\n") else p.text + "\n"
        parts.append(text)
        offset += len(text)
        boundaries.append((start, offset))
    full_text = "".join(parts)
    return full_text, boundaries
