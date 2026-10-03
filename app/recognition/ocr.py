"""Tespit edilen plaka bölgesinin OCR ile okunması (Tesseract OCR, Apache 2.0).

Tesseract, sistemde kurulu `tesseract` ikili dosyası üzerinden pytesseract
sarmalayıcısıyla çağrılır. Kurulu değilse anlaşılır bir hata fırlatılır;
rastgele/sahte metin üretilmez.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_WHITELIST = "ABCDEFGHIJKLMNOPRSTUVYZ0123456789"
_TESSERACT_CONFIG = f'--psm 7 --oem 3 -c tessedit_char_whitelist={_WHITELIST}'


class TesseractNotAvailableError(RuntimeError):
    pass


class PlateOCR:
    def __init__(self, lang: str = "eng") -> None:
        self._lang = lang
        self._verified = False

    def _verify_available(self) -> None:
        if self._verified:
            return
        import pytesseract

        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:
            raise TesseractNotAvailableError(
                "Tesseract OCR motoru bulunamadı. Windows'ta Tesseract-OCR "
                "kurulumunun PATH'e eklendiğinden emin olun "
                "(bkz. README.md kurulum adımları)."
            ) from exc
        self._verified = True

    @staticmethod
    def _preprocess(plate_crop_bgr):
        import cv2

        gray = cv2.cvtColor(plate_crop_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        _thresh_val, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary

    def read(self, plate_crop_bgr) -> tuple[str, float]:
        """Plaka kırpımından (raw_text, confidence[0..1]) döndürür.
        Hiçbir karakter okunamazsa ("", 0.0) döner."""
        self._verify_available()
        import pytesseract

        if plate_crop_bgr is None or plate_crop_bgr.size == 0:
            return "", 0.0

        processed = self._preprocess(plate_crop_bgr)
        data = pytesseract.image_to_data(
            processed,
            lang=self._lang,
            config=_TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT,
        )

        texts: list[str] = []
        confidences: list[float] = []
        for text, conf in zip(data.get("text", []), data.get("conf", [])):
            text = text.strip()
            if not text:
                continue
            try:
                conf_f = float(conf)
            except (TypeError, ValueError):
                continue
            if conf_f < 0:
                continue
            texts.append(text)
            confidences.append(conf_f)

        if not texts:
            return "", 0.0

        combined_text = "".join(texts)
        avg_confidence = (sum(confidences) / len(confidences)) / 100.0
        return combined_text, max(0.0, min(1.0, avg_confidence))
