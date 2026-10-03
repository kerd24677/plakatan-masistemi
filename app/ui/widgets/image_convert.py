from __future__ import annotations

from PySide6.QtGui import QImage, QPixmap


def bgr_frame_to_qpixmap(frame) -> QPixmap:
    import cv2

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    qimage = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
    # .copy(): rgb (numpy) tamponu bu fonksiyon dönünce serbest kalabilir;
    # QImage kendi belleğine kopyalamadan referans tutarsa veri bozulabilir.
    return QPixmap.fromImage(qimage.copy())
