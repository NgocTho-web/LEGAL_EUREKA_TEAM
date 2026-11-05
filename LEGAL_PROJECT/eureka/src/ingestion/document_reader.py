"""Eureka: read PDF/DOCX into unverified page-level JSON (Python 3.10+).

Dependencies: pymupdf, python-docx; OCR optional: pytesseract, Pillow.
Tesseract executable and Vietnamese traineddata are required for OCR.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any



def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_pdf(path: Path, *, ocr: bool, lang: str, dpi: int,
             tesseract_cmd: str | None, tessdata_dir: str | None) -> list[dict[str, Any]]:
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise RuntimeError('Install PyMuPDF: python -m pip install pymupdf') from exc

    pages: list[dict[str, Any]] = []
    if ocr:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError('OCR requires pytesseract and Pillow') from exc
        if tesseract_cmd:
            if not Path(tesseract_cmd).is_file():
                raise FileNotFoundError(f'Tesseract executable missing: {tesseract_cmd}')
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        if tessdata_dir:
            if not Path(tessdata_dir).is_dir():
                raise FileNotFoundError(f'Tessdata directory missing: {tessdata_dir}')
            os.environ['TESSDATA_PREFIX'] = tessdata_dir

    with fitz.open(path) as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted PDF requires a password')
        for index, page in enumerate(doc):
            text = page.get_text('text').strip()
            method = 'embedded_text'
            # OCR only when text layer is absent/nearly empty; preserve unverified status.
            if ocr and len(text) < 40:
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
                image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(image, lang=lang, config='--oem 1 --psm 6').strip()
                method = 'tesseract_ocr'
            pages.append({'page_number': index + 1, 'text': text,
                          'extraction_method': method, 'verification_status': 'unverified'})
    return pages


def read_docx(path: Path) -> list[dict[str, Any]]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError('Install python-docx: python -m pip install python-docx') from exc
    doc = Document(path)
    # DOCX has no stable physical page boundaries without a rendering engine.
    # Iterate body blocks in document order, including tables.
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    parts: list[str] = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn('w:p'):
            s = Paragraph(child, doc).text.strip()
            if s:
                parts.append(s)
        elif child.tag == qn('w:tbl'):
            table = Table(child, doc)
            for row in table.rows:
                parts.append(' | '.join(cell.text.strip().replace('\n', ' / ') for cell in row.cells))
    return [{'page_number': None, 'text': '\n'.join(parts),
             'extraction_method': 'docx_xml', 'verification_status': 'unverified'}]


def read_document(path: Path, *, ocr: bool = False, lang: str = 'vie', dpi: int = 250,
                  tesseract_cmd: str | None = None,
                  tessdata_dir: str | None = None) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if dpi < 72 or dpi > 400:
        raise ValueError('dpi must be between 72 and 400')
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        pages = read_pdf(path, ocr=ocr, lang=lang, dpi=dpi,
                         tesseract_cmd=tesseract_cmd, tessdata_dir=tessdata_dir)
    elif suffix == '.docx':
        pages = read_docx(path)
    elif suffix == '.doc':
        raise ValueError('Legacy .doc is not supported. Convert to .docx first.')
    else:
        raise ValueError(f'Unsupported extension: {suffix}')
    return {
        'schema_version': 1,
        'source_file': str(path),
        'file_name': path.name,
        'sha256': sha256_file(path),
        'read_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_verification': 'unverified',
        'legal_effect_verification': 'unverified',
        'pages': pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Read PDF/DOCX into unverified JSON')
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ocr', action='store_true', help='OCR pages with little/no embedded text')
    parser.add_argument('--lang', default='vie')
    parser.add_argument('--dpi', type=int, default=250)
    parser.add_argument('--tesseract', default=None)
    parser.add_argument('--tessdata', default=None)
    args = parser.parse_args()
    result = read_document(args.input, ocr=args.ocr, lang=args.lang, dpi=args.dpi,
                           tesseract_cmd=args.tesseract, tessdata_dir=args.tessdata)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Never silently overwrite existing staging artifacts.
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(result['pages'])} page/block records; SHA256={result['sha256']}")
    print(f'Output: {args.out}')
    print('Neo4j was not modified.')


if __name__ == '__main__':
    main()
