"""Türk plaka biçimi doğrulama ve OCR çıktısı normalizasyonu.

Bu modül kasıtlı olarak diğer katmanlardan (kamera, OCR motoru, UI)
bağımsızdır; böylece hem birim testlerde hem de farklı OCR motorlarıyla
tekrar kullanılabilir.
"""

from __future__ import annotations

import re

from app.config.constants import OCR_CHAR_CORRECTIONS, TURKISH_PLATE_REGEXES

_TURKISH_CHAR_MAP = {
    "İ": "I", "I": "I", "ı": "I", "Ş": "S", "ş": "S", "Ğ": "G", "ğ": "G",
    "Ü": "U", "ü": "U", "Ö": "O", "ö": "O", "Ç": "C", "ç": "C",
}
_LETTER_TO_DIGIT = dict(OCR_CHAR_CORRECTIONS)
_DIGIT_TO_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B"}
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]")


def clean_raw_text(text: str) -> str:
    """Büyük harfe çevirir, Türkçe karakterleri ASCII karşılıklarına
    eşler ve harf/rakam dışındaki her şeyi (boşluk, tire, nokta) atar."""
    text = text.upper()
    for src, dst in _TURKISH_CHAR_MAP.items():
        text = text.replace(src.upper(), dst)
    return _NON_ALNUM_RE.sub("", text)


def _correct_run(s: str, expect: str) -> str:
    table = _LETTER_TO_DIGIT if expect == "digit" else _DIGIT_TO_LETTER
    is_right_type = str.isdigit if expect == "digit" else str.isalpha
    return "".join(ch if is_right_type(ch) else table.get(ch, ch) for ch in s)


def validate_plate(plate_normalized: str) -> bool:
    """Boşluksuz, büyük harf bir dizginin geçerli bir TR plaka biçimine
    uyup uymadığını kontrol eder."""
    return any(re.match(p, plate_normalized) for p in TURKISH_PLATE_REGEXES)


def _count_corrections(original: str, fixed: str) -> int:
    return sum(1 for a, b in zip(original, fixed) if a != b)


def normalize_plate(raw_text: str) -> str | None:
    """OCR çıktısını temizler, olası karakter karışıklıklarını (O/0, I/1, ...)
    konuma göre düzeltmeye çalışır ve geçerliyse normalize edilmiş plakayı
    ('34ABC123' biçiminde, boşluksuz) döndürür. Geçersizse None döner.

    Harf/rakam blok uzunluğu belirsiz olduğundan (örn. 'AB1234' hem
    2 harf+4 rakam hem de -yanlış biçimde- 3 harf+3 rakam gibi
    yorumlanabilir), en AZ karakter düzeltmesi gerektiren -yani OCR
    çıktısına en sadık kalan- geçerli yorum seçilir.
    """
    cleaned = clean_raw_text(raw_text)
    if not (7 <= len(cleaned) <= 8):
        return None

    province_raw = cleaned[:2]
    rest = cleaned[2:]
    province = _correct_run(province_raw, expect="digit")
    if not province.isdigit():
        return None
    province_corrections = _count_corrections(province_raw, province)

    best_candidate: str | None = None
    best_corrections = None
    # 2 harfli biçim istatistiksel olarak en yaygın olduğundan eşit
    # düzeltme sayısında öncelik tanınır.
    for letter_len in (2, 3, 1):
        if letter_len >= len(rest):
            continue
        letters_raw = rest[:letter_len]
        digits_raw = rest[letter_len:]
        letters = _correct_run(letters_raw, expect="letter")
        digits = _correct_run(digits_raw, expect="digit")
        if not (letters.isalpha() and digits.isdigit()):
            continue
        candidate = f"{province}{letters}{digits}"
        if not validate_plate(candidate):
            continue
        corrections = (
            province_corrections
            + _count_corrections(letters_raw, letters)
            + _count_corrections(digits_raw, digits)
        )
        if best_corrections is None or corrections < best_corrections:
            best_candidate = candidate
            best_corrections = corrections

    return best_candidate


def format_plate_display(plate_normalized: str) -> str:
    """'34ABC123' -> '34 ABC 123' biçiminde okunabilir gösterim üretir."""
    match = re.match(r"^(\d{2})([A-Z]+)(\d+)$", plate_normalized)
    if not match:
        return plate_normalized
    return " ".join(match.groups())
