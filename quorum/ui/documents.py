"""Text extraction from uploaded bids: plain text, PDF and scanned documents.

No Python dependencies. PDF and OCR use command-line tools that the interface
image installs (Dockerfile, WITH_OCR=1):

  pdftotext, pdftoppm   (poppler-utils)      text layer / page rendering
  tesseract             (tesseract-ocr-spa)  OCR of scans and photos

A PDF with a text layer is read directly. If it has none (a scan), its first
pages are rendered and passed through OCR. Images go straight to OCR.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path

MAX_BYTES = 8_000_000
MAX_PAGES = 3
TIMEOUT = 60
TEXT, PDF, OCR = "text", "pdf", "ocr"
_IMAGES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
_MIN_TEXT = 20   # fewer characters than this in a PDF means there is no text layer
_CACHE_SIZE = 64  # extractions kept by content hash: the same file uploaded again is instant
_cache: OrderedDict[str, tuple[str, str]] = OrderedDict()
_cache_lock = threading.Lock()
# Pages are read in parallel, one tesseract per page. Each one is limited to a
# single thread: otherwise every process starts one thread per core and they
# compete with each other, which is slower than reading page after page.
_OCR_ENV = {**os.environ, "OMP_THREAD_LIMIT": "1"}


class ExtractionError(ValueError):
    pass


def available() -> dict[str, bool]:
    """Which formats this machine can read."""
    pdf = bool(shutil.which("pdftotext"))
    ocr = bool(shutil.which("tesseract"))
    return {"pdf": pdf, "scanned_pdf": ocr and bool(shutil.which("pdftoppm")), "image": ocr}


def _run(*command: str, env: dict[str, str] | None = None) -> str:
    try:
        done = subprocess.run(command, capture_output=True, timeout=TIMEOUT, check=False, env=env)
    except FileNotFoundError:
        raise ExtractionError(f"falta la herramienta {command[0]!r}; el lector de PDF y OCR viene en la "
                              "imagen Docker de la interfaz") from None
    except subprocess.TimeoutExpired:
        raise ExtractionError("el documento tardó demasiado en procesarse") from None
    if done.returncode != 0:
        raise ExtractionError(f"{command[0]} no pudo leer el documento")
    return done.stdout.decode("utf-8", errors="replace")


@cache
def _languages() -> str:
    """Asked once per process, not once per page."""
    return "spa+eng" if "spa" in _run("tesseract", "--list-langs") else "eng"


def _ocr(image: Path) -> str:
    return _run("tesseract", str(image), "stdout", "-l", _languages(), "--psm", "6", env=_OCR_ENV)


def _ocr_pages(pages: list[Path]) -> str:
    if len(pages) == 1:
        return _ocr(pages[0])
    with ThreadPoolExecutor(max_workers=min(len(pages), os.cpu_count() or 1)) as pool:
        return "\n".join(pool.map(_ocr, pages))   # map keeps the page order


def extract(filename: str, data: bytes) -> tuple[str, str]:
    """Returns (text, method) where method is 'text', 'pdf' or 'ocr'."""
    if len(data) > MAX_BYTES:
        raise ExtractionError("el documento supera el tamaño máximo")
    key = hashlib.sha256(Path(filename).suffix.lower().encode() + b"\0" + data).hexdigest()
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    result = _extract(filename, data)
    with _cache_lock:
        _cache[key] = result
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return result


def _extract(filename: str, data: bytes) -> tuple[str, str]:
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
        # PGM, not PNG: the image is only read once by tesseract, and compressing
        # it took longer than the OCR itself
        _run("pdftoppm", "-r", "200", "-gray", "-l", str(MAX_PAGES), str(source), str(Path(folder) / "page"))
        pages = sorted(Path(folder).glob("page*.pgm"))
        if not pages:
            raise ExtractionError("el PDF no tiene páginas legibles")
        return _ocr_pages(pages), OCR
