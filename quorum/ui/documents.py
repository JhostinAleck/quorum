"""Text extraction from uploaded bids: plain text, PDF and scanned documents.

No Python dependencies. PDF and OCR use command-line tools that the interface
image installs (Dockerfile, WITH_OCR=1):

  pdftotext, pdftoppm   (poppler-utils)      text layer / page rendering
  tesseract             (tesseract-ocr-spa)  OCR of scans and photos

A PDF with a text layer is read directly. If it has none (a scan), its first
pages are rendered and passed through OCR. Images go straight to OCR.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

MAX_BYTES = 8_000_000
MAX_PAGES = 3
TIMEOUT = 60
TEXT, PDF, OCR = "text", "pdf", "ocr"
_IMAGES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
_MIN_TEXT = 20   # fewer characters than this in a PDF means there is no text layer


class ExtractionError(ValueError):
    pass


def available() -> dict[str, bool]:
    """Which formats this machine can read."""
    pdf = bool(shutil.which("pdftotext"))
    ocr = bool(shutil.which("tesseract"))
    return {"pdf": pdf, "scanned_pdf": ocr and bool(shutil.which("pdftoppm")), "image": ocr}


def _run(*command: str) -> str:
    try:
        done = subprocess.run(command, capture_output=True, timeout=TIMEOUT, check=False)
    except FileNotFoundError:
        raise ExtractionError(f"falta la herramienta {command[0]!r}; el lector de PDF y OCR viene en la "
                              "imagen Docker de la interfaz") from None
    except subprocess.TimeoutExpired:
        raise ExtractionError("el documento tardó demasiado en procesarse") from None
    if done.returncode != 0:
        raise ExtractionError(f"{command[0]} no pudo leer el documento")
    return done.stdout.decode("utf-8", errors="replace")


def _ocr(image: Path) -> str:
    languages = "spa+eng" if "spa" in _run("tesseract", "--list-langs") else "eng"
    return _run("tesseract", str(image), "stdout", "-l", languages, "--psm", "6")


def extract(filename: str, data: bytes) -> tuple[str, str]:
    """Returns (text, method) where method is 'text', 'pdf' or 'ocr'."""
    if len(data) > MAX_BYTES:
        raise ExtractionError("el documento supera el tamaño máximo")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", *_IMAGES}:
        if b"\x00" in data[:2000]:
            raise ExtractionError("formato no soportado: usa .txt, .md, .pdf o una imagen")
        return data.decode("utf-8", errors="replace"), TEXT

    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / f"document{suffix}"   # never the uploaded name
        source.write_bytes(data)
        if suffix in _IMAGES:
            return _ocr(source), OCR
        text = _run("pdftotext", "-l", str(MAX_PAGES), "-layout", str(source), "-")
        if len("".join(text.split())) >= _MIN_TEXT:
            return text, PDF
        _run("pdftoppm", "-r", "200", "-gray", "-png", "-l", str(MAX_PAGES), str(source), str(Path(folder) / "page"))
        pages = sorted(Path(folder).glob("page*.png"))
        if not pages:
            raise ExtractionError("el PDF no tiene páginas legibles")
        return "\n".join(_ocr(page) for page in pages), OCR
