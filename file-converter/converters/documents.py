"""Document format conversion.

Supported conversions:
    .docx -> .pdf   (uses MS Word via docx2pdf; Windows + Word required)
    .pdf  -> .docx  (pure python, via pdf2docx)
    .pdf  -> .txt   (text extraction, via pypdf)
    .docx -> .txt   (via python-docx)
    .txt  <-> .md   (plain copy/rename; content is compatible either way)
"""
from pathlib import Path

# input_ext -> list of possible output extensions
DOCUMENT_FORMATS = {
    ".docx": [".pdf", ".txt"],
    ".pdf": [".docx", ".txt"],
    ".txt": [".md"],
    ".md": [".txt"],
}

SUPPORTED_INPUT_EXTENSIONS = set(DOCUMENT_FORMATS.keys())


def convert_document(input_path: str, output_path: str, target_ext: str) -> str:
    src = Path(input_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    src_ext = src.suffix.lower()
    target_ext = target_ext.lower()

    if src_ext == ".docx" and target_ext == ".pdf":
        _docx_to_pdf(src, out)
    elif src_ext == ".pdf" and target_ext == ".docx":
        _pdf_to_docx(src, out)
    elif src_ext == ".pdf" and target_ext == ".txt":
        _pdf_to_txt(src, out)
    elif src_ext == ".docx" and target_ext == ".txt":
        _docx_to_txt(src, out)
    elif {src_ext, target_ext} == {".txt", ".md"}:
        out.write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported conversion: {src_ext} -> {target_ext}")

    return str(out)


def _docx_to_pdf(src: Path, out: Path) -> None:
    try:
        from docx2pdf import convert as _convert
    except ImportError as e:
        raise RuntimeError(
            "docx -> pdf requires Microsoft Word (Windows only)."
        ) from e
    _convert(str(src), str(out))


def _pdf_to_docx(src: Path, out: Path) -> None:
    from pdf2docx import Converter

    cv = Converter(str(src))
    try:
        cv.convert(str(out))
    finally:
        cv.close()


def _pdf_to_txt(src: Path, out: Path) -> None:
    from pypdf import PdfReader

    reader = PdfReader(str(src))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    out.write_text(text, encoding="utf-8")


def _docx_to_txt(src: Path, out: Path) -> None:
    import docx

    doc = docx.Document(str(src))
    text = "\n".join(p.text for p in doc.paragraphs)
    out.write_text(text, encoding="utf-8")
