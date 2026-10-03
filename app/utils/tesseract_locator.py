"""Tesseract OCR ikilisini bulur.

Öncelik sırası:
  1. Uygulamanın yanında paketlenmiş `vendor/tesseract/tesseract.exe`
     (EXE'yi tam bağımsız/self-contained dağıtmak isteyenler için;
     build.bat bu klasörü doldurma talimatını içerir).
  2. Sistem PATH'inde kurulu `tesseract` (standart Windows kurulumu,
     bkz. README.md).

Hiçbiri bulunamazsa, OCR çağrıldığında PlateOCR zaten anlaşılır bir
hata fırlatır (bkz. app/recognition/ocr.py); burada sessizce yutulmaz.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_tesseract_path() -> None:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]

    exe_name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    bundled = base / "vendor" / "tesseract" / exe_name
    if not bundled.exists():
        return

    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = str(bundled)
    tessdata = bundled.parent / "tessdata"
    if tessdata.exists():
        os.environ["TESSDATA_PREFIX"] = str(tessdata)
