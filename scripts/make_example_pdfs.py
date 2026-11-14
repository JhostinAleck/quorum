"""Builds the example PDFs from quorum/ui/examples/oferta-*.md. Standard library plus pdftoppm.

  pdf/oferta-1.pdf             PDF with a text layer
  pdf/oferta-2-escaneada.pdf   image only, like a scan: it needs OCR
  pdf/oferta-3.pdf             PDF with a text layer

Run it where pdftoppm exists, for example in the interface image:
  docker run --rm -u root -v "$PWD:/work" -w /work --entrypoint python quorum:ui scripts/make_example_pdfs.py
"""
from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "quorum" / "ui" / "examples"
OUT = EXAMPLES / "pdf"


def _pdf(objects: list[bytes]) -> bytes:
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)


def text_pdf(text: str) -> bytes:
    def escape(line: str) -> bytes:
        return line.encode("cp1252", "replace").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    lines = b"".join(b"(" + escape(line) + b") Tj T*\n" for line in text.splitlines())
    stream = b"BT /F1 13 Tf 72 760 Td 20 TL\n" + lines + b"ET"
    return _pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ])


def _jpeg_size(data: bytes) -> tuple[int, int, int]:
    i = 2
    while i < len(data):
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xC3:
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height, data[i + 9]   # components: 1 grey, 3 colour
        i += 2 + length
    raise ValueError("not a JPEG")


def scanned_pdf(text: str) -> bytes:
    """The same page, rendered to a grey JPEG and wrapped in a PDF with no text layer."""
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "page.pdf"
        source.write_bytes(text_pdf(text))
        subprocess.run(["pdftoppm", "-r", "150", "-gray", "-jpeg", "-singlefile", str(source),
                        str(Path(folder) / "scan")], check=True)
        jpeg = (Path(folder) / "scan.jpg").read_bytes()
    width, height, components = _jpeg_size(jpeg)
    colour = b"/DeviceGray" if components == 1 else b"/DeviceRGB"
    stream = b"q 595 0 0 842 0 0 cm /Im1 Do Q"
    return _pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /XObject << /Im1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace %s "
        b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n" % (width, height, colour, len(jpeg))
        + jpeg + b"\nendstream",
    ])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(EXAMPLES.glob("oferta-*.md")):
        text = path.read_text(encoding="utf-8")
        if path.stem == "oferta-2":
            (OUT / "oferta-2-escaneada.pdf").write_bytes(scanned_pdf(text))
        else:
            (OUT / f"{path.stem}.pdf").write_bytes(text_pdf(text))
    print("written:", ", ".join(p.name for p in sorted(OUT.glob("*.pdf"))))


if __name__ == "__main__":
    main()
