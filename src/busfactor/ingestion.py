"""Ingestion — read project files as numbered pages of plain text (Teammate 1).

Only text is extracted. Uploaded content is never executed, imported or evaluated.

Page numbering (this is what DecisionCard.source_refs[].page refers to):
- PDF:      the real PDF page number (1-based), via pdfplumber.
- .md/.txt: pages are separated by lines containing only `---`, numbered from 1.
            A file with no `---` lines is cut into ~3000-character chunks instead.
Empty pages are left out but keep their number, so citations never shift.
"""
from __future__ import annotations

import re
from pathlib import Path

CHUNK_CHARS = 3000
TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
_PAGE_BREAK = re.compile(r"^[ \t]*---[ \t]*$", flags=re.MULTILINE)


def load_pages(path: str | Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] for a PDF, Markdown or text file.

    An empty file gives []. A missing file raises FileNotFoundError;
    an unsupported file type raises ValueError.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix in TEXT_SUFFIXES:
        return _load_text(path.read_text(encoding="utf-8", errors="replace"))
    raise ValueError(f"Unsupported file type '{suffix}'. Use .pdf, .md or .txt.")


def _load_pdf(path: Path) -> list[tuple[int, str]]:
    # Imported here so Markdown/text ingestion works even without pdfplumber installed.
    import pdfplumber

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = _page_text(page).strip()
            if text:  # scanned/blank pages have no text layer -> skipped, number kept
                pages.append((number, text))
    return pages


_LINE_TOLERANCE = 3.0     # words whose tops differ by less than this are on one line (points)
_GUTTER = 6.0             # a gap at least this wide in the middle of a line is the space between two columns


def _page_text(page) -> str:
    """Text of one PDF page in reading order.

    Two-column papers (IEEE, ACM) are read left column first, then right column; a plain `extract_text`
    runs across both columns line by line, which scrambles sentences so that no quote can be found.
    Full-width lines (title, wide figures) stay where they are.
    """
    words = page.extract_words(x_tolerance=1.5, y_tolerance=_LINE_TOLERANCE, keep_blank_chars=False)
    if not words:
        return ""
    middle = float(page.width) / 2
    rows: list[list[dict]] = []
    for word in sorted(words, key=lambda w: (round(float(w["top"])), float(w["x0"]))):
        if rows and abs(float(word["top"]) - float(rows[-1][0]["top"])) <= _LINE_TOLERANCE:
            rows[-1].append(word)
        else:
            rows.append([word])
    # without a clear gutter in at least a few lines, this is a one-column page: keep the normal order
    split_rows = sum(1 for row in rows if _split_row(row, middle) is not None)
    if split_rows < 5:
        return "\n".join(" ".join(w["text"] for w in sorted(row, key=lambda w: float(w["x0"]))) for row in rows)
    out: list[str] = []
    left: list[str] = []
    right: list[str] = []

    def flush() -> None:
        out.extend(left)
        out.extend(right)
        left.clear()
        right.clear()

    for row in rows:
        parts = _split_row(row, middle)
        if parts is None:            # a line that crosses the middle: it is full width
            flush()
            out.append(" ".join(w["text"] for w in sorted(row, key=lambda w: float(w["x0"]))))
            continue
        if parts[0]:
            left.append(" ".join(w["text"] for w in parts[0]))
        if parts[1]:
            right.append(" ".join(w["text"] for w in parts[1]))
    flush()
    return "\n".join(out)


def _split_row(row: list[dict], middle: float):
    """(left words, right words) when the line has a gutter around the middle of the page, else None."""
    ordered = sorted(row, key=lambda w: float(w["x0"]))
    left = [w for w in ordered if (float(w["x0"]) + float(w["x1"])) / 2 < middle]
    right = [w for w in ordered if (float(w["x0"]) + float(w["x1"])) / 2 >= middle]
    if any(float(w["x0"]) < middle - 1 and float(w["x1"]) > middle + 1 for w in ordered):
        return None                  # a word crosses the middle
    if left and right and float(right[0]["x0"]) - float(left[-1]["x1"]) < _GUTTER:
        return None                  # the two sides touch: one wide line
    return left, right


def _load_text(text: str) -> list[tuple[int, str]]:
    if _PAGE_BREAK.search(text):
        parts = _PAGE_BREAK.split(text)
    else:
        parts = _chunk(text, CHUNK_CHARS)
    return [(number, part.strip()) for number, part in enumerate(parts, start=1) if part.strip()]


def _chunk(text: str, size: int) -> list[str]:
    """Split text into pieces of at most ~size characters, preferring paragraph or line breaks."""
    chunks: list[str] = []
    while len(text) > size:
        cut = max(text.rfind("\n\n", 0, size), text.rfind("\n", 0, size))
        if cut <= 0:
            cut = text.rfind(" ", 0, size)
        if cut <= 0:  # one very long word: hard cut
            cut = size
        chunks.append(text[:cut])
        text = text[cut:]
    chunks.append(text)
    return chunks
