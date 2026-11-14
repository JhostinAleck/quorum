"""Every other place an uploaded bid writes its own sealed amount.

parse_bid seals the value of the 'Valor:' line, and the rest of the document
becomes the annex: third-party text that every agent reads as public context.
Real bids repeat the amount (a summary box, the cover letter, the amount in
words). Left in the annex, those copies would reach the portal without the
label of the sealed value, and the gate could not see them. So they are taken
out here, before the annex is stored.

Matched loosely on purpose, because the text may come from OCR:
  figures  the digits of the value in order, with any separators or a
           stray space between them ("468.915.720", "468 915 720", "468915720,00")
  words    the amount written in Spanish, with or without accents, any case,
           and any line breaks between the words
"""
from __future__ import annotations

import re
import unicodedata

SEALED = "[sellado]"

_UNITS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
          "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve",
          "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis",
          "veintisiete", "veintiocho", "veintinueve"]
_TENS = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
_HUNDREDS = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos",
             "setecientos", "ochocientos", "novecientos"]
_SEP = r"[\s.,'’]{0,2}"     # between two digits of the amount


def _below_thousand(n: int, *, apocope: bool) -> list[str]:
    """Words for 0..999. `apocope`: "un" and not "uno" before mil / millones."""
    if n == 100:
        return ["cien"]
    words = [_HUNDREDS[n // 100]] if n >= 100 else []
    rest = n % 100
    if rest < 30:
        unit = _UNITS[rest]
        if apocope and unit.endswith("uno"):
            unit = unit[:-1] if unit == "uno" else unit[:-3] + "ún"
        words += [unit] if unit else []
    else:
        words.append(_TENS[rest // 10])
        if rest % 10:
            unit = _UNITS[rest % 10]
            words += ["y", "un" if apocope and unit == "uno" else unit]
    return words


def _below_million(n: int, *, apocope: bool) -> list[str]:
    thousands, rest = n // 1000, n % 1000
    words = [] if not thousands else ["mil"] if thousands == 1 else [*_below_thousand(thousands, apocope=True), "mil"]
    return words + (_below_thousand(rest, apocope=apocope) if rest else [])


def in_words(n: int) -> list[str]:
    """The amount in Spanish words, as a bid writes it: 468915720 -> cuatrocientos sesenta y ocho millones ...
    Up to 999 999 999 999 (the long scale: "mil millones", not "billón")."""
    if n == 0:
        return ["cero"]
    millions, rest = n // 1_000_000, n % 1_000_000
    words = [] if not millions else ["un", "millón"] if millions == 1 \
        else [*_below_million(millions, apocope=True), "millones"]
    return words + (_below_million(rest, apocope=False) if rest else [])


def _fold(text: str) -> str:
    """Lower case without accents, one character per character (so positions match the original)."""
    return "".join(unicodedata.normalize("NFD", ch)[0].lower() for ch in text)


def _figures(value: int) -> re.Pattern[str]:
    digits = str(value)
    return re.compile(r"(?<![\d.,])" + _SEP.join(digits) + r"(?:[.,]\d{1,2})?(?!\d)")


def _words(value: int) -> re.Pattern[str]:
    folded = [_fold(w) for w in in_words(value)]
    return re.compile(r"\b" + r"\s+".join(map(re.escape, folded)) + r"\b")


def redact(text: str, value: int) -> str:
    """The text with every copy of `value`, in figures or in words, replaced by SEALED."""
    text = _figures(value).sub(SEALED, text)
    if value < 1000:          # too short in words to be told apart from ordinary prose
        return text
    folded, out, last = _fold(text), [], 0
    for match in _words(value).finditer(folded):
        out += [text[last:match.start()], SEALED]
        last = match.end()
    return "".join(out) + text[last:]
