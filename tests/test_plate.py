from app.utils.plate import clean_raw_text, format_plate_display, normalize_plate, validate_plate


def test_clean_raw_text_strips_and_uppercases():
    assert clean_raw_text(" 34 abc-123 ") == "34ABC123"


def test_clean_raw_text_maps_turkish_chars():
    assert clean_raw_text("34şİ123") == "34SI123"


def test_validate_plate_accepts_known_formats():
    assert validate_plate("34ABC123")
    assert validate_plate("06AB1234")
    assert validate_plate("01A1234")
    assert validate_plate("35ABC12")


def test_validate_plate_rejects_bad_province_or_letters():
    assert not validate_plate("00ABC123")  # il kodu 00 geçersiz
    assert not validate_plate("82ABC123")  # il kodu 82 geçersiz (max 81)
    assert not validate_plate("34QBC123")  # Q Türk plakalarında kullanılmaz


def test_normalize_plate_handles_exact_match():
    assert normalize_plate("34 ABC 123") == "34ABC123"


def test_normalize_plate_corrects_ocr_digit_letter_confusion():
    # OCR 'O' yerine '0' okuduğunda ilk iki hanenin rakama düzeltilmesi
    assert normalize_plate("O6 AB 1234") == "06AB1234"


def test_normalize_plate_rejects_garbage():
    assert normalize_plate("HELLO WORLD") is None
    assert normalize_plate("12") is None
    assert normalize_plate("") is None


def test_format_plate_display():
    assert format_plate_display("34ABC123") == "34 ABC 123"
