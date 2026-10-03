"""Tespit kayıtlarını CSV olarak dışa aktarma.

Excel ile doğrudan uyumlu olması için UTF-8 BOM (utf-8-sig) kullanılır.
Excel'e özgü ileri biçimlendirme gerekirse (örn. renkli hücreler,
birden fazla sayfa) openpyxl tabanlı ayrı bir `export_excel.py` modülü
eklenebilir; mevcut CSV ihracı Excel'de doğrudan açılabildiği için bu
ilk sürümde gerekli görülmemiştir.
"""

from __future__ import annotations

import csv
from pathlib import Path

from app.database.models import Detection
from app.utils.plate import format_plate_display

_HEADERS = [
    "Plaka", "Tarih ve Saat", "Kamera", "Tespit Güveni (%)", "OCR Güveni (%)",
    "Yetkili mi", "İnceleme Durumu", "Görüntü Yolu",
]


def export_detections_csv(
    detections: list[Detection], camera_names: dict[int, str], output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(_HEADERS)
        for d in detections:
            writer.writerow([
                format_plate_display(d.plate_normalized),
                d.detected_at,
                camera_names.get(d.camera_id, f"Kamera #{d.camera_id}"),
                f"{d.detection_confidence * 100:.1f}",
                f"{d.ocr_confidence * 100:.1f}",
                "Evet" if d.is_authorized else "Hayır",
                d.review_status,
                d.image_path or "",
            ])
    return output_path
